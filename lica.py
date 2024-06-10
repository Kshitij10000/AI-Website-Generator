import requests
import time
import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st 

# Constants
API_KEY = os.getenv("LICA_API_KEY")
BASE_URL = 'https://api.lica.world/api/v1'

def create_ml_request(model, payload):
    url = f"{BASE_URL}/ml-requests/"
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        'model': model,
        'payload': payload
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['data']['request_id']
    else:
        raise Exception(f"Request failed: {response.text}")
#vKYUnZWsvrRMc7bkRYQr
def fetch_ml_request_status(request_id):
    url = f"{BASE_URL}/ml-requests/{request_id}/"
    headers = {
        'x-api-key': API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
        raise Exception(f"Request failed: {response.text}")

def text_to_image(text):
    try:
        model = 'TEXT_TO_IMAGE'
        payload = {'text': text}
        request_id = create_ml_request(model, payload)
        
        # Polling the request status
        while True:
            status_response = fetch_ml_request_status(request_id)
            status = status_response['status']
            if status == 'completed':
                return True, status_response['response']['images'][0    ]
            elif status == 'failed':
                return False, "The request failed."
            time.sleep(5)  # Adjust sleep time based on how responsive the API is
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    text_prompt = st.text_input("Input your prompt")
    if text_prompt:
        success, result = text_to_image(text_prompt)
        if success:
            st.write(f"Image for the prompt '{text_prompt}':")
            st.image(result)
        else:
            st.info(f"An error occurred: {result}")
    else:
        st.info("Please enter a prompt to generate an image.")