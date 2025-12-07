import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env local (tidak ngefek di Railway, aman)
load_dotenv()


API_KEY = os.getenv("GEMINI_API_KEY")

TEXT_MODEL_NAME = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash") 
VISION_MODEL_NAME = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")
if not API_KEY:
    print("CRITICAL ERROR] Konfigurasi API Key Gagal.")
else:
    genai.configure(api_key=API_KEY)

# --- 5. HELPER FUNCTIONS ---
def get_text_model():
    return genai.GenerativeModel(TEXT_MODEL_NAME)

def get_vision_model():
    return genai.GenerativeModel(VISION_MODEL_NAME)

def upload_file_to_gemini(file_path: str, mime_type: str = None):
    try:
        uploaded_file = genai.upload_file(path=file_path, mime_type=mime_type)
        print(f"✅ File uploaded to Gemini: {uploaded_file.uri}")
        return uploaded_file
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise e