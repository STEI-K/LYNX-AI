from typing import List, Optional
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.chat_services import deep_tutor_service

router = APIRouter()

@router.post("/deep-tutor")
async def deep_tutor(
    question: str = Form(...),
    subject: Optional[str] = Form(None),
    student_level: Optional[str] = Form(None),
    history: Optional[str] = Form(None),  # JSON String
    file: Optional[UploadFile] = File(None) # File Upload support
):
    """
    Deep Tutor Endpoint (Multimodal Upgrade).
    - Bisa terima Teks + File (Gambar/PDF/Video).
    - Bisa generate Gambar/Video jika diminta.
    """
    
    # 1. Parsing History (karena dikirim sebagai JSON string di Form Data)
    history_list = []
    if history:
        try:
            history_list = json.loads(history)
        except json.JSONDecodeError:
            history_list = []

    # 2. Handle File Upload (Simpan sementara)
    file_path = None
    mime_type = None
    
    if file:
        import os
        import shutil
        
        # Buat folder temp jika belum ada
        os.makedirs("temp", exist_ok=True)
        file_path = f"temp/{file.filename}"
        
        # Simpan file fisik
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        mime_type = file.content_type

    # 3. Panggil Service
    try:
        result = deep_tutor_service(
            question=question,
            history=history_list,
            subject=subject,
            student_level=student_level,
            file_path=file_path,
            mime_type=mime_type
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Cleanup: Hapus file temp agar server tidak penuh
        if file_path and os.path.exists(file_path):
            os.remove(file_path)