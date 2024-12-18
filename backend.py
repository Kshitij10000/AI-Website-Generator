from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from dotenv import load_dotenv
import pyaudio
import wave
import threading
from datetime import datetime
from openai import OpenAI
import aiohttp
import asyncio
import re
from typing import Dict, List, Union
from bs4 import BeautifulSoup

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)

# OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])  # this is also the default, it can be omitted

# LICA API Key
lica_api_key = os.getenv("LICA_API_KEY")
lica_base_url = 'https://api.lica.world/api/v1'

# Audio configuration
audio = pyaudio.PyAudio()
stream = None
frames = []
isRecording = False  # Track recording status
AUDIO_HISTORY_FOLDER = "audio_history"
if not os.path.exists(AUDIO_HISTORY_FOLDER):
    os.makedirs(AUDIO_HISTORY_FOLDER)

def record():
    global isRecording, frames, stream
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []

    while isRecording:
        data = stream.read(1024)
        frames.append(data)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/record', methods=['POST'])
def start_recording():
    global isRecording
    isRecording = True
    threading.Thread(target=record).start()
    return jsonify({"message": "Recording started"})

@app.route('/stop_record', methods=['POST'])
def stop_recording():
    global isRecording, stream, frames
    isRecording = False

    if stream is not None:
        stream.stop_stream()
        stream.close()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{AUDIO_HISTORY_FOLDER}/recording_{timestamp}.wav"
    
    waveFile = wave.open(filename, 'wb')
    waveFile.setnchannels(1)
    waveFile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    waveFile.setframerate(44100)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    stream = None
    frames = []
    return jsonify({"message": "Recording stopped and saved", "file": filename})

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    list_of_files = os.listdir(AUDIO_HISTORY_FOLDER)
    if not list_of_files:
        return jsonify({"transcription": "No recordings found in the directory."})

    latest_file = max(list_of_files, key=lambda x: os.path.getctime(os.path.join(AUDIO_HISTORY_FOLDER, x)))
    latest_file_path = os.path.join(AUDIO_HISTORY_FOLDER, latest_file)

    with open(latest_file_path, "rb") as audio_file:
        try:
            # Assuming the response is just plain text
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            transcription_text = transcription
        except Exception as e:
            transcription_text = f"API Error: {str(e)}"
            print("Error:", e)

    return jsonify({"transcription": transcription_text})

def create_ml_request(model, payload):
    url = f"{lica_base_url}/ml-requests/"
    headers = {
        'x-api-key': lica_api_key,
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

def fetch_ml_request_status(request_id):
    url = f"{lica_base_url}/ml-requests/{request_id}/"
    headers = {
        'x-api-key': lica_api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
        raise Exception(f"Request failed: {response.text}")

async def generate_image_lica(prompt: str):
    try:
        model = 'TEXT_TO_IMAGE'
        payload = {'text': prompt}
        request_id = create_ml_request(model, payload)
        
        # Polling the request status
        while True:
            status_response = fetch_ml_request_status(request_id)
            status = status_response['status']
            if status == 'completed':
                return status_response['response']['images'][0]
            elif status == 'failed':
                raise Exception("The request failed.")
            await asyncio.sleep(5)  # Adjust sleep time based on how responsive the API is
    except Exception as e:
        print(f"Image generation failed: {str(e)}")
        return None

async def generate_image_dalle(prompt: str, api_key: str, base_url: str):
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        async with session.post(f"{base_url}/images/generations", headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return result['data'][0]['url']
            else:
                error_text = await response.text()
                raise Exception(f"Failed to generate image: {error_text}")

async def process_tasks(prompts: List[str], image_model: str, api_key: str = None, base_url: str = None):
    if image_model == "LICA":
        tasks = [generate_image_lica(prompt) for prompt in prompts]
    else:  # DALL-E
        tasks = [generate_image_dalle(prompt, api_key, base_url) for prompt in prompts]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    processed_results: List[Union[str, None]] = []
    for result in results:
        if isinstance(result, Exception):
            print(f"An exception occurred: {result}")
            processed_results.append(None)
        else:
            processed_results.append(result)

    return processed_results

def extract_dimensions(url: str):
    matches = re.findall(r"(\d+)x(\d+)", url)
    if matches:
        width, height = matches[0]
        width = int(width)
        height = int(height)
        return (width, height)
    else:
        return (100, 100)

def create_alt_url_mapping(code: str) -> Dict[str, str]:
    soup = BeautifulSoup(code, "html.parser")
    images = soup.find_all("img")

    mapping: Dict[str, str] = {}

    for image in images:
        if not image["src"].startswith("https://placehold.co"):
            mapping[image["alt"]] = image["src"]

    return mapping

async def generate_images(code: str, image_model: str, api_key: str = None, base_url: str = None, image_cache: Dict[str, str] = {}):
    soup = BeautifulSoup(code, "html.parser")
    images = soup.find_all("img")

    alts = []
    for img in images:
        if img["src"].startswith("https://placehold.co") and image_cache.get(img.get("alt")) is None:
            alts.append(img.get("alt", None))

    alts = [alt for alt in alts if alt is not None]

    prompts = list(set(alts))

    if len(prompts) == 0:
        return code

    results = await process_tasks(prompts, image_model, api_key, base_url)

    mapped_image_urls = dict(zip(prompts, results))

    mapped_image_urls = {**mapped_image_urls, **image_cache}

    for img in images:
        if not img["src"].startswith("https://placehold.co"):
            continue

        new_url = mapped_image_urls[img.get("alt")]

        if new_url:
            width, height = extract_dimensions(img["src"])
            img["width"] = width
            img["height"] = height
            img["src"] = new_url
        else:
            print("Image generation failed for alt text:" + img.get("alt"))

    return soup.prettify()

@app.route('/generate-code', methods=['POST'])
def generate_code():
    transcription = request.json.get('transcription')
    image_model = request.json.get('image_model', 'LICA')
    if not transcription:
        return jsonify({'error': 'Transcription is required'}), 400

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    prompt_template = '''
    
        ## Background:
        You are an accomplished web developer with three decades of experience in building websites using various technologies, including HTML, CSS, JavaScript, and specifically Tailwind CSS. 
        Your expertise extends to both frontend and backend development. 
        You have an excellent understanding of the visual aspects of websites, including themes, fonts, colors, images, and logos. 
        Your goal is to create a single-page web application that adheres to the user’s requirements, even if those requirements are provided in the form of audio or video input.
        Don't add style="background-image: url('https://placehold.co/1200x500'). Only add images using placeholder link with src for product section and not for hero section.
        
        
        ## Task Description:
        Input Format:
        The user may provide input in the form of different languages like Hindi, Marathi, English, Punjabi, Gujarati, tamil, or telgu. Due to their limited technical knowledge, their requirements might not be precise or detailed. Your task is to interpret the user's input and build a website based on your experience and understanding of user's business domain.

        ## Building the Website:
        Imagine that the user has a specific business or purpose for the website (e.g., an online store, portfolio, blog, or service platform). Create a website with a well-defined information architecture, considering the following aspects:
        - Design: Use your expertise to design an appealing and professional layout with a focus on responsiveness and user experience. Leverage Tailwind CSS for rapid prototyping and a consistent design system. Always make interactive buttons & tabs.
        - Functionality: Make the website interactive with smooth navigation, user-friendly features, and clear calls to action. 
        - Responsiveness: Ensure the website adapts seamlessly across different devices (desktop, tablet, mobile) using responsive design techniques.
        - User Satisfaction: Your goal is to build a website that surpasses user expectations, including elements and functionalities they might not have explicitly mentioned. Leverage your understanding of the user's business domain to add additional features in the website. Don't be user specific Always add some additional information as per website specifications & domain.
        - Dynamic Content: Implement features that allow users to dynamically update content on the website, such as blog posts, product listings, or event calendars (depending on the website type).

        ## Additional Contextual Considerations:
        -Understand the context and logical intent behind the user's input. Look beyond keywords and focus on the user's business goals.
        - Business Specifications: Consider the user's business specifications and tailor the website accordingly. This may involve integrating payment gateways for online stores, appointment booking systems for service platforms, or contact forms for lead generation.
        - Multilingual Support: While the default language for the website should be English, integrate the ability to switch languages based on user preference or website content requirements. Utilize language detection libraries and translation APIs for dynamic content.
        - Placeholder Images and Graphics: Use placeholder images from placehold.co with various dimensions (e.g., hero banners, product thumbnails, portfolio images) to represent different image needs on the website.
        - Image Optimization: Include detailed alt text for each image to improve accessibility and SEO. Consider using image optimization techniques (blurring, cropping, resizing) to enhance website performance and user experience.
        - Branding and Logos: Always generate a unique and relevant logo for the website based on the user's domain and specifications. Keep the logo small and visually appealing.
        - Information Architecture: Design a clear and intuitive information architecture with a well-defined navigation structure, including menus, submenus, headers, footers, and tabs. Ensure these elements are interactive and visually appealing.
        - Research and Inspiration: Use your experience and leverage resources like Google and Wikipedia to research websites related to the user's domain. Analyze existing website structures, design trends, and user interface best practices to inform your design decisions. Always add the contact details, social media platforms in the footer of the website.
        - Code Quality: Write clean, maintainable, and well-commented code that adheres to best practices. Avoid placeholder comments and strive to write full code for all functionalities.

        ## Language Detection and Application:
        - Detect the language of the text input (English, Hindi, Marathi, Gujarati, Punjabi, Telgu, Bengali, Tamil, Kannada).
        - Generate all textual content and labels on the website based on the detected or user-specified language.
        
        ## Libraries and Dependencies:
        - Tailwind CSS: <script src="https://cdn.tailwindcss.com"></script>
        - Use different Google Fonts 
        - Font Awesome for icons: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css"></link>

        ## Return Format:
        - Provide the complete multi-page website code within <html></html> tags. 
        - Strictly Omit any markdown or "html" at the start or end of the response.
        - Keep in mind that unless & until user will not say to give the website in the local language always give the website in the English language.
        - Strictly don't add unnecessary things, text in the generated website.
        '''
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": f"{prompt_template}\n\nUser input transcription: {transcription}"
            }
        ],
        "max_tokens": 3000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        try:
            response_json = response.json()
            content = response_json['choices'][0]['message']['content']

            website_description = transcription
            if image_model == "LICA":
                image_url = asyncio.run(generate_image_lica(website_description))
            else:
                image_url = asyncio.run(generate_image_dalle(website_description, api_key, "https://api.openai.com/v1"))

            if image_url:
                content = content.replace("PLACEHOLDER_IMAGE_URL", image_url)

            generated_content = asyncio.run(generate_images(content, image_model, api_key, "https://api.openai.com/v1", {}))

            return jsonify({'code': generated_content})
        except (KeyError, TypeError) as e:
            print(f"Error parsing response JSON: {e}")
            return jsonify({'error': 'Failed to parse API response'}), 500
    else:
        return jsonify({'error': 'Failed to generate code: ' + response.text}), 500

@app.route('/update-code', methods=['POST'])
def update_code():
    try:
        data = request.get_json()
        current_code = data.get('current_code')
        user_prompt = data.get('user_prompt')
        image_model = data.get('image_model', 'LICA')

        if not current_code or not user_prompt:
            return jsonify({'error': 'Current code and user prompt are required'}), 400

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        update_prompt_template = '''
    
        ## Background:
        You are an accomplished web developer with three decades of experience in building websites using various technologies, including HTML, CSS, JavaScript, and specifically Tailwind CSS. 
        Your expertise extends to both frontend and backend development. 
        You have an excellent understanding of the visual aspects of websites, including themes, fonts, colors, images, and logos. 
        Your goal is to create a single-page web application that adheres to the user’s requirements, even if those requirements are provided in the form of audio or video input.
        Don't add style="background-image: url('https://placehold.co/1200x500'). Only add images using placeholder link with src for product section and not for hero section.
        
        
        ## Task Description:
        Input Format:
        The user may provide input in the form of different languages like Hindi, Marathi, English, Punjabi, Gujarati, tamil, or telgu. Due to their limited technical knowledge, their requirements might not be precise or detailed. Your task is to interpret the user's input and build a website based on your experience and understanding of user's business domain.

        ## Building the Website:
        Imagine that the user has a specific business or purpose for the website (e.g., an online store, portfolio, blog, or service platform). Create a website with a well-defined information architecture, considering the following aspects:
        - Design: Use your expertise to design an appealing and professional layout with a focus on responsiveness and user experience. Leverage Tailwind CSS for rapid prototyping and a consistent design system. Always make interactive buttons & tabs.
        - Functionality: Make the website interactive with smooth navigation, user-friendly features, and clear calls to action. 
        - Responsiveness: Ensure the website adapts seamlessly across different devices (desktop, tablet, mobile) using responsive design techniques.
        - User Satisfaction: Your goal is to build a website that surpasses user expectations, including elements and functionalities they might not have explicitly mentioned. Leverage your understanding of the user's business domain to add additional features in the website. Don't be user specific Always add some additional information as per website specifications & domain.
        - Dynamic Content: Implement features that allow users to dynamically update content on the website, such as blog posts, product listings, or event calendars (depending on the website type).

        ## Additional Contextual Considerations:
        -Understand the context and logical intent behind the user's input. Look beyond keywords and focus on the user's business goals.
        - Business Specifications: Consider the user's business specifications and tailor the website accordingly. This may involve integrating payment gateways for online stores, appointment booking systems for service platforms, or contact forms for lead generation.
        - Multilingual Support: While the default language for the website should be English, integrate the ability to switch languages based on user preference or website content requirements. Utilize language detection libraries and translation APIs for dynamic content.
        - Placeholder Images and Graphics: Use placeholder images from placehold.co with various dimensions (e.g., hero banners, product thumbnails, portfolio images) to represent different image needs on the website.
        - Image Optimization: Include detailed alt text for each image to improve accessibility and SEO. Consider using image optimization techniques (blurring, cropping, resizing) to enhance website performance and user experience.
        - Branding and Logos: Always generate a unique and relevant logo for the website based on the user's domain and specifications. Keep the logo small and visually appealing.
        - Information Architecture: Design a clear and intuitive information architecture with a well-defined navigation structure, including menus, submenus, headers, footers, and tabs. Ensure these elements are interactive and visually appealing.
        - Research and Inspiration: Use your experience and leverage resources like Google and Wikipedia to research websites related to the user's domain. Analyze existing website structures, design trends, and user interface best practices to inform your design decisions. Always add the contact details, social media platforms in the footer of the website.
        - Code Quality: Write clean, maintainable, and well-commented code that adheres to best practices. Avoid placeholder comments and strive to write full code for all functionalities.

        ## Language Detection and Application:
        - Detect the language of the text input (English, Hindi, Marathi, Gujarati, Punjabi, Telgu, Bengali, Tamil, Kannada).
        - Generate all textual content and labels on the website based on the detected or user-specified language.
        
        ## Libraries and Dependencies:
        - Tailwind CSS: <script src="https://cdn.tailwindcss.com"></script>
        - Use different Google Fonts 
        - Font Awesome for icons: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css"></link>

        ## Return Format:
        - Provide the complete multi-page website code within <html></html> tags. 
        - Strictly Omit any markdown or "html" at the start or end of the response.
        - Keep in mind that unless & until user will not say to give the website in the local language always give the website in the English language.
        - Strictly don't add unnecessary things, text in the generated website.
'''

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": f"Here is the update prompt template:\n{update_prompt_template} and current code:\n{current_code}\n\nMake the following changes:\n{user_prompt}"
                }
            ],
            "max_tokens": 3000
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        if response.status_code == 200:
            try:
                response_json = response.json()
                content = response_json['choices'][0]['message']['content']

                generated_content = asyncio.run(generate_images(content, image_model, api_key, "https://api.openai.com/v1", {}))

                return jsonify({'code': generated_content})
            except (KeyError, TypeError) as e:
                print(f"Error parsing response JSON: {e}")
                return jsonify({'error': 'Failed to parse API response'}), 500
        else:
            print("Failed to update code:", response.text)
            return jsonify({'error': 'Failed to update code: ' + response.text}), 500
    except Exception as e:
        print("Exception occurred:", str(e))
        return jsonify({'error': 'An error occurred: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=True)















