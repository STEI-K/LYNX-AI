from typing import List, Dict, Any

import io
import json

from PIL import Image

from utils.ai_clients import get_gemini_pro_model
from utils.prompt_loader import build_pg_sheet_grader_prompt


def _parse_answers_from_model(text: str, expected_len: int) -> List[int]:
    """
    Parse output JSON dari model menjadi list jawaban integer.

    Struktur ideal:
    {
      "answers": [0,1,2,...]
    }
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start : end + 1]
            data = json.loads(json_str)
        else:
            raise ValueError("Model tidak mengembalikan JSON valid untuk lembar jawaban.")

    answers = data.get("answers", [])
    if not isinstance(answers, list):
        raise ValueError("Field 'answers' tidak berbentuk list.")

    # Normalisasi panjang
    if len(answers) < expected_len:
        answers = answers + [-1] * (expected_len - len(answers))
    elif len(answers) > expected_len:
        answers = answers[:expected_len]

    # Pastikan int
    cleaned: List[int] = []
    for a in answers:
        try:
            cleaned.append(int(a))
        except (ValueError, TypeError):
            cleaned.append(-1)

    return cleaned


def grade_pg_service(image_bytes: bytes, key_list: List[int]) -> Dict[str, Any]:
    """
    Grader lembar jawaban PG dari gambar.

    - Menggunakan Gemini Pro (Vision).
    - TIDAK nge-hardcode template – kita suruh model baca pola apapun.
    - Input:
        image_bytes: gambar lembar jawaban
        key_list: list kunci jawaban (index 0-based)
    """
    total_questions = len(key_list)
    model = get_gemini_pro_model()  # 1.5 Pro multimodal

    prompt = build_pg_sheet_grader_prompt(
        total_questions=total_questions,
        key_list=key_list,
    )

    # Load image ke PIL
    image = Image.open(io.BytesIO(image_bytes))

    response = model.generate_content(
        [
            prompt,
            image,
        ]
    )
    text = response.text

    student_answers = _parse_answers_from_model(text, total_questions)

    # Hitung skor
    detail = []
    correct_count = 0
    score_per_question = 100 // total_questions if total_questions > 0 else 0

    for idx, (stud, key) in enumerate(zip(student_answers, key_list), start=1):
        is_correct = stud == key
        if is_correct:
            correct_count += 1
        detail.append(
            {
                "no": idx,
                "student": stud,
                "key": key,
                "correct": is_correct,
            }
        )

    score = correct_count * score_per_question

    return {
        "score": score,
        "total": total_questions,
        "correct": correct_count,
        "answers": student_answers,
        "detail": detail,
        "raw_model_output": text,  # optional: bisa di-hide di FE kalau nggak mau
    }