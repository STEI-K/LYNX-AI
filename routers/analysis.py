from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.analysis_service import analysis_performace_service

router = APIRouter()

# REQUEST BODY BARU (Lebih Simpel)
class SmartAnalysisRequest(BaseModel):
    """
    post ke link lynx-ai.up.railway.app/analysis/
    Contoh Request Body:
    {
        "student_id": "stu123",
        "student_name": "Budi",
        "grade_level": "12 SMA"
    }
    """
    student_id: str   # Kunci utama untuk cari data di DB
    student_name: str # Untuk konteks sapaan di Prompt AI
    grade_level: str  # e.g., "12 SMA"

@router.post("/")
def analyze_report_card(req: SmartAnalysisRequest):
    """
    Endpoint Analisis Raport Otomatis.
    Mengambil data real-time dari database 'submissions'.
    """
    result = analysis_performace_service(
        req.student_id,
        req.student_name,
        req.grade_level
    )
    
    if "error" in result:
        # Jika error karena data tidak ada, return 404
        if "Belum ada data" in result["error"]:
             raise HTTPException(status_code=404, detail=result["error"])
        # Error lain (koneksi/AI) return 500
        raise HTTPException(status_code=500, detail=result["error"])
        
    """
    Return Format:
    
    """
    return {"analysis": result}