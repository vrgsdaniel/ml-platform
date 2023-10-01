import os
import streamlit as st
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the URL for the prediction API
API_URL = os.environ.get("API_URL", "http://localhost:8000/v2/models/classifier/infer")

# Create a Streamlit web app
st.title("Wine Quality Prediction")

# Add a slider for input
fixed_acidity = st.slider("fixed acidity", 0.0, 15.0, 7.4, 0.1)
volatile_acidity = st.slider("volatile acidity", 0.0, 1.0, 0.7, 0.01)
citric_acid = st.slider("citric acid", 0.0, 1.0, 0.0, 0.01)
residual_sugar = st.slider("residual sugar", 0.0, 20.0, 1.9, 0.1)
chlorides = st.slider("chlorides", 0.0, 1.0, 0.076, 0.01)
free_sulfur_dioxide = st.slider("free sulfur dioxide", 1.0, 100.0, 11.0, 0.1)
total_sulfur_dioxide = st.slider("total sulfur dioxide", 1.0, 1000.0, 34.0, 0.1)
density = st.slider("density", 0.0, 1.0, 0.9978, 0.01)
pH = st.slider("pH", 0.0, 14.0, 3.51, 0.1)
sulphates = st.slider("sulphates", 0.0, 5.0, 0.56, 0.1)
alcohol = st.slider("alcohol", 0.0, 1.0, 9.4, 0.01)

# Add a button to make the prediction
if st.button("Predict"):
    # Make a POST request to the prediction API
    inference_request = {
        "parameters": {"content_type": "pd"},
        "inputs": [
            {
                "name": "fixed acidity",
                "shape": [1],
                "datatype": "FP32",
                "data": [fixed_acidity],
                "parameters": {"content_type": "np"},
            },
            {
                "name": "volatile acidity",
                "shape": [1],
                "datatype": "FP32",
                "data": [volatile_acidity],
                "parameters": {"content_type": "np"},
            },
            {
                "name": "citric acid",
                "shape": [1],
                "datatype": "FP32",
                "data": [citric_acid],
                "parameters": {"content_type": "np"},
            },
            {
                "name": "residual sugar",
                "shape": [1],
                "datatype": "FP32",
                "data": [residual_sugar],
                "parameters": {"content_type": "np"},
            },
            {
                "name": "chlorides",
                "shape": [1],
                "datatype": "FP32",
                "data": [chlorides],
                "parameters": {"content_type": "np"},
            },
            {
                "name": "free sulfur dioxide",
                "shape": [1],
                "datatype": "FP32",
                "data": [free_sulfur_dioxide],
                "parameters": {"content_type": "np"},
            },
            {
                "name": "total sulfur dioxide",
                "shape": [1],
                "datatype": "FP32",
                "data": [total_sulfur_dioxide],
                "parameters": {"content_type": "np"},
            },
            {
                "name": "density",
                "shape": [1],
                "datatype": "FP32",
                "data": [density],
                "parameters": {"content_type": "np"},
            },
            {"name": "pH", "shape": [1], "datatype": "FP32", "data": [pH], "parameters": {"content_type": "np"}},
            {
                "name": "sulphates",
                "shape": [1],
                "datatype": "FP32",
                "data": [sulphates],
                "parameters": {"content_type": "np"},
            },
            {
                "name": "alcohol",
                "shape": [1],
                "datatype": "FP32",
                "data": [alcohol],
                "parameters": {"content_type": "np"},
            },
        ],
    }
    logger.info("Sending inference request to %s", str(inference_request))
    response = requests.post(API_URL, json=inference_request)

    if response.status_code == 200:
        prediction = response.json()["outputs"][0]["data"][0]

        # Calculate the color based on the prediction value
        red = int(255 * (1 - prediction / 10))
        green = int(255 * (prediction / 10))

        # Display the prediction in a colored circle
        st.markdown(
            f'<div style="background-color: rgb({red}, {green}, 0); width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">{prediction:.1f}</div>',
            unsafe_allow_html=True,
        )
    else:
        logger.error("Error making the prediction: %s", response.text)
        st.error("Error making the prediction.")
