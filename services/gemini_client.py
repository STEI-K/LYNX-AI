import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
API_KEY = os.getenv("GEMINI_API_KEY")
TEXT_MODEL_NAME = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL_NAME = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
VIDEO_MODEL_NAME = os.getenv("GEMINI_VIDEO_MODEL", "veo-3.1-generate-preview")

if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env")
else:
    genai.configure(api_key=API_KEY)

# --- HELPER FUNCTIONS ---

def get_text_model():
    """Model untuk Chat, Tutor, dan Analisis Gambar (Vision)"""
    return genai.GenerativeModel(TEXT_MODEL_NAME)

def get_image_generation_model():
    """Model khusus membuat gambar (Nano Banana)"""
    return genai.GenerativeModel(IMAGE_MODEL_NAME)

def get_video_generation_model():
    """Model khusus membuat video (Veo)"""
    return genai.GenerativeModel(VIDEO_MODEL_NAME)

def upload_file_to_gemini(file_path: str, mime_type: str = None):
    """
    Upload file ke server Gemini agar bisa dibaca oleh AI.
    Returns: File object dari Gemini
    """
    try:
        # Upload file
        uploaded_file = genai.upload_file(path=file_path, mime_type=mime_type)
        print(f"✅ File uploaded to Gemini: {uploaded_file.uri}")
        return uploaded_file
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise e