import os
import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify

# --- Configuration & Initialization ---
app = Flask(__name__)

# Define model paths RELATIVE to the container's working directory (/app)
# These paths assume you copied the files into the /app folder in your Dockerfile.
MODEL_PATH = 'rfmodel_compressed_max.joblib'
FEATURE_PATH = 'feature.joblib'

# Helper function to load the model and features
def load_model_and_features():
    """Loads the pre-trained model and feature names from joblib files."""
    try:
        model = joblib.load(MODEL_PATH)
        feature_names = joblib.load(FEATURE_PATH)
        return model, feature_names
    except FileNotFoundError as e:
        # Log a warning if the files aren't found in the container
        print(f"Error: Model file not found. Please ensure {MODEL_PATH} and {FEATURE_PATH} are copied to /app.")
        print(f"Details: {e}")
        return None, None

# Load model globally when the app starts
MODEL, FEATURE_NAMES = load_model_and_features()

# Check if model loaded successfully
if MODEL is None or FEATURE_NAMES is None:
    print("WARNING: Model or features failed to load. The API will not function correctly.")

# Mapping for Select Box options (Used for internal preprocessing)
CUT_OPTIONS = ['Ideal', 'Premium', 'Very Good', 'Good', 'Fair']

COLOR_OPTIONS = {
    "D": "D - Colorless (Best)",
    "E": "E - Colorless (Near Perfect)",
    "F": "F - Colorless (Slight Tint)",
    "G": "G - Near Colorless",
    "H": "H - Near Colorless (Slight Yellow)",
    "I": "I - Near Colorless (More Tint)",
    "J": "J - Faint Color"
}

CLARITY_OPTIONS = {
    "IF": "IF - Internally Flawless",
    "VVS1": "VVS1 - Very Very Slightly Included (1)",
    "VVS2": "VVS2 - Very Very Slightly Included (2)",
    "VS1": "VS1 - Very Slightly Included (1)",
    "VS2": "VS2 - Very Slightly Included (2)",
    "SI1": "SI1 - Slightly Included (1)",
    'SI2': "SI2 - Slightly Included (2)",
    "I1": "I1 - Included (Lowest Clarity)"
}

# --- Routes and API Endpoints ---

@app.route('/', methods=['GET'])
def index():
    """Renders the main input form and handles initial page load."""
    if MODEL is None:
        error_message = "🚨 Model files not found! Prediction API is disabled."
    else:
        error_message = None

    # This route assumes you have an index.html file in a 'templates' folder
    return render_template('index.html',
                            cut_options=CUT_OPTIONS,
                            color_options=COLOR_OPTIONS,
                            clarity_options=CLARITY_OPTIONS,
                            error_message=error_message)

@app.route('/predict', methods=['POST'])
def predict():
    """
    API endpoint: Receives data, preprocesses it, and returns the prediction.
    It is now robust against incorrect Content-Type headers from the client.
    """
    if MODEL is None:
        return jsonify({'error': 'Model not loaded on the server.'}), 500

    try:
        # 1. Get data from the POST request (Robustly handling JSON or form data)
        # Try to get JSON first. 'silent=True' prevents the 415 error if Content-Type is missing/wrong.
        data = request.get_json(silent=True) 
        
        if data is None:
             # If JSON parsing failed or was skipped, try standard form data
             data = request.form

        if not data:
             # If no data found at all
             raise ValueError("No input data provided in the request body.")

        # Extract numerical features and convert to float
        # We use .get() for safe dictionary access, providing a default 0.0 value
        carat = float(data.get('carat', 0.0))
        depth = float(data.get('depth', 0.0))
        table = float(data.get('table', 0.0))
        x = float(data.get('x', 0.0))
        y = float(data.get('y', 0.0))
        z = float(data.get('z', 0.0))
        
        # Extract categorical features
        cut = data.get('cut', 'Ideal')
        color = data.get('color', 'D')
        clarity = data.get('clarity', 'IF')

        # 2. Preprocessing: Create the feature vector for the model
        # Initialize the input vector with zeros based on the feature names list
        input_dict = {name: 0 for name in FEATURE_NAMES}

        # Set the numerical values
        input_dict['carat'] = carat
        input_dict['depth'] = depth
        input_dict['table'] = table
        input_dict['x'] = x
        input_dict['y'] = y
        input_dict['z'] = z
        
        # Set the one-hot encoded categorical values
        input_dict[f'cut_{cut}'] = 1
        input_dict[f'color_{color}'] = 1
        input_dict[f'clarity_{clarity}'] = 1

        # Create a DataFrame in the correct order for the model
        input_df = pd.DataFrame([input_dict], columns=FEATURE_NAMES)
        
        # 3. Prediction
        prediction = MODEL.predict(input_df)[0]
        
        # 4. Return result as a JSON response
        return jsonify({
            'predicted_price': f"${prediction:,.2f}",
            'raw_price': prediction 
        })

    except Exception as e:
        # Handle potential errors during conversion, prediction, or data extraction
        print(f"Prediction Error: {e}")
        # Return a 400 Bad Request for client-side input errors
        return jsonify({'error': f'An error occurred during prediction: {str(e)}'}), 400

# --- Running the App ---
if __name__ == '__main__':
    # This runs the development server locally, not used in the Docker/Gunicorn environment
    app.run(debug=True)
