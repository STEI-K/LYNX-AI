import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env untuk local development (di laptop)
# Di Railway, baris ini tidak akan melakukan apa-apa karena file .env tidak ada,
# tapi itu tidak masalah karena Railway pakai System Environment Variables.
load_dotenv()

# --- 1. LOAD CONFIG ---
API_KEY = os.getenv("GEMINI_API_KEY")

# --- MODEL CONFIGURATION ---
TEXT_MODEL_NAME = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash") 
VISION_MODEL_NAME = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")

# --- 2. VALIDATION & DEBUGGING ---
if not API_KEY:
    # Pesan error yang lebih jelas untuk Log Railway
    print("\n" + "="*50)
    print("❌ [CRITICAL ERROR] GEMINI_API_KEY KOSONG!")
    print("   Server berjalan di environment cloud (Railway/Vercel/dll),")
    print("   tapi variable 'GEMINI_API_KEY' belum diset di Dashboard Project.")
    print("   -> Buka Railway > Tab 'Variables' > Add 'GEMINI_API_KEY'")
    print("="*50 + "\n")
else:
    # Konfigurasi jika key ditemukan
    genai.configure(api_key=API_KEY)
    print(f"✅ Gemini API Key terdeteksi. Menggunakan model: {TEXT_MODEL_NAME}")

# --- 3. HELPER FUNCTIONS ---

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