from typing import Dict, Any

import json

from utils.ai_clients import get_openai_client
from utils.prompt_loader import build_essay_grader_prompt


def grade_essay_service(
    question: str,
    rubric: str,
    answer: str,
    max_score: int = 100,
) -> Dict[str, Any]:
    """
    Essay grader:
    - Pakai OpenAI (biar load ke provider lain juga, ngurangi limit di Gemini)
    """
    client = get_openai_client()

    prompt = build_essay_grader_prompt(
        question=question,
        rubric=rubric,
        max_score=max_score,
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Kamu adalah penilai essay yang objektif."},
            {
                "role": "user",
                "content": (
                    prompt
                    + "\n\nBerikut jawaban mahasiswa:\n"
                    + answer
                ),
            },
        ],
        temperature=0.2,
    )

    text = resp.choices[0].message.content

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start : end + 1]
            data = json.loads(json_str)
        else:
            raise ValueError("Model tidak mengembalikan JSON valid untuk grading essay.")

    # Safety net
    score = int(data.get("score", 0))
    data["score"] = max(0, min(max_score, score))
    data["max_score"] = max_score

    return data