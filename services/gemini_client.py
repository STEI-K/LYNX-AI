import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env local (tidak ngefek di Railway, aman)
load_dotenv()

# --- 1. DEBUGGING ENVIRONMENT ---
# Ini akan mencetak daftar variable yang dideteksi Python ke Log Railway
print("\n" + "="*40)
print("🔍 DEBUG: MEMERIKSA ENVIRONMENT VARIABLES")
print("="*40)
found_keys = [k for k in os.environ.keys()]
if "GEMINI_API_KEY" in found_keys:
    print("✅ GEMINI_API_KEY DITEMUKAN dalam daftar environment!")
    # Cek apakah kosong atau tidak (tanpa menampilkan isinya)
    val = os.environ.get("GEMINI_API_KEY")
    if not val or len(val.strip()) == 0:
        print("❌ TAPI NILAINYA KOSONG/STRING KOSONG.")
    else:
        print(f"✅ Nilai terisi (Panjang: {len(val)} karakter).")
else:
    print("❌ GEMINI_API_KEY TIDAK ADA dalam daftar environment.")
    print("   Variable yang ada:", found_keys)
print("="*40 + "\n")

# --- 2. LOAD CONFIG ---
API_KEY = os.getenv("GEMINI_API_KEY")

# --- 3. MODEL CONFIGURATION ---
TEXT_MODEL_NAME = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash") 
VISION_MODEL_NAME = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")

# --- 4. VALIDATION ---
if not API_KEY:
    print("❌ [CRITICAL ERROR] Konfigurasi API Key Gagal.")
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