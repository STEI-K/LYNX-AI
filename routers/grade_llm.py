from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.grade_llm_service import grade_essay_service

router = APIRouter()


class EssayGradeRequest(BaseModel):
    question: str = Field(..., description="Soal essay / prompt yang diberikan")
    rubric: str = Field(..., description="Rubrik penilaian detail")
    answer: str = Field(..., description="Jawaban mahasiswa")
    max_score: int = Field(100, description="Skor maksimum", ge=1)


@router.post("/essay")
async def grade_essay(req: EssayGradeRequest) -> Dict[str, Any]:
    """
    Auto grading essay dengan feedback.
    """
    result = grade_essay_service(
        question=req.question,
        rubric=req.rubric,
        answer=req.answer,
        max_score=req.max_score,
    )
    return result