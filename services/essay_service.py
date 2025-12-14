from services.gemini_client import get_text_model

def grade_essay_service(question, rubric, answer, max_score):
    prompt = f"""
    Kamu adalah AI Essay Grader.
    Feedback harus konstruktif dan spesifik serta deskripsi yang rapih.
    Pertanyaan: {question}
    Jawaban siswa: {answer}
    Rubrik: {rubric}

    Nilai dari 0 sampai {max_score}.
    
    Output JSON STRICT:
    {{
        "score": <angka>,
        "max_score": {max_score},
        "strengths": "...",
        "weaknesses": "...",
        "suggestions": "..."
    }}
    """

    model = get_text_model()

    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return clean_text
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'