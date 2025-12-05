from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.chat_services import deep_tutor_service

router = APIRouter()

class DeepTutorRequest(BaseModel):
    question: str
    subject: Optional[str] = None
    student_level: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []
    
    # OPSI 1: Link (Cloudinary/S3) - Hemat Bandwidth Server
    file_url: Optional[str] = None 
    
    # OPSI 2: Base64 String - Praktis untuk file kecil
    file_base64: Optional[str] = None 
    
    # Wajib diisi jika pakai Base64, Opsional jika pakai URL
    mime_type: Optional[str] = None 

@router.post("/deep-tutor")
async def deep_tutor(req: DeepTutorRequest) -> Dict[str, Any]:
    try:
        result = deep_tutor_service(
            question=req.question,
            history=req.history,
            subject=req.subject,
            student_level=req.student_level,
            file_url=req.file_url,
            file_base64=req.file_base64, # <-- Kirim parameter baru
            mime_type=req.mime_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))