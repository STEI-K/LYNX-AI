from fastapi import APIRouter
from pydantic import BaseModel
from services.analysis_service import analysis_mastery_service

router = APIRouter()

class Attempt(BaseModel):
    student_id: str
    question_id: int
    concepts: list
    correct: bool
    time_spent: float
    difficulty: str

class AnalysisRequest(BaseModel):
    attempts: list[Attempt]

@router.post("/")
def analyze(req: AnalysisRequest):
    result = analysis_mastery_service([a.dict() for a in req.attempts])
    return {"analysis": result}