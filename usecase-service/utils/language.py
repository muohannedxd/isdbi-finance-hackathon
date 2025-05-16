"""
Language detection utilities for the Islamic Finance API.
"""

import logging
from langdetect import detect

logger = logging.getLogger("islamic_finance_api")

def detect_language(text):
    """
    Detect the language of the transaction text.
    
    Args:
        text (str): The text to detect language from
        
    Returns:
        str: The detected language code (e.g., 'en' for English)
    """
    try:
        detected_lang = detect(text)
        return detected_lang
    except Exception:
        logger.warning("Language detection failed, defaulting to English")
        return 'en'
