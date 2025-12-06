import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- 1. LOAD CONFIG ---
API_KEY = os.getenv("GEMINI_API_KEY")

# --- MODEL CONFIGURATION (FREE TIER OPTIMIZED) ---
# Gunakan 'gemini-1.5-pro' untuk chat pintar (Free Tier tersedia)
# Gunakan 'gemini-1.5-flash' hanya untuk task cepat/vision massal
TEXT_MODEL_NAME = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash") 
VISION_MODEL_NAME = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")

# --- 2. VALIDATION ---
if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env")
else:
    genai.configure(api_key=API_KEY)

# --- 3. HELPER FUNCTIONS ---

def get_text_model():
    """
    Mengembalikan model PRO untuk percakapan panjang dan cerdas.
    """
    return genai.GenerativeModel(TEXT_MODEL_NAME)

def get_vision_model():
    """
    Mengembalikan model FLASH untuk Vision (lebih cepat & efisien kuota).
    """
    return genai.GenerativeModel(VISION_MODEL_NAME)

def upload_file_to_gemini(file_path: str, mime_type: str = None):
    try:
        uploaded_file = genai.upload_file(path=file_path, mime_type=mime_type)
        print(f"✅ File uploaded to Gemini: {uploaded_file.uri}")
        return uploaded_file
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise e
