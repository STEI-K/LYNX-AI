import google.generativeai as genai
from .config import (
    GEMINI_API_KEY, 
    GEMINI_TEXT_MODEL, 
    GEMINI_REASONING_MODEL
)

# Konfigurasi Global (Cukup sekali)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_flash_model():
    """Mengembalikan model untuk task ringan (Text Gen/Soal)"""
    return genai.GenerativeModel(GEMINI_TEXT_MODEL)

def get_gemini_pro_model():
    """Mengembalikan model untuk task berat (Reasoning/Tutor)"""
    return genai.GenerativeModel(GEMINI_REASONING_MODEL)