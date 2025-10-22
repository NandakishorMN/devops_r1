import os
import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify

# *** MLOPS INSTRUMENTATION ***
# Import Prometheus client library
from prometheus_client import Counter, Histogram, generate_latest, Gauge
from prometheus_client import start_http_server, REGISTRY
import threading
import time

# --- Configuration & Initialization ---
app = Flask(__name__)

# Define model paths RELATIVE to the container's working directory (/app)
MODEL_PATH = 'rfmodel_compressed_max.joblib'
FEATURE_PATH = 'feature.joblib'

# 1. DEFINE PROMETHEUS METRICS
REQUEST_COUNT = Counter(
    'ml_prediction_requests_total', 
    'Total number of prediction requests served', 
    ['method', 'endpoint']
)
REQUEST_LATENCY = Histogram(
    'ml_prediction_latency_seconds', 
    'Prediction latency (seconds)',
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0) # Custom buckets for latency monitoring
)
MODEL_LOADED_STATUS = Gauge(
    'ml_model_load_status', 
    'Status of model loading (1=success, 0=failure)'
)

# Helper function to load the model and features
def load_model_and_features():
    """Loads the pre-trained model and feature names from joblib files."""
    try:
        model = joblib.load(MODEL_PATH)
        feature_names = joblib.load(FEATURE_PATH)
        MODEL_LOADED_STATUS.set(1) # Set gauge to 1 on success
        return model, feature_names
    except FileNotFoundError as e:
        print(f"Error: Model file not found. Please ensure {MODEL_PATH} and {FEATURE_PATH} are copied to /app.")
        print(f"Details: {e}")
        MODEL_LOADED_STATUS.set(0) # Set gauge to 0 on failure
        return None, None

# Load model globally when the app starts
MODEL, FEATURE_NAMES = load_model_and_features()

if MODEL is None or FEATURE_NAMES is None:
    print("WARNING: Model or features failed to load. The API will not function correctly.")

# Mapping options (No changes needed, kept for reference)
CUT_OPTIONS = ['Ideal', 'Premium', 'Very Good', 'Good', 'Fair']
COLOR_OPTIONS = {
    "D": "D - Colorless (Best)",
    # ... (Rest of COLOR_OPTIONS) ...
}
CLARITY_OPTIONS = {
    "IF": "IF - Internally Flawless",
    # ... (Rest of CLARITY_OPTIONS) ...
}


# --- Metrics Endpoint ---
@app.route("/metrics")
def metrics():
    """Exposes the Prometheus metrics endpoint (required by ServiceMonitor)."""
    # Note: Flask runs this endpoint via Gunicorn on port 8080
    return Response(generate_latest(REGISTRY), mimetype='text/plain')


# --- Routes and API Endpoints ---
@app.route('/', methods=['GET'])
def index():
    """Renders the main input form and handles initial page load."""
    REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
    
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
    """API endpoint: Receives data, preprocesses it, and returns the prediction."""
    
    REQUEST_COUNT.labels(method='POST', endpoint='/predict').inc()
    
    if MODEL is None:
        return jsonify({'error': 'Model not loaded on the server.'}), 500

    # Start a timer to measure latency
    start_time = time.time()
    
    try:
        # 1. Get data from the POST request (Robustly handling JSON or form data)
        # ... (Data extraction logic remains the same) ...
        data = request.get_json(silent=True) or request.form

        if not data:
             raise ValueError("No input data provided in the request body.")

        # Extract numerical features and convert to float
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

        input_df = pd.DataFrame([input_dict], columns=FEATURE_NAMES)
        
        # 3. Prediction
        prediction = MODEL.predict(input_df)[0]
        
        # 4. Return result as a JSON response
        return jsonify({
            'predicted_price': f"${prediction:,.2f}",
            'raw_price': prediction 
        })

    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({'error': f'An error occurred during prediction: {str(e)}'}), 400
        
    finally:
        # Observe the time taken for the request
        latency = time.time() - start_time
        REQUEST_LATENCY.observe(latency)


# --- Running the App ---
if __name__ == '__main__':
    # This block is for local development testing only
    # Note: In production (Kubernetes/Gunicorn), the entrypoint handles the run command.
    app.run(host='0.0.0.0', port=8080, debug=True)