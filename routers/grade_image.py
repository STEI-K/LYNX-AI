from typing import List

from fastapi import APIRouter, UploadFile, File, Form
import json

from services.grade_service import grade_pg_service

router = APIRouter()


@router.post("/")
async def grade_image(
    image: UploadFile = File(...),
    type: str = Form(...),
    key: str = Form(...),
):
    """
    Grading lembar jawaban dari gambar.

    - type: saat ini hanya "pg" yang didukung.
    - key: JSON array string, contoh: "[1,0,3,2,...]"
      (index 0-based untuk tiap soal)
    """
    if type != "pg":
        return {"error": "Type not supported yet. Only 'pg' is supported."}

    image_bytes = await image.read()

    key_list: List[int] = json.loads(key)

    result = grade_pg_service(image_bytes, key_list)
    return result