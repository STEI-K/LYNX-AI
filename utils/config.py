import os
from dotenv import load_dotenv

load_dotenv()

# --- API KEYS ---
# Gunakan logic fallback: Coba cari key spesifik dulu, kalau tidak ada pakai key global
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- MODEL NAMES (Sesuai .env kamu) ---
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash")
GEMINI_REASONING_MODEL = os.getenv("GEMINI_REASONING_MODEL", "gemini-1.5-pro")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")

def ensure_keys():
    if not GEMINI_API_KEY:
        print("[CRITICAL] GEMINI_API_KEY tidak ditemukan di .env!")
        # Di production, ini sebaiknya raise Error
        
ensure_keys()