from typing import List, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.analysis_service import summarize_concepts_service

router = APIRouter()


class Attempt(BaseModel):
    student_id: str
    question_id: int
    concepts: List[str] = Field(..., description="Daftar konsep yang diuji")
    correct: bool
    time_spent: float = Field(..., description="Waktu pengerjaan dalam detik")
    difficulty: str = Field(..., description='"easy" | "medium" | "hard"')


class ConceptAnalysisRequest(BaseModel):
    attempts: List[Attempt]


@router.post("/mastery")
async def analyze_mastery(req: ConceptAnalysisRequest) -> Dict[str, Any]:
    """
    Analisis mastery konsep, pattern kesalahan, dan rekomendasi.
    """
    attempts_dict = [a.dict() for a in req.attempts]
    result = summarize_concepts_service(attempts_dict)
    return result