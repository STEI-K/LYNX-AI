from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.analysis_service import analysis_performace_service

router = APIRouter()

class SmartAnalysisRequest(BaseModel):
    student_id: str
    student_name: str # Opsional, buat konteks prompt AI aja
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
        # Jika error karena data kosong, return 404, selain itu 500
        if "Belum ada data" in result["error"]:
             raise HTTPException(status_code=404, detail=result["error"])
        raise HTTPException(status_code=500, detail=result["error"])
        
    return {"analysis": result}