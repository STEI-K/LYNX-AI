from fastapi import APIRouter
from pydantic import BaseModel
from services.soal_service import generate_soal_service

router = APIRouter()

class GenerateSoalRequest(BaseModel):
    subject: str
    topic: str
    difficulty: str
    total_questions: int
    types: list
    language: str = "id"

@router.post("/soal")
def generate_soal(req: GenerateSoalRequest):
    result = generate_soal_service(
        req.subject,
        req.topic,
        req.difficulty,
        req.total_questions,
        req.types,
        req.language
    )
    return {"generated": result}