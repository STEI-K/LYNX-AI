from typing import List, Dict, Any

from utils.ai_clients import get_gemini_flash_model
from utils.prompt_loader import build_concept_analysis_prompt


def summarize_concepts_service(attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Advanced analytics (Mode C) – konsep:
    - Input: list attempt
      {
        "student_id": str,
        "question_id": int,
        "concepts": [str],
        "correct": bool,
        "time_spent": float,
        "difficulty": "easy" | "medium" | "hard"
      }

    - Output: ringkasan mastery per konsep + insight dari LLM
    """
    # Kamu bisa tambahin pre-aggregate lokal, tapi untuk hackathon
    # bisa langsung lempar ke LLM dengan sedikit pre-format.
    model = get_gemini_flash_model()  # flash cukup, cuma analisis text

    prompt = build_concept_analysis_prompt()

    import json

    attempts_json = json.dumps(attempts, ensure_ascii=False, indent=2)

    response = model.generate_content(
        prompt + "\n\nBerikut data attempt dalam JSON:\n" + attempts_json
    )

    text = response.text
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start : end + 1]
            data = json.loads(json_str)
        else:
            raise ValueError("Model tidak mengembalikan JSON valid untuk analytics.")

    return data