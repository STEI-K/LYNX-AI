from fastapi import APIRouter
from pydantic import BaseModel
from services.essay_service import grade_essay_service

router = APIRouter()

class EssayGradeRequest(BaseModel):
    question: str
    rubric: str
    answer: str
    max_score: int = 100

@router.post("/")
def grade_essay(req: EssayGradeRequest):
    result = grade_essay_service(
        req.question,
        req.rubric,
        req.answer,
        req.max_score
    )
    return {"grading": result}