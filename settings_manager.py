import json
from pathlib import Path
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

SETTINGS_FILE = Path("settings.json") # As specified, in the root

DEFAULT_SETTINGS = {
    "api_keys": [], # List of stored API keys (e.g., {"name": "MyKey1", "key": "AIza..."})
    "active_api_key_name": "", # Name of the active API key from the list
    "models": [ # Default list of models, can be expanded by user
        {"name": "gemini-1.5-flash", "displayName": "Gemini 1.5 Flash (Recommended)"},
        {"name": "gemini-1.5-pro", "displayName": "Gemini 1.5 Pro"},
        {"name": "gemini-2.5-flash-preview-05-20", "displayName": "Gemini 2.5 Flash Preview (05-20)"}, # User specified
        {"name": "gemini-2.5-pro-preview-05-06", "displayName": "Gemini 2.5 Pro Preview (05-06)"},   # User specified
        {"name": "gemini-pro", "displayName": "Gemini Pro (Legacy)"} # Common model
    ],
    "selected_model_transcription": "gemini-2.5-flash-preview-05-20", # Default selection
    "selected_model_summary": "gemini-2.5-flash-preview-05-20",
    "selected_model_translation": "gemini-2.5-flash-preview-05-20",
    "prompts": {
        "transcription_system": "You are a highly accurate audio transcriptionist. Please transcribe the given audio content meticulously. Include timestamps if possible and clearly demarcate speakers if discernible.",
        "transcription_user": "Transcribe the audio from this video.",
        "summary_system": "You are an expert in creating concise and informative summaries. Please summarize the provided text, focusing on the key points and main arguments. The summary should be easy to understand and neutral in tone.",
        "summary_user": "Please summarize the following text: {text_content}", # Placeholder for text
        "translation_system": "You are a professional translator. Translate the given text accurately and naturally into the specified target language. Maintain the original meaning and tone as much as possible.",
        "translation_user": "Translate the following text to {target_language}: {text_content}" # Placeholders
    },
    "save_options": {
        # Using Path.home().joinpath() for better cross-platform compatibility in creating the string
        "default_save_directory": str(Path.home().joinpath("youtube_gemini_outputs")), 
        "auto_save_transcription": False,
        "auto_save_summary": False,
        "auto_save_translation": False
    },
    "ui_settings": {
        "theme": "Light", # Example: Light, Dark
        "font_size": 12
    }
}

def load_settings() -> dict:
    """
    Loads settings from SETTINGS_FILE.
    Returns default settings if the file doesn't exist or is corrupted.
    """
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # Basic validation: check if top-level keys from default are present
                for key in DEFAULT_SETTINGS:
                    if key not in settings:
                        logger.warning(f"Key '{key}' not found in settings.json, adding from defaults.")
                        settings[key] = DEFAULT_SETTINGS[key]
                logger.info(f"Settings loaded successfully from {SETTINGS_FILE}")
                return settings
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {SETTINGS_FILE}: {e}. Returning default settings.")
            return DEFAULT_SETTINGS.copy() 
        except Exception as e: 
            logger.error(f"An unexpected error occurred while loading {SETTINGS_FILE}: {e}. Returning default settings.")
            return DEFAULT_SETTINGS.copy()
    else:
        logger.info(f"{SETTINGS_FILE} not found. Returning default settings and creating the file.")
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()

def save_settings(data: dict) -> bool:
    """
    Saves the given data dictionary to SETTINGS_FILE as JSON.

    Args:
        data: The dictionary of settings to save.

    Returns:
        True if saving was successful, False otherwise.
    """
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4) 
        logger.info(f"Settings saved successfully to {SETTINGS_FILE}")
        return True
    except IOError as e:
        logger.error(f"IOError saving settings to {SETTINGS_FILE}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving settings to {SETTINGS_FILE}: {e}")
        return False

if __name__ == '__main__':
    # Basic configuration for standalone testing of this module
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Testing settings_manager.py functions...")

    # Test load_settings
    print("\n--- Test: load_settings ---")
    # To simulate various scenarios, you might want to temporarily rename/delete/corrupt settings.json
    
    # Ensure settings.json doesn't exist for a clean first load test
    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()
        print(f"Temporarily deleted existing {SETTINGS_FILE} for a clean load test.")

    settings_data = load_settings()
    print(f"Loaded settings (first load, should be defaults and file created):")
    # print(json.dumps(settings_data, indent=2, sort_keys=True)[:500] + "...") # Print snippet
    assert settings_data["selected_model_transcription"] == "gemini-2.5-flash-preview-05-20" 
    assert SETTINGS_FILE.exists() 

    # Test save_settings
    print("\n--- Test: save_settings ---")
    settings_data["selected_model_transcription"] = "gemini-1.5-pro"
    settings_data["ui_settings"]["theme"] = "Dark"
    settings_data["api_keys"].append({"name": "TestKey", "key": "AIzaTest..."})
    
    save_success = save_settings(settings_data)
    print(f"Saving settings successful: {save_success}")
    assert save_success

    # Test loading modified settings
    print("\n--- Test: load_settings (after save) ---")
    reloaded_settings = load_settings()
    # print(f"Reloaded settings: {json.dumps(reloaded_settings, indent=2, sort_keys=True)[:500]}...")
    assert reloaded_settings["selected_model_transcription"] == "gemini-1.5-pro"
    assert reloaded_settings["ui_settings"]["theme"] == "Dark"
    assert len(reloaded_settings["api_keys"]) == 1
    assert reloaded_settings["api_keys"][0]["name"] == "TestKey"

    # Test loading corrupted settings
    print("\n--- Test: load_settings (corrupted file) ---")
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        f.write("This is not valid JSON")
    
    corrupted_load_settings = load_settings()
    # print(f"Loaded settings after corruption (should be defaults): {json.dumps(corrupted_load_settings, indent=2, sort_keys=True)[:500]}...")
    assert corrupted_load_settings["selected_model_transcription"] == "gemini-2.5-flash-preview-05-20" # Back to default
    
    # Clean up by saving defaults again
    save_settings(DEFAULT_SETTINGS.copy())
    print(f"\nRestored {SETTINGS_FILE} with default settings.")
    
    print("\nsettings_manager.py tests finished.")
