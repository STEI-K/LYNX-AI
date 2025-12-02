from typing import List, Dict, Optional, Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.chat_service import deep_tutor_service

router = APIRouter()


class HistoryTurn(BaseModel):
    role: str = Field(..., description='"user" atau "assistant"')
    content: str


class TutorRequest(BaseModel):
    question: str
    subject: Optional[str] = None
    student_level: Optional[str] = None
    history: Optional[List[HistoryTurn]] = None


@router.post("/deep-tutor")
async def deep_tutor(req: TutorRequest) -> Dict[str, Any]:
    """
    Deep Tutor endpoint.
    """
    result = deep_tutor_service(
        question=req.question,
        history=[h.dict() for h in (req.history or [])],
        subject=req.subject,
        student_level=req.student_level,
    )
    return result