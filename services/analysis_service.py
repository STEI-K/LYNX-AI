from services.gemini_client import client
import json

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

    Format output JSON:
    {{
        "concepts": [...],
        "global_insight": "...",
        "recommendations": ["...", "..."],
        "weak_patterns": ["...", "..."]
    }}
    """

    resp = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return resp.text