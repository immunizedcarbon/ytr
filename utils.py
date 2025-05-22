import re
from datetime import datetime
from pathlib import Path
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

def sanitize_filename_part(part: str, max_length: int = 50) -> str:
    """
    Sanitizes a string part for use in a filename.
    Removes special characters, replaces spaces with hyphens, and truncates.
    """
    if not part:
        return ""
    # Remove non-alphanumeric characters except hyphens and underscores
    sanitized = re.sub(r'[^\w\-_]', '', part)
    # Replace multiple hyphens/underscores with a single one
    sanitized = re.sub(r'[-_]+', '-', sanitized)
    # Truncate to max_length
    return sanitized[:max_length].strip('-')

def save_text_to_file(
    content: str,
    suggested_filename_prefix: str,
    video_title: str | None,
    video_id: str | None,
    parent_widget=None  # For Kivy FileChooser, not used in this basic implementation
) -> str | None:
    """
    Prepares content with a header and generates a suggested filename.
    Conceptually, this would show a file dialog in Kivy.
    For now, it simulates saving by printing info and can optionally save to a predefined directory if possible.

    Args:
        content: The main text content to save.
        suggested_filename_prefix: E.g., "Transcription", "Summary".
        video_title: The title of the video.
        video_id: The ID of the video.
        parent_widget: Placeholder for Kivy dialog parent.

    Returns:
        The suggested filename (or path if actually saved) if successful, None otherwise.
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    cleaned_title = sanitize_filename_part(video_title if video_title else "")
    cleaned_video_id = sanitize_filename_part(video_id if video_id else "")

    if cleaned_title and cleaned_video_id:
        suggested_filename = f"{suggested_filename_prefix}_{cleaned_title}_{cleaned_video_id}_{timestamp_str}.txt"
    elif cleaned_title:
        suggested_filename = f"{suggested_filename_prefix}_{cleaned_title}_{timestamp_str}.txt"
    elif cleaned_video_id:
        suggested_filename = f"{suggested_filename_prefix}_{cleaned_video_id}_{timestamp_str}.txt"
    else:
        suggested_filename = f"{suggested_filename_prefix}_{timestamp_str}.txt"

    header = f"Title: {video_title if video_title else 'N/A'}\n" \
             f"Video-ID: {video_id if video_id else 'N/A'}\n" \
             f"Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
             f"Prefix: {suggested_filename_prefix}\n" \
             f"--------------------------------------------------\n\n"
    
    full_content_to_save = header + content
    
    try:
        # Using a more specific name consistent with settings_manager.py if it were to save there
        output_dir = Path.home() / "youtube_gemini_outputs" 
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / suggested_filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content_to_save)
        
        logger.info(f"File content prepared and saved to: {file_path}")
        # These print statements are for simulation in a headless environment
        print(f"SIMULATED SAVE: Would ask user to save '{suggested_filename}'.")
        print(f"Actually saved for testing at: {file_path}")
        return str(file_path)

    except IOError as e:
        logger.error(f"Error during file saving simulation: {e}")
        print(f"ERROR: Could not simulate save for '{suggested_filename}' due to: {e}")
        return suggested_filename 
    except Exception as e:
        logger.error(f"An unexpected error occurred during file saving: {e}")
        print(f"UNEXPECTED ERROR during save for '{suggested_filename}': {e}")
        return None


def markdown_to_kivy_markup(text: str) -> str:
    """
    Placeholder function to convert Markdown text to Kivy's rich text markup.
    """
    logger.info("markdown_to_kivy_markup: Placeholder used, returning text as is.")
    return text


if __name__ == '__main__':
    # Basic configuration for standalone testing of this module
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Testing utils.py functions...")

    # Test sanitize_filename_part
    print("\n--- Test: sanitize_filename_part ---")
    test_strings = ["Normal Title", "Title with !@#$%", " Spaces  & Chars ", "LooooooooongTitleWithMoreThan50CharactersIndeed"]
    for s in test_strings:
        print(f"Original: '{s}' -> Sanitized: '{sanitize_filename_part(s)}'")

    # Test save_text_to_file
    print("\n--- Test: save_text_to_file ---")
    sample_content = "This is the main content of the file.\nIt can span multiple lines."
    title1 = "My Awesome Video Title !@#"
    video_id1 = "dQw4w9WgXcQ"
    prefix1 = "Transcription"
    
    saved_path1 = save_text_to_file(sample_content, prefix1, title1, video_id1)
    print(f"Call 1: save_text_to_file returned: {saved_path1}")

    print("\n--- Test: save_text_to_file (minimal info) ---")
    title2 = None
    video_id2 = None
    prefix2 = "Summary"
    saved_path2 = save_text_to_file(sample_content, prefix2, title2, video_id2)
    print(f"Call 2: save_text_to_file returned: {saved_path2}")
    
    if saved_path1:
        try:
            with open(saved_path1, "r", encoding="utf-8") as f_read:
                print(f"Content of {saved_path1} (first 300 chars):\n{f_read.read(300)}...")
        except FileNotFoundError:
            print(f"File {saved_path1} not found, could not read back content.")


    # Test markdown_to_kivy_markup
    print("\n--- Test: markdown_to_kivy_markup ---")
    markdown_sample = "This is **bold** and *italic* text. \n- Item 1\n- Item 2"
    kivy_markup = markdown_to_kivy_markup(markdown_sample)
    print(f"Original Markdown:\n{markdown_sample}")
    print(f"Converted Kivy Markup (placeholder behavior):\n{kivy_markup}")

    print("\nutils.py tests finished.")
