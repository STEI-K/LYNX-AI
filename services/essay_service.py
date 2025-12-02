from services.gemini_client import client

def grade_essay_service(question, rubric, answer, max_score):
    prompt = f"""
    Kamu adalah AI Essay Grader.

    Pertanyaan:
    {question}

    Jawaban siswa:
    {answer}

    Gunakan rubrik ini:
    {rubric}

    Nilai dari 0 sampai {max_score}.
    Berikan output JSON:
    {{
        "score": <angka>,
        "max_score": {max_score},
        "strengths": "...",
        "weaknesses": "...",
        "suggestions": "..."
    }}
    """

    resp = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=prompt
    )

    return resp.text