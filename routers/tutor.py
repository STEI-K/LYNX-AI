from fastapi import APIRouter
from pydantic import BaseModel
from services.tutor_service import tutor_service

router = APIRouter()

class TutorRequest(BaseModel):
    question: str
    subject: str
    student_level: str
    history: list = []

@router.post("/")
def tutor(req: TutorRequest):
    result = tutor_service(req.question, req.subject, req.student_level, req.history)
    return {"reply": result}