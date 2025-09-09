import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Gemstone Price Predictor",
    page_icon="💎",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
.stButton>button {
    color: #ffffff;
    background-color: #FF4B4B;
    border-radius: 8px;
    padding: 10px 20px;
    border: none;
    font-size: 16px;
    font-weight: bold;
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    transition: 0.3s;
}
.stButton>button:hover {
    background-color: #e64545;
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
}
[data-testid="stMetricValue"] {
    font-size: 2.5rem;
    color: #28a745;
}
h1 {
    text-align: center;
}
.st-emotion-cache-z5fcl4 {
    padding-bottom: 0.25rem;
}
</style>
""", unsafe_allow_html=True)

# --- Load Model and Feature Names ---
@st.cache_resource
def load_model():
    try:
        model = joblib.load('rfmodel.joblib')
        feature_names = joblib.load('feature.joblib')
        return model, feature_names
    except FileNotFoundError:
        return None, None

model, feature_names = load_model()

# --- App Header ---
if model is None:
    st.error("🚨 **Model files not found!**")
    st.info("Please make sure 'rfmodel.joblib' and 'feature.joblib' are in the same directory.")
    st.stop()

st.title("💎 Gemstone Price Predictor")
st.markdown("""
Welcome! This app predicts the price of a cubic zirconia stone (synthetic/lab-made gemstone).
Use the interactive controls in the sidebar to describe your stone.
""")
st.markdown("---")

# --- Sidebar for User Inputs ---
st.sidebar.header("Stone Characteristics")

def create_synced_input(label, key_prefix, min_val, max_val, default_val, step, help_text=""):
    main_key = key_prefix
    slider_key = f"{key_prefix}_slider"
    num_input_key = f"{key_prefix}_num_input"

    if main_key not in st.session_state:
        st.session_state[main_key] = default_val

    def sync_slider():
        st.session_state[main_key] = st.session_state[slider_key]
    def sync_num_input():
        st.session_state[main_key] = st.session_state[num_input_key]

    st.sidebar.markdown(f"**{label}**")
    if help_text:
        st.sidebar.caption(help_text)

    col1, col2 = st.sidebar.columns([3, 2])
    with col1:
        st.slider(
            label, min_value=min_val, max_value=max_val,
            value=st.session_state[main_key],
            step=step, key=slider_key, on_change=sync_slider,
            label_visibility='collapsed'
        )
    with col2:
        st.number_input(
            label, min_value=min_val, max_value=max_val,
            value=st.session_state[main_key],
            step=step, key=num_input_key, on_change=sync_num_input,
            label_visibility='collapsed'
        )

    return st.session_state[main_key]

def get_user_input():
    cut_options = ['Ideal', 'Premium', 'Very Good', 'Good', 'Fair']

    color_options = {
        "D": "D - Colorless (Best)",
        "E": "E - Colorless (Near Perfect)",
        "F": "F - Colorless (Slight Tint)",
        "G": "G - Near Colorless",
        "H": "H - Near Colorless (Slight Yellow)",
        "I": "I - Near Colorless (More Tint)",
        "J": "J - Faint Color"
    }

    clarity_options = {
        "IF": "IF - Internally Flawless",
        "VVS1": "VVS1 - Very Very Slightly Included (1)",
        "VVS2": "VVS2 - Very Very Slightly Included (2)",
        "VS1": "VS1 - Very Slightly Included (1)",
        "VS2": "VS2 - Very Slightly Included (2)",
        "SI1": "SI1 - Slightly Included (1)",
        "SI2": "SI2 - Slightly Included (2)",
        "I1": "I1 - Included (Lowest Clarity)"
    }

    carat = create_synced_input("Carat", "carat", 0.2, 5.0, 1.0, 0.01, "Weight of the stone.")
    
    cut = st.sidebar.selectbox("Cut Quality", cut_options, help="Quality of the stone's cut.")

    color_label = st.sidebar.selectbox("Color Grade", list(color_options.values()), help="Color grade from D to J.")
    color = [k for k, v in color_options.items() if v == color_label][0]

    clarity_label = st.sidebar.selectbox("Clarity Grade", list(clarity_options.values()), help="Clarity from IF to I1.")
    clarity = [k for k, v in clarity_options.items() if v == clarity_label][0]

    st.sidebar.markdown("---")
    st.sidebar.subheader("Dimensions (mm)")

    depth = create_synced_input("Depth (%)", "depth", 40.0, 80.0, 60.0, 0.1, "Total depth percentage.")
    table = create_synced_input("Table (%)", "table", 40.0, 80.0, 55.0, 0.1, "Width of top facet.")
    x = create_synced_input("Length (x)", "x", 0.0, 12.0, 5.0, 0.1)
    y = create_synced_input("Width (y)", "y", 0.0, 12.0, 5.0, 0.1)
    z = create_synced_input("Depth (z)", "z", 0.0, 8.0, 3.0, 0.1)

    input_data = {
        'carat': carat, 'cut': cut, 'color': color, 'clarity': clarity,
        'depth': depth, 'table': table, 'x': x, 'y': y, 'z': z
    }
    return input_data

user_input = get_user_input()

# --- Main Panel: Prediction and Results ---
if st.sidebar.button(" Predict Price"):
    input_dict = {name: 0 for name in feature_names}
    input_dict['carat'] = user_input['carat']
    input_dict['depth'] = user_input['depth']
    input_dict['table'] = user_input['table']
    input_dict['x'] = user_input['x']
    input_dict['y'] = user_input['y']
    input_dict['z'] = user_input['z']
    input_dict[f'cut_{user_input["cut"]}'] = 1
    input_dict[f'color_{user_input["color"]}'] = 1
    input_dict[f'clarity_{user_input["clarity"]}'] = 1
    input_df = pd.DataFrame([input_dict], columns=feature_names)

    with st.spinner('Calculating the price...'):
        time.sleep(1)
        prediction = model.predict(input_df)[0]

    st.markdown("---")
    st.subheader("Prediction Result")
    st.metric(label="Predicted Price", value=f"${prediction:,.2f}")
    st.success("Prediction complete! Use the sidebar to try different values.")
else:
    st.info("Adjust the controls in the sidebar and click 'Predict Price' to see the result.")

    st.markdown(
        """
        <div style="text-align: center;">
            <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcnc4NThqdXl5aW5rajE4Y2htMWR3OTFvZHF6bWZ0NHJqNTRrenAxZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l1KVccToDJ6oz6qYg/giphy.gif" width="300">
        </div>
        """,
        unsafe_allow_html=True
    )
