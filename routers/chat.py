from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.chat_services import chat_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    subject: Optional[str] = None # Opsional, misal user lagi di halaman matkul tertentu
    
    # Support File Upload
    file_url: Optional[str] = None 
    file_base64: Optional[str] = None 
    mime_type: Optional[str] = None 

@router.post("/message")
async def chat_endpoint(req: ChatRequest) -> Dict[str, Any]:
    """
    Endpoint Chat All-in-One:
    - Text Chat (Smart / Gemini Pro)
    - Image Gen (Trigger: "buatkan gambar")
    - Video Gen (Trigger: "buatkan video")
    - Flashcard (Trigger: "buatkan flashcard")
    """
    try:
        result = chat_service(
            question=req.message,
            history=req.history,
            subject=req.subject,
            file_url=req.file_url,
            file_base64=req.file_base64,
            mime_type=req.mime_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))