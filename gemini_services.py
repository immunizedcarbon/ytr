from google import genai # For new SDK structure
from google.genai import types # For new SDK structure
import re
import logging
import os # For testing with GOOGLE_API_KEY

logger = logging.getLogger(__name__) # Get a logger for this module

# Default Generation Config values
DEFAULT_TEMPERATURE = 0.7
# DEFAULT_TOP_P is not directly in GenerateContentConfig, handled via CandidateFilter if needed.
DEFAULT_MAX_OUTPUT_TOKENS_TRANSCRIPTION = 8192 
DEFAULT_MAX_OUTPUT_TOKENS_SUMMARY = 2048
DEFAULT_MAX_OUTPUT_TOKENS_TRANSLATION = 4096


def configure_gemini_client(api_key: str) -> genai.Client | None:
    """
    Configures and returns a Google Generative AI Client instance using the `google.genai` SDK.

    Args:
        api_key: The API key for the Google Gemini service. If empty or None,
                 the client will attempt to use the `GOOGLE_API_KEY` environment variable.

    Returns:
        A `google.genai.Client` instance or `None` if configuration fails.
    """
    api_key_to_use = api_key if api_key else None
    if not api_key_to_use:
        logger.warning("API key not explicitly provided. Client will attempt to use GOOGLE_API_KEY env var.")
    
    try:
        client = genai.Client(api_key=api_key_to_use)
        logger.info("Google Generative AI client configured successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to create Google Generative AI client: {e}")
        return None

def clean_youtube_url(youtube_url: str) -> tuple[str | None, str | None]:
    """
    Cleans the YouTube URL and extracts the video ID.
    """
    if not youtube_url:
        return None, None
    match = re.search(r"(?:v=|\/|embed\/|watch\?v=|youtu\.be\/)([0-9A-Za-z_-]{11})", youtube_url)
    if match:
        video_id = match.group(1)
        cleaned_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Cleaned YouTube URL: {cleaned_url}, Video ID: {video_id}")
        return cleaned_url, video_id
    else:
        logger.warning(f"Invalid YouTube URL format: {youtube_url}")
        return None, None

def transcribe_video(
    client: genai.Client,
    model_name_str: str, # e.g., "gemini-1.5-flash"
    video_url: str, 
    video_id_from_url: str, 
    progress_callback: callable,
    status_callback: callable,
    system_prompt_text: str,
    user_prompt_text: str = "Please transcribe this video accurately, including timestamps if possible."
) -> dict:
    """
    Transcribes video using `client.models.generate_content_stream`.
    Note: `video_url` for `types.Part.from_uri` needs runtime verification for YouTube URLs.
    """
    status_callback("Starting transcription process...")
    progress_callback(0)

    if not client:
        status_callback("Error: Gemini Client not initialized.")
        return {"success": False, "error": "Gemini Client not initialized."}
    if not video_url:
        status_callback("Error: Video URL is missing.")
        return {"success": False, "error": "Video URL is missing."}
    
    model_name_prefixed = model_name_str if model_name_str.startswith("models/") else f"models/{model_name_str}"

    try:
        contents = [
            types.Part.from_uri(uri=video_url, mime_type="video/youtube"), 
            types.Part.from_text(text=user_prompt_text)
        ]
        
        config = types.GenerateContentConfig(
            system_instruction=types.Part.from_text(system_prompt_text),
            response_mime_type="text/plain", 
            temperature=DEFAULT_TEMPERATURE,
            max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS_TRANSCRIPTION
        )

        status_callback(f"Sending request to Gemini API ({model_name_prefixed}) for transcription...")
        response_stream = client.models.generate_content_stream( # Corrected: client.models.generate_content_stream
            model=model_name_prefixed, # Pass the string name
            contents=contents,
            config=config
        )

        full_transcription = []
        chunk_count = 0
        simulated_total_chunks = 50 

        for chunk_count, chunk in enumerate(response_stream):
            if chunk.text:
                full_transcription.append(chunk.text)
            progress = min(95, (chunk_count / simulated_total_chunks) * 100) 
            progress_callback(progress)
            status_callback(f"Transcription in progress... Chunk {chunk_count + 1} received.")
            logger.info(f"Received chunk {chunk_count + 1}: {chunk.text[:50] if chunk.text else 'No text in chunk'}")

        transcription_text = "".join(full_transcription)
        video_title = [line for line in transcription_text.splitlines() if line.strip()][0][:50] if transcription_text.strip() else "Untitled Transcription"
        
        progress_callback(100)
        status_callback("Transcription completed successfully.")
        logger.info(f"Transcription successful for video ID: {video_id_from_url}")
        return {"success": True, "transcription": transcription_text, "video_title": video_title, "video_id": video_id_from_url}

    except Exception as e:
        error_message = f"Transcription error: {str(e)}"
        logger.error(error_message, exc_info=True)
        status_callback(error_message)
        progress_callback(0)
        return {"success": False, "error": str(e)}

def summarize_text(
    client: genai.Client,
    model_name_str: str, # e.g., "gemini-1.5-flash"
    text_to_summarize_or_full_user_prompt: str,
    status_callback: callable,
    system_prompt_text: str,
    target_language_name: str = "original" # Metadata, not directly used in API call here
) -> dict:
    """
    Summarizes text using `client.models.generate_content`.
    `text_to_summarize_or_full_user_prompt` should be the full prompt including the text.
    """
    status_callback("Starting summarization...")
    if not client:
        status_callback("Error: Gemini Client not initialized.")
        return {"success": False, "error": "Gemini Client not initialized."}
    if not text_to_summarize_or_full_user_prompt.strip():
        status_callback("Error: No text provided for summarization.")
        return {"success": False, "error": "No text to summarize."}
    
    model_name_prefixed = model_name_str if model_name_str.startswith("models/") else f"models/{model_name_str}"

    try:
        contents = [types.Part.from_text(text=text_to_summarize_or_full_user_prompt)]
        config = types.GenerateContentConfig(
            system_instruction=types.Part.from_text(system_prompt_text),
            response_mime_type="text/plain",
            temperature=DEFAULT_TEMPERATURE,
            max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS_SUMMARY
        )
        
        status_callback(f"Sending request to Gemini API ({model_name_prefixed}) for summarization...")
        response = client.models.generate_content( # Corrected: client.models.generate_content
            model=model_name_prefixed,
            contents=contents,
            config=config
        )
        summary_text = response.text 
        status_callback("Summarization completed successfully.")
        logger.info("Summarization successful.")
        return {"success": True, "summary": summary_text}

    except Exception as e:
        error_message = f"Summarization error: {str(e)}"
        logger.error(error_message, exc_info=True)
        status_callback(error_message)
        return {"success": False, "error": str(e)}

def translate_text(
    client: genai.Client,
    model_name_str: str, # e.g., "gemini-1.5-flash"
    text_to_translate: str,
    target_language_name: str, 
    status_callback: callable,
    system_prompt_text: str,
    user_prompt_template: str = "Translate the following text to {language}:\n\n{text}" 
) -> dict:
    """
    Translates text using `client.models.generate_content`.
    """
    status_callback(f"Starting translation to {target_language_name}...")
    if not client:
        status_callback("Error: Gemini Client not initialized.")
        return {"success": False, "error": "Gemini Client not initialized."}
    # ... (other checks) ...
    if not text_to_translate.strip(): # Added check
        status_callback("Error: No text provided for translation.")
        return {"success": False, "error": "No text to translate."}
    if not target_language_name: # Added check
        status_callback("Error: Target language not specified.")
        return {"success": False, "error": "Target language not specified."}

    model_name_prefixed = model_name_str if model_name_str.startswith("models/") else f"models/{model_name_str}"

    try:
        final_user_prompt = user_prompt_template.format(language=target_language_name, text=text_to_translate)
        contents = [types.Part.from_text(final_user_prompt)]
        config = types.GenerateContentConfig(
            system_instruction=types.Part.from_text(system_prompt_text),
            response_mime_type="text/plain",
            temperature=0.1, 
            max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS_TRANSLATION
        )

        status_callback(f"Sending request to Gemini API ({model_name_prefixed}) for translation to {target_language_name}...")
        response = client.models.generate_content( # Corrected: client.models.generate_content
            model=model_name_prefixed,
            contents=contents,
            config=config
        )
        translated_text = response.text 
        status_callback(f"Translation to {target_language_name} completed successfully.")
        logger.info(f"Translation to {target_language_name} successful.")
        return {"success": True, "translation": translated_text}

    except Exception as e:
        error_message = f"Translation error: {str(e)}"
        logger.error(error_message, exc_info=True)
        status_callback(error_message)
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Running basic tests for gemini_services.py (New Client SDK with client.models)...")

    api_key_to_test = os.environ.get("GOOGLE_API_KEY")
    client_instance = configure_gemini_client(api_key_to_test if api_key_to_test else "YOUR_DUMMY_API_KEY")
    logger.info(f"Client instance created: {client_instance is not None}")

    # ... (clean_youtube_url tests can remain as they are independent) ...

    if client_instance and (api_key_to_test and api_key_to_test != "YOUR_DUMMY_API_KEY"):
        logger.info("Attempting mock API calls with a configured client...")
        # Add mock calls here if desired, similar to previous test structure but using client.models.generate_content
    else:
        logger.warning("Skipping mock API calls as client is not configured with a real API key.")
    logger.info("Basic tests for gemini_services.py finished.")
