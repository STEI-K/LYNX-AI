import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- [MAGIC CODE] AUTO-CREATE FIREBASE CREDENTIALS ON RAILWAY ---
# Kode ini akan berjalan setiap kali server Railway dinyalakan.
# Dia mengambil isi variabel 'FIREBASE_CREDENTIALS_JSON' dan mengubahnya jadi file fisik.
if os.getenv("FIREBASE_CREDENTIALS_JSON"):
    print("[INFO] Mendeteksi Kredensial Firebase di Environment Variable...")
    try:
        # Ambil isinya
        creds_content = os.getenv("FIREBASE_CREDENTIALS_JSON")
        
        # Tulis ke file 'serviceAccountKey.json'
        with open("serviceAccountKey.json", "w") as f:
            f.write(creds_content)
        
        # Beritahu library Google agar baca file yang baru saja dibuat
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "serviceAccountKey.json"
        print("[SUCCESS] File 'serviceAccountKey.json' berhasil dibuat otomatis!")
    except Exception as e:
        print(f"[CRITICAL ERROR] Gagal membuat file kredensial: {e}")

# ----------------------------------------------------------------

# Import routers (Pastikan import ini ada SETELAH magic code di atas)
from routers import generate, analysis, chat, batch

app = FastAPI(title="LYNX AI Backend (FULL GEMINI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTER ROUTES
app.include_router(generate.router, prefix="/generate", tags=["Generate Soal"])
app.include_router(chat.router, prefix="/chat", tags=["General Chat & Assistant"]) 
app.include_router(batch.router, prefix="/grade", tags=["Batch Processing"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "LYNX AI is running 🚀"}