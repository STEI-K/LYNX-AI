import json
from services.gemini_client import get_text_model

def analysis_mastery_service(attempts):
    prompt = f"""
    Kamu adalah AI Learning Analyst.

    Berikut data attempts siswa (JSON):
    {json.dumps(attempts)}

    Buat analisis:
    - mastery per konsep
    - kelemahan utama kelas
    - rekomendasi belajar
    - pola kesalahan
    - summary

    Format output JSON STRICT:
    {{
        "concepts": [],
        "global_insight": "...",
        "recommendations": ["...", "..."],
        "weak_patterns": ["...", "..."]
    }}
    """

    model = get_text_model()
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return clean_text
    except Exception as e:
        return json.dumps({"error": str(e)})