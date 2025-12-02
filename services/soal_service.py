from services.gemini_client import client

def generate_soal_service(subject, topic, difficulty, total, types, language):
    prompt = f"""
    Buatkan paket soal mata kuliah {subject} topik {topic}.
    Level kesulitan: {difficulty}
    Jumlah soal: {total}
    Jenis soal: {types}
    Bahasa: {language}

    Format output JSON:
    {{
        "questions": [
            {{
                "no": 1,
                "type": "pg/essay",
                "question": "...",
                "choices": ["A", "B", "C", "D"],  # kosong jika essay
                "answer": 1,                      # untuk PG
                "rubric": "..."                   # untuk essay
            }}
        ]
    }}
    """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return response.text