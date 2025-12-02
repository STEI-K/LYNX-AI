from fastapi import APIRouter, UploadFile, File, Form
import json

from services.vision_pg_service import grade_pg_vision
from services.vision_essay_service import grade_essay_vision

router = APIRouter()

@router.post("/pg")
async def grade_pg(image: UploadFile = File(...), key: str = Form(...)):

    image_bytes = await image.read()
    key_list = json.loads(key)

    result = grade_pg_vision(image_bytes, key_list)
    return {"grading": result}


@router.post("/essay")
async def grade_essay_image(
    image: UploadFile = File(...),
    question: str = Form(...),
    rubric: str = Form(...),
    max_score: int = Form(100)
):

    image_bytes = await image.read()

    result = grade_essay_vision(image_bytes, question, rubric, max_score)
    return {"grading": result}