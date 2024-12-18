# AI-Website-Generator

**AI-Website-Generator** is a Flask-powered web application that transforms your spoken input into fully functional, responsive websites. By leveraging OpenAI's transcription and language processing capabilities alongside advanced image generation APIs, AI-Website-Generator simplifies the website creation process, enabling you to build professional websites effortlessly using just your voice.

## Table of Contents

1.  [🚀 Features](#-features)
2.  [🌟 Demo](#-demo)
3.  [📦 Installation](#-installation)
4.  [🛠️ Usage](#️-usage)
5.  [🔧 Configuration](#-configuration)
6.  [📚 Technologies Used](#-technologies-used)
7.  [🤝 Contributing](#-contributing)
8.  [📄 License](#-license)
9.  [📞 Contact](#-contact)

---

## 🚀 Features

-   **Audio Recording & Transcription**
    -   Record audio directly through the web interface.
    -   Transcribe spoken input into text using OpenAI's Whisper model.
-   **AI-Powered Website Generation**
    -   Generate complete multi-page website code based on transcribed input.
    -   Utilize Tailwind CSS for responsive and modern design.
    -   Incorporate dynamic content and interactive elements seamlessly.
-   **Advanced Image Generation**
    -   Integrate high-quality images using LICA or DALL-E APIs.
    -   Automatically replace placeholder images with generated visuals tailored to your website's theme.
-   **Code Management**
    -   Easily update and refine website code based on additional prompts.
    -   Ensure clean, maintainable, and well-commented code adhering to best practices.
-   **User-Friendly Interface**
    -   Intuitive web interface with support for multiple device views (desktop, tablet, mobile).
    -   Real-time code display and easy copying functionality.

---


## 📦 Installation

### Prerequisites

-   Python 3.7 or higher
-   [pip](https://pip.pypa.io/en/stable/) (Python's package installer)
-   [Git](https://git-scm.com/) (Version control system)

### Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/kshitij10000/AI-Website-Generator.git
    cd AI-Website-Generator
    ```
2.  **Create a Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *   This will install all of the dependencies (listed in `requirements.txt`) that the project needs.
4.  **Set Up Environment Variables**
    *   Create a `.env` file in the root directory. This file is used to store sensitive information, like your API keys, and should not be committed to version control:
        ```env
        OPENAI_API_KEY=your_openai_api_key
        LICA_API_KEY=your_lica_api_key
        ```
        *Replace `your_openai_api_key` and `your_lica_api_key` with your actual API keys.*

---

## 🛠️ Usage

1.  **Run the Application:**
    ```bash
    python app.py
    ```
    The application will be accessible at `http://localhost:5000`.
2.  **Access the Web Interface:** Open your browser and navigate to `http://localhost:5000`.
3.  **Record Your Voice Input:**
    -   Click on the "Start Recording" button to begin.
    -   Speak your website requirements clearly.
    -   Click "Stop Recording" to end the session.
4.  **Transcribe Audio:** The recorded audio will be automatically transcribed into text.
5.  **Generate Website Code:** The transcribed text will be processed to generate the website code.
6.  **View & Copy Code:** View the generated code in the output section and copy it as needed.
7.  **Customize & Update:** Use the "Update Code" feature to make further modifications based on additional prompts.

---

## 🔧 Configuration

### API Keys

-   Obtain your OpenAI API key from the [OpenAI API Key Page](https://beta.openai.com/account/api-keys).
-   Obtain your LICA API key from the [LICA API website](https://www.lica.ai/)

### Environment Variables

-   Ensure the `.env` file contains the necessary API keys for seamless integration.

---

## 📚 Technologies Used

### Backend:

-   [Flask](https://flask.palletsprojects.com/): Web framework.
-   [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/): Audio recording.
-   [OpenAI API](https://openai.com/api/): Transcription and language processing.
-   [LICA API](https://www.lica.ai/): Image generation.

### Frontend:

-   [Tailwind CSS](https://tailwindcss.com/): Styling framework.
-   [Font Awesome](https://fontawesome.com/): Icons.
-   [Prism.js](https://prismjs.com/): Syntax highlighting.

### Others:

-   [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/): HTML parsing.
-   [aiohttp](https://docs.aiohttp.org/en/stable/): Asynchronous HTTP requests.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps to contribute:

1.  Fork the Repository
2.  Create a Feature Branch
    ```bash
    git checkout -b feature/YourFeature
    ```
3.  Commit Your Changes
    ```bash
    git commit -m "Add Your Feature"
    ```
4.  Push to the Branch
    ```bash
    git push origin feature/YourFeature
    ```
5.  Open a Pull Request

*   Please see the contributing guidelines in `CONTRIBUTING.md` if present

---

## 📄 License

This project is licensed under the MIT License.

---
