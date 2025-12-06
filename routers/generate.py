import os
import shutil
import uuid
import requests
import mimetypes
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Optional
from services.generate_service import generate_soal_service, generate_summary_service

router = APIRouter()

# --- SETUP TEMP FOLDER ---
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# --- REQUEST MODELS ---
class GenerateSoalRequest(BaseModel):
    subject: str
    topic: str
    difficulty: str
    total_questions: int
    types: List[Literal["pg", "essay"]]
    language: str = "id"

# --- HELPER FUNCTIONS ---
def _get_direct_url(url: str) -> str:
    """
    Mengubah URL Google Drive View/Sharing menjadi Direct Download Link.
    Contoh: .../view?usp=sharing -> .../uc?export=download&id=...
    """
    # Regex untuk menangkap File ID dari berbagai format URL GDrive
    patterns = [
        r"drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)",
        r"docs\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            # Construct direct download URL
            return f"https://drive.google.com/uc?export=download&id={file_id}"
            
    return url # Return original if not a GDrive link

# --- ENDPOINTS ---

@router.post("/soal")
def generate_soal(req: GenerateSoalRequest):
    """
    Generate soal lengkap dengan kunci jawaban, rubrik, dan poin penilaian.
    """
    result = generate_soal_service(
        req.subject,
        req.topic,
        req.difficulty,
        req.total_questions,
        req.types,
        req.language
    )
    return {"data": result}

@router.post("/summary")
async def generate_summary(
    file: UploadFile = File(None),
    file_url: str = Form(None)
):
    """
    Generate Summary dari Dokumen.
    Bisa via Upload File (PDF/Text) ATAU via URL Link.
    """
    # 1. Validasi: Harus ada salah satu
    if not file and not file_url:
        raise HTTPException(status_code=400, detail="Harap upload file ATAU kirim file_url.")

    filename = f"{uuid.uuid4()}"
    file_path = ""
    mime_type = "application/pdf" # Default fallback

    try:
        # --- KASUS A: FILE UPLOAD ---
        if file:
            ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
            filename += f".{ext}"
            file_path = os.path.join(TEMP_DIR, filename)
            mime_type = file.content_type or "application/pdf"
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # --- KASUS B: FILE URL (Download Dulu) ---
        elif file_url:
            # Transform URL jika itu link Google Drive
            download_url = _get_direct_url(file_url)
            print(f"[INFO] Downloading URL: {download_url}")
            
            # Coba tebak ekstensi dari URL asli (bukan direct link yg aneh)
            if "." in file_url.split("/")[-1]:
                ext = file_url.split("/")[-1].split("?")[0].split(".")[-1]
                filename += f".{ext}"
            else:
                filename += ".pdf" # Default PDF jika tidak jelas
            
            file_path = os.path.join(TEMP_DIR, filename)
            
            # Download File
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(download_url, stream=True, headers=headers, timeout=30)
            
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Gagal download URL: {resp.status_code}")
            
            with open(file_path, "wb") as f:
                f.write(resp.content)
            
            # Tebak Mime Type dari file yang didownload (penting untuk Gemini)
            guessed_type, _ = mimetypes.guess_type(file_path)
            if guessed_type:
                mime_type = guessed_type
            else:
                # Fallback manual check header file
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    if header == b'%PDF':
                        mime_type = 'application/pdf'

        # 2. Panggil Service (Sama untuk kedua kasus)
        result = generate_summary_service(file_path, mime_type)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return {"data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Cleanup: Hapus file temp
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass