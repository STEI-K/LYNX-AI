from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from services.batch_grade_service import process_batch_grading

router = APIRouter()

class SubmissionItem(BaseModel):
    student_id: str
    
    # Untuk Text Grading
    answer: Optional[str] = None 
    
    # Untuk Vision Grading (Gambar di-hosting di Cloudinary/S3)
    file_url: Optional[str] = None
    
    # Konteks Soal (Opsional per siswa)
    question: Optional[str] = None
    rubric: Optional[str] = None
    
    # Khusus LJK (Vision PG)
    key_list: Optional[List[int]] = None 
    
    max_score: int = 100

class BatchRequest(BaseModel):
    assignment_id: str
    # Opsi tipe: 'essay', 'pg', 'vision_essay', 'vision_pg'
    type: str = "essay" 
    submissions: List[SubmissionItem]

@router.post("/")
def batch_grade(req: BatchRequest):
    """
    Endpoint Penilaian Massal (Text & Vision).
    """
    if not req.submissions:
        raise HTTPException(status_code=400, detail="Data submission kosong.")
    
    # Ubah ke dict agar mudah diolah service
    submissions_data = [s.dict() for s in req.submissions]
    
    result = process_batch_grading(submissions_data, req.type)
    
    return {
        "assignment_id": req.assignment_id,
        "batch_result": result
    }