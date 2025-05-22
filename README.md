# Gemini YouTube Processor

**Gemini YouTube Processor** is a Python desktop application that leverages the power of Google's Gemini AI models to transcribe YouTube videos, generate summaries, and translate content into various languages. It features a user-friendly interface built with Kivy.

## Features

*   **YouTube Video Transcription:** Provide a YouTube video URL to get a full transcription of its audio content.
*   **Content Summarization:** Generate concise summaries from the transcription.
*   **Text Translation:** Translate the transcription into multiple supported languages.
*   **Model Selection:** Choose from various Gemini models (including `gemini-2.5-flash-preview-05-20` and `gemini-2.5-pro-preview-05-06`) for different tasks.
*   **API Key Input:** Easily input your Google Gemini API Key via the UI.
*   **Customizable (Future):** Planned features include managing multiple API keys, customizing model lists, and editing prompts directly within the application via `settings.json`.
*   **Cross-Platform:** Built with Kivy, aiming for compatibility where Kivy runs (Windows, macOS, Linux).

## Requirements

*   Python 3.9+
*   Kivy framework
*   Google Generative AI SDK

## Setup Instructions

Follow these steps to set up and run the application:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/your-repository-name.git # Replace with your actual repository URL
    cd your-repository-name
    ```

2.  **Create and Activate a Virtual Environment:**

    *   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

    *   **macOS / Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    Once the virtual environment is activated, install the required packages from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Kivy installation can sometimes be complex depending on your system. If you encounter issues, please refer to the official [Kivy installation guide](https://kivy.org/doc/stable/gettingstarted/installation.html).)*

## Configuration

1.  **Google Gemini API Key:**
    *   You will need a Google Gemini API Key to use the application. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   The first time you run the application, or if no API key is configured, you can enter your API key directly into the input field provided in the UI.
    *   For more advanced configuration, the API key and other settings are stored in `settings.json` in the application's root directory.

2.  **Settings File (`settings.json`):**
    This file is automatically created and stores your API keys (future support for multiple), model preferences, and prompts. Advanced users can modify this file directly, but ensure the JSON structure is maintained. Default prompts and model lists are provided.

## Running the Application

After completing the setup and configuration:

1.  Ensure your virtual environment is activated.
2.  Navigate to the application's root directory in your terminal.
3.  Run the main script:
    ```bash
    python main.py
    ```

## Usage

1.  **Enter API Key:** If prompted or if it's your first time, enter your Google Gemini API Key in the designated field. The application will attempt to configure the Gemini client.
2.  **Select Model:** Choose your preferred Gemini model from the dropdown menu for the tasks.
3.  **Enter YouTube URL:** Paste the full YouTube video URL into the input field. The application will validate the URL format.
4.  **Transcribe:** Click the "Transcribe" button. Progress will be shown, and the transcription will appear in the "📝 Transcription" tab.
5.  **Summarize:** Once a transcription is available, go to the "📚 Summary" tab and click "Summarize".
6.  **Translate:** Go to the "🌐 Translation" tab, select your target language, and click "Translate".
7.  **Save Outputs:** Each tab has a "Save" button to save the respective content (transcription, summary, translation) to a text file.

## File Structure

*   `main.py`: The main Kivy application file containing the UI layout and core application logic.
*   `gemini_services.py`: Handles all API interactions with the Google Gemini models.
*   `utils.py`: Provides utility functions like saving text to files.
*   `settings_manager.py`: Manages loading and saving application settings from/to `settings.json`.
*   `settings.json`: Stores user-specific settings, including API keys, model preferences, and custom prompts.
*   `requirements.txt`: Lists Python dependencies for the project.
*   `README.md`: This file.

## Troubleshooting (Example)

*   **Kivy Installation Issues:** If `pip install kivy` fails, consult the [official Kivy documentation](https://kivy.org/doc/stable/gettingstarted/installation.html) for platform-specific dependencies and troubleshooting steps.
*   **API Key Errors:** Ensure your API key is correctly entered and has the necessary permissions for the Gemini API. Check the error messages in the UI for more details.
*   **`[Errno videos_unavailable]` or similar from Gemini:** This might indicate the specific YouTube video cannot be accessed or processed by the Gemini API. Try a different video.

## License

This project is licensed under the Apache License 2.0. (A `LICENSE` file should be added to the repository if this is the case).
```
