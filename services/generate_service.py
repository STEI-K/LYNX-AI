from typing import List, Literal, Optional, Dict, Any

import json

from utils.ai_clients import get_gemini_flash_model, get_gemini_pro_model
from utils.prompt_loader import build_generate_soal_prompt


def generate_soal_service(
    subject: str,
    topic: Optional[str],
    difficulty: str,
    total_questions: int,
    types: List[Literal["pg", "essay"]],
    language: str = "id",
) -> Dict[str, Any]:
    """
    Generate paket soal lengkap (format C).
    Auto-switch model:
    - Kalau ada essay → pakai Gemini Pro (butuh reasoning)
    - Kalau hanya PG & total_soal > 20 → pakai Flash (cepat)
    - Lainnya → default Flash juga boleh
    """
    has_essay = "essay" in types

    prompt = build_generate_soal_prompt(
        subject=subject,
        topic=topic,
        difficulty=difficulty,
        total_questions=total_questions,
        types=types,
        language=language,
    )

    if has_essay:
        model = get_gemini_pro_model()
    else:
        # soal PG banyak → flash cocok
        if total_questions > 20:
            model = get_gemini_flash_model()
        else:
            model = get_gemini_flash_model()

    response = model.generate_content(prompt)
    text = response.text

    # Parse JSON aman
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # fallback: coba potong dari { pertama sampai } terakhir
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start : end + 1]
            data = json.loads(json_str)
        else:
            raise ValueError("Model tidak mengembalikan JSON valid untuk generate soal.")

    return data