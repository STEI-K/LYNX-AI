from typing import List, Dict, Any, Optional

from utils.ai_clients import get_gemini_pro_model
from utils.prompt_loader import build_deep_tutor_system_prompt
from utils.content_safety import is_safe_text


def deep_tutor_service(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    subject: Optional[str] = None,
    student_level: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deep Tutor:
    - pakai Gemini Pro (butuh reasoning)
    - history format: [{ "role": "user"/"assistant", "content": "..." }]
    """
    safe, reason = is_safe_text(question)
    if not safe:
        return {
            "answer": "Maaf, aku tidak bisa menjawab pertanyaan ini karena melanggar kebijakan konten.",
            "safety_reason": reason,
        }

    model = get_gemini_pro_model()

    system_prompt = build_deep_tutor_system_prompt()

    convo = [system_prompt]
    if subject:
        convo.append(f"Mata kuliah / subjek: {subject}")
    if student_level:
        convo.append(f"Tingkat mahasiswa: {student_level}")

    convo.append("Berikut konteks percakapan sebelumnya (jika ada).")

    if history:
        for turn in history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            convo.append(f"{role.upper()}: {content}")

    convo.append(f"PERTANYAAN TERKINI MAHASISWA:\n{question}")

    response = model.generate_content("\n\n".join(convo))
    answer = response.text

    return {
        "answer": answer,
    }