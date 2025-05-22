from google import genai # For new SDK structure
from google.genai import types # For new SDK structure
import re
import logging
import os # For testing with GOOGLE_API_KEY

# Configure basic logging
# Ensure this is configured in main.py or when the app starts,
# or it might conflict if multiple modules configure it.
# For a library file like this, it's often better to just get a logger:
logger = logging.getLogger(__name__) # Get a logger for this module

# Default Generation Config values (can be overridden by settings later)
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.95 # Note: top_p is not a direct param in new GenerateContentConfig, it's part of a candidate filter. For simplicity, we might omit it or research specific filter usage.
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
    if not api_key:
        # The new genai.Client() will automatically look for GOOGLE_API_KEY if api_key is None
        logger.warning("API key not explicitly provided to configure_gemini_client. Relying on GOOGLE_API_KEY env var if set.")
        # Pass None to allow the SDK to handle env var.
        # If an empty string is passed and GOOGLE_API_KEY is also not set, it will fail.
        api_key_to_use = None 
    else:
        api_key_to_use = api_key

    try:
        # If api_key_to_use is None, genai.Client() checks for GOOGLE_API_KEY
        client = genai.Client(api_key=api_key_to_use)
        logger.info("Google Generative AI client configured successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to create Google Generative AI client: {e}")
        return None

# get_gemini_model is removed as model is specified directly in client.models.generate_content()

def clean_youtube_url(youtube_url: str) -> tuple[str | None, str | None]:
    """
    Cleans the YouTube URL and extracts the video ID.

    Args:
        youtube_url: The input YouTube URL string.

    Returns:
        A tuple (cleaned_url, video_id). cleaned_url is in the format 
        https://www.youtube.com/watch?v=VIDEO_ID.
        Returns (None, None) if the URL is invalid.
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
    model_name: str,
    video_url: str, 
    video_id_from_url: str, 
    progress_callback: callable,
    status_callback: callable,
    system_prompt_text: str,
    user_prompt_text: str = "Please transcribe this video accurately, including timestamps if possible."
) -> dict:
    """
    Transcribes the video from the given URL using the Gemini model via the new Client SDK.
    Note: Gemini's direct video URI processing for YouTube URLs needs runtime verification.
    It might require a direct video file URI instead of a YouTube page URL.

    Args:
        client: Initialized `google.genai.Client` instance.
        model_name: Name of the model to use (e.g., "gemini-1.5-flash").
                    The "models/" prefix will be added if not present.
        video_url: The cleaned YouTube URL (or potentially a direct video file URI).
        video_id_from_url: The extracted YouTube video ID, used for metadata.
        progress_callback: Callable to update progress (e.g., `func(percentage: float)`).
        status_callback: Callable to update status messages (e.g., `func(message: str)`).
        system_prompt_text: The system instruction for the transcription model.
        user_prompt_text: The user-facing prompt for the transcription.

    Returns:
        A dictionary containing the transcription `text`, `video_title`, `video_id` on success,
        or an `error` message on failure.
    """
    status_callback("Starting transcription process...")
    progress_callback(0)

    if not client:
        status_callback("Error: Gemini Client not initialized.")
        return {"success": False, "error": "Gemini Client not initialized."}
    if not video_url:
        status_callback("Error: Video URL is missing.")
        return {"success": False, "error": "Video URL is missing."}
    
    # Ensure model name has "models/" prefix for new SDK
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    try:
        contents = [
            types.Part.from_uri(uri=video_url, mime_type="video/youtube"), # Still needs runtime verification for YouTube URLs
            types.Part.from_text(text=user_prompt_text)
        ]
        
        config = types.GenerateContentConfig(
            system_instruction=types.Part.from_text(system_prompt_text), # Correct way for new SDK
            response_mime_type="text/plain", # Ensure this is valid; often not needed or handled by default
            temperature=DEFAULT_TEMPERATURE,
            # top_p=DEFAULT_TOP_P, # top_p is part of CandidateFilter, not directly in GenerateContentConfig
            max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS_TRANSCRIPTION
        )

        status_callback(f"Sending request to Gemini API ({model_name}) for transcription...")
        response_stream = client.generate_content_stream( # generate_content_stream
            model=model_name,
            contents=contents,
            config=config # Pass the config object
        )

        full_transcription = []
        chunk_count = 0
        simulated_total_chunks = 50 

        for chunk_count, chunk in enumerate(response_stream):
            if chunk.text: # Check if text attribute exists and is not None
                full_transcription.append(chunk.text)
            
            progress = min(95, (chunk_count / simulated_total_chunks) * 100) 
            progress_callback(progress)
            status_callback(f"Transcription in progress... Chunk {chunk_count + 1} received.")
            logger.info(f"Received chunk {chunk_count + 1}: {chunk.text[:50] if chunk.text else 'No text in chunk'}")

        transcription_text = "".join(full_transcription)

        if not transcription_text.strip():
            status_callback("Warning: Transcription is empty.")
            
        lines = [line for line in transcription_text.splitlines() if line.strip()]
        video_title = lines[0][:50] if lines else "Untitled Transcription"
        
        progress_callback(100)
        status_callback("Transcription completed successfully.")
        logger.info(f"Transcription successful for video ID: {video_id_from_url}")
        return {
            "success": True,
            "transcription": transcription_text,
            "video_title": video_title,
            "video_id": video_id_from_url,
        }

    except Exception as e:
        error_message = f"Transcription error: {str(e)}"
        logger.error(error_message, exc_info=True)
        status_callback(error_message)
        progress_callback(0)
        return {"success": False, "error": str(e)}


def summarize_text(
    client: genai.Client,
    model_name: str,
    text_to_summarize_or_full_user_prompt: str, # This will be the full prompt including the text
    status_callback: callable,
    system_prompt_text: str,
    # user_prompt_text argument is effectively merged into text_to_summarize_or_full_user_prompt
    target_language_name: str = "original" 
) -> dict:
    """
    Summarizes the given text using the Gemini model via the `google.genai` Client SDK.

    Args:
        client: Initialized `google.genai.Client` instance.
        model_name: Name of the model to use (e.g., "gemini-1.5-flash").
                    The "models/" prefix will be added if not present.
        text_to_summarize_or_full_user_prompt: The full user prompt, which should already
                                                contain the text to be summarized
                                                (e.g., "Summarize this: <long_text_here>").
        status_callback: Callable to update status messages.
        system_prompt_text: System-level instructions for the summarization model.
        target_language_name: Intended language of the summary (primarily for metadata,
                              as the prompt itself should guide the model's language output if needed).

    Returns:
        A dictionary containing the `summary` on success, or an `error` message on failure.
    """
    status_callback("Starting summarization...")
    if not client:
        status_callback("Error: Gemini Client not initialized.")
        return {"success": False, "error": "Gemini Client not initialized."}
    if not text_to_summarize_or_full_user_prompt.strip():
        status_callback("Error: No text provided for summarization.")
        return {"success": False, "error": "No text to summarize."}
    
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    try:
        # The user_prompt_text from main.py is already formatted to include the text.
        contents = [types.Part.from_text(text=text_to_summarize_or_full_user_prompt)]

        config = types.GenerateContentConfig(
            system_instruction=types.Part.from_text(system_prompt_text),
            response_mime_type="text/plain", # As per previous structure
            temperature=DEFAULT_TEMPERATURE,
            max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS_SUMMARY
        )
        
        status_callback(f"Sending request to Gemini API ({model_name}) for summarization...")
        response = client.generate_content( # Non-streaming
            model=model_name,
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
    model_name: str,
    text_to_translate: str,
    target_language_name: str, 
    status_callback: callable,
    system_prompt_text: str,
    user_prompt_template: str = "Translate the following text to {language}:\n\n{text}" 
) -> dict:
    """
    Translates the given text to the target language using the Gemini model via the `google.genai` Client SDK.

    Args:
        client: Initialized `google.genai.Client` instance.
        model_name: Name of the model to use (e.g., "gemini-1.5-flash").
                    The "models/" prefix will be added if not present.
        text_to_translate: The text content to be translated.
        target_language_name: The name of the target language (e.g., "German", "French").
        status_callback: Callable to update status messages.
        system_prompt_text: System-level instructions for the translation model.
        user_prompt_template: A template for the user prompt, which must include
                              `{language}` and `{text}` placeholders.

    Returns:
        A dictionary containing the `translation` on success, or an `error` message on failure.
    """
    status_callback(f"Starting translation to {target_language_name}...")
    if not client:
        status_callback("Error: Gemini Client not initialized.")
        return {"success": False, "error": "Gemini Client not initialized."}
    if not text_to_translate.strip():
        status_callback("Error: No text provided for translation.")
        return {"success": False, "error": "No text to translate."}
    if not target_language_name:
        status_callback("Error: Target language not specified.")
        return {"success": False, "error": "Target language not specified."}
    
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    try:
        final_user_prompt = user_prompt_template.format(
            language=target_language_name,
            text=text_to_translate
        )
        contents = [types.Part.from_text(final_user_prompt)]

        config = types.GenerateContentConfig(
            system_instruction=types.Part.from_text(system_prompt_text),
            response_mime_type="text/plain", # As per previous structure
            temperature=0.1, 
            max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS_TRANSLATION
        )

        status_callback(f"Sending request to Gemini API ({model_name}) for translation to {target_language_name}...")
        response = client.generate_content( # Non-streaming
            model=model_name,
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
    # Configure logging for standalone testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Running basic tests for gemini_services.py (New Client SDK)...")

    # Test 1: Configure Gemini Client
    print("\n--- Test: Configure Gemini Client ---")
    api_key_to_test = os.environ.get("GOOGLE_API_KEY") 
    if not api_key_to_test:
        print("GOOGLE_API_KEY not set. Using a dummy key for structure test.")
        api_key_to_test = "YOUR_DUMMY_API_KEY_FOR_STRUCTURE_TEST" 
    
    client_instance = configure_gemini_client(api_key_to_test)
    print(f"Client instance created: {client_instance is not None}")
    if client_instance is None and api_key_to_test == "YOUR_DUMMY_API_KEY_FOR_STRUCTURE_TEST":
        print("Note: Client creation likely failed due to dummy API key or missing GOOGLE_API_KEY. This is expected for dummy key.")
    
    # Test 2: Clean YouTube URL (No changes needed for this function, it's independent of SDK)
    print("\n--- Test: Clean YouTube URL ---")
    urls_to_test = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("http://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ]
    for url, expected_id in urls_to_test:
        cleaned_url, video_id = clean_youtube_url(url)
        print(f"Original: '{url}' -> Cleaned: '{cleaned_url}', ID: '{video_id}' (Expected ID: {expected_id})")
        assert video_id == expected_id

    # Placeholder callbacks for further tests
    def dummy_progress_callback(p): print(f"Progress: {p}%")
    def dummy_status_callback(s): print(f"Status: {s}")

    print("\n--- Placeholder Tests for API-dependent functions (New Client SDK structure) ---")
    print("To run full tests for transcribe, summarize, and translate, ensure:")
    print("1. GOOGLE_API_KEY environment variable is set to a valid key OR provide one to configure_gemini_client.")
    print("2. The specified model (e.g., 'models/gemini-1.5-flash') is available to your key.")

    if client_instance and api_key_to_test != "YOUR_DUMMY_API_KEY_FOR_STRUCTURE_TEST":
        # Use a model name compatible with the new SDK (usually needs "models/" prefix)
        model_for_test = "models/gemini-1.5-flash-latest" # Or any valid model for your key

        print(f"\n--- Mock Test: Transcribe Video (Structure with Client SDK) ---")
        # Test with a conceptual video URL, acknowledge it might not work with current Gemini `from_uri`
        # if it doesn't natively support YouTube page URLs for video content.
        # This test is more about the function call structure.
        # result_transcribe = transcribe_video(
        #     client_instance, model_for_test,
        #     video_url="https://www.youtube.com/watch?v=TESTVIDEO", # Placeholder
        #     video_id_from_url="TESTVIDEO",
        #     progress_callback=dummy_progress_callback, status_callback=dummy_status_callback,
        #     system_prompt_text="Transcribe this video with Client SDK.",
        #     user_prompt_text="Please transcribe this video."
        # )
        # print(f"Client SDK Transcription test result: {result_transcribe}")
        print("Skipping actual API call for transcription in this basic test environment (Client SDK).")

        print("\n--- Mock Test: Summarize Text (Structure with Client SDK) ---")
        # In main.py, user_prompt_template.format(text_content=self.current_transcription) is passed as `user_prompt_text`
        # which becomes `text_to_summarize_or_full_user_prompt` here.
        # So, the `text_to_summarize` arg in the old signature is now part of `text_to_summarize_or_full_user_prompt`.
        # result_summarize = summarize_text(
        #     client_instance, model_for_test,
        #     text_to_summarize_or_full_user_prompt="Summarize this: This is a long text for Client SDK summarization.",
        #     status_callback=dummy_status_callback,
        #     system_prompt_text="You are an expert Client SDK summarizer."
        #     # target_language_name is default
        # )
        # print(f"Client SDK Summarization test result: {result_summarize}")
        print("Skipping actual API call for summarization in this basic test environment (Client SDK).")

        print("\n--- Mock Test: Translate Text (Structure with Client SDK) ---")
        # result_translate = translate_text(
        #     client_instance, model_for_test,
        #     text_to_translate="Hello, Client SDK world!",
        #     target_language_name="German",
        #     status_callback=dummy_status_callback,
        #     system_prompt_text="You are a Client SDK translation expert.",
        #     user_prompt_template="Translate to {language} with Client SDK: {text}" # This is the default
        # )
        # print(f"Client SDK Translation test result: {result_translate}")
        print("Skipping actual API call for translation in this basic test environment (Client SDK).")
    else:
        print("\nSkipping API-dependent function tests as client instance is not available or used dummy key.")

    print("\nBasic tests for gemini_services.py finished.")
