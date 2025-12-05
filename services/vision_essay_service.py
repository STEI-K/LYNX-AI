from services.gemini_client import get_vision_model

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
    
    Soal: {question}
    Rubrik: {rubric}
    """

    model = get_vision_model()
    
    try:
        # SDK Google GenAI v1.0+ menerima list [prompt, image]
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        return response.text.replace("```json", "").replace("```", "").strip()
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'