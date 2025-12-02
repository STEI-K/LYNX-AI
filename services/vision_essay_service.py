from services.gemini_client import client

def grade_essay_vision(image_bytes, question, rubric, max_score):
    prompt = f"""
    Kamu adalah AI OCR + Essay Grader.

    Langkah:
    1. Ekstrak teks dari gambar.
    2. Nilai jawaban siswa berdasarkan rubrik.
    3. Format JSON:
    {{
        "extracted_answer": "...",
        "score": <angka>,
        "max_score": {max_score},
        "strengths": "...",
        "weaknesses": "...",
        "suggestions": "..."
    }}
    """

    resp = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=[
            {
                "mime_type": "image/jpeg",
                "data": image_bytes
            },
            prompt
        ]
    )

    return resp.text