from typing import List, Literal, Optional, Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.generate_service import generate_soal_service

router = APIRouter()


class GenerateSoalRequest(BaseModel):
    subject: str = Field(..., description="Nama mata kuliah / mapel, misal: Kalkulus 1")
    topic: Optional[str] = Field(None, description="Topik spesifik (opsional)")
    difficulty: str = Field(
        "medium",
        description="easy | medium | hard | mixed",
    )
    total_questions: int = Field(10, ge=1, le=100)
    types: List[Literal["pg", "essay"]] = Field(
        ...,
        description='List tipe soal, contoh: ["pg"], ["essay"], ["pg", "essay"]',
    )
    language: str = Field("id", description="id/en/dll")


@router.post("/soal")
async def generate_soal(req: GenerateSoalRequest) -> Dict[str, Any]:
    """
    Generate paket soal untuk dosen (format C).
    """
    data = generate_soal_service(
        subject=req.subject,
        topic=req.topic,
        difficulty=req.difficulty,
        total_questions=req.total_questions,
        types=req.types,
        language=req.language,
    )
    return data