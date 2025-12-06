from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.analysis_service import analysis_performace_service

router = APIRouter()

class SubjectScore(BaseModel):
    subject: str
    score: float
    target: Optional[float] = 75  # Nilai KKM/Target (Default 75)

class ReportCardRequest(BaseModel):
    student_name: str
    grade_level: str
    scores: List[SubjectScore]

@router.post("/")
def analyze_report_card(req: ReportCardRequest):
    """
    Endpoint untuk menganalisis performa belajar siswa berdasarkan nilai raport.
    """
    result = analysis_performace_service(
        req.student_name,
        req.grade_level,
        [s.dict() for s in req.scores]
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return {"analysis": result}