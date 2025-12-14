from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from services.batch_grade_service import _download_image, process_batch_grading, _download_pdf
from services.vision_pg_service import get_rubric_vision, extract_rubric_vision
from services.vision_essay_service import extract_text_from_image, extract_text_from_pdf    

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

class rubricRequest(BaseModel):
    assignment_id: str
    image_url: Optional[str] = None
    pdf_url: Optional[str] = None

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

@router.post("/getrubric")
def get_rubric(req: rubricRequest):
    """
    Endpoint untuk mengubah image URL menjadi list string dengan get_rubric_vision.
    """
    """
    CONTOH REQUEST:
    {
        "assignment_id": "pg_rubric",
        "image_url": "https://example.com/image.jpg"
    }
    """
    
    if req.assignment_id.strip() == "" or req.image_url.strip() == "":
        raise HTTPException(status_code=400, detail="assignment_id dan image_url harus diisi.")
    if req.assignment_id == "pg_rubric":
        if req.image_url:
            try:
                image_bytes = _download_image(req.image_url)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Gagal mengunduh gambar: {str(e)}")
            
            rubric_list = get_rubric_vision(image_bytes)
            return {
                "assignment_id": req.assignment_id,
                "rubric": rubric_list
            }
        elif req.pdf_url:
            try:
                pdf_bytes = _download_pdf(req.pdf_url)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Gagal mengunduh PDF: {str(e)}")
            
            rubric_list = extract_rubric_vision(pdf_bytes)
            return {
                "assignment_id": req.assignment_id,
                "rubric": rubric_list
            }
    
    elif req.assignment_id == "essay_rubric":
        if req.pdf_url:
            try:
                pdf_bytes = _download_pdf(req.pdf_url)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Gagal mengunduh PDF: {str(e)}")
            
            extracted_text = extract_text_from_pdf(pdf_bytes)
            return {
                "assignment_id": req.assignment_id,
                "extracted_text": extracted_text
            }
        elif req.image_url:
            try:
                image_bytes = _download_image(req.image_url)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Gagal mengunduh gambar: {str(e)}")
            
            extracted_text = extract_text_from_image(image_bytes)
            return {
                "assignment_id": req.assignment_id,
                "extracted_text": extracted_text
            }
        else:
            raise HTTPException(status_code=400, detail="Untuk essay_rubric, harus menyediakan image_url atau pdf_url.")
    else:
        raise HTTPException(status_code=400, detail="assignment_id tidak valid.")