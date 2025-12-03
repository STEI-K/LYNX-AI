import json
from services.gemini_client import get_text_model

def generate_soal_service(subject, topic, difficulty, total, types, language):
    prompt = f"""
    Buatkan paket soal mata kuliah {subject} topik {topic}.
    Level kesulitan: {difficulty}
    Jumlah soal: {total}
    Jenis soal: {types}
    Bahasa: {language}

    Format output JSON STRICT:
    {{
        "questions": [
            {{
                "no": 1,
                "type": "pg",
                "question": "...",
                "choices": ["A", "B", "C", "D"], 
                "answer": 1,
                "rubric": null
            }}
        ]
    }}
    Pastikan JSON valid tanpa markdown block.
    """

    model = get_text_model()
    
    try:
        # Temperature agak tinggi agar soal variatif
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.7}
        )
        # Bersihkan potensi markdown ```json
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return clean_text
    except Exception as e:
        # Return error dalam format string JSON agar frontend tidak bingung
        return json.dumps({"error": str(e)})