from flask import Flask, request, jsonify, send_from_directory
import base64
import requests
import os
from dotenv import load_dotenv
from systemprompt.html_tailwind import html_tailwind_prompt
from systemprompt.react_tailwind import react_tailwind_prompt

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)

# OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")

def encode_image(image_file):
    """Function to encode the uploaded image file to base64."""
    return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/encode-image', methods=['POST'])
def encode_image_route():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    base64_image = encode_image(image_file)

    # Get the prompt type from the request form
    prompt_type = request.form.get('prompt_type')
    if prompt_type == 'react_tailwind':
        prompt = react_tailwind_prompt
    elif prompt_type == 'html_tailwind':
        prompt = html_tailwind_prompt
    else:
        return jsonify({'error': 'Invalid prompt type'}), 400

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 3000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        response_json = response.json()
        content = response_json['choices'][0]['message']['content']
        return jsonify({'code': content})
    else:
        return jsonify({'error': 'Failed to generate code: ' + response.text}), 500

if __name__ == '__main__':
    app.run(debug=True)
