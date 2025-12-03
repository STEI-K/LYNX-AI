import json
from services.gemini_client import get_vision_model

def grade_pg_vision(image_bytes: bytes, key_list: list):
    key_string = json.dumps(key_list)
    
    prompt = f"""
    Ini adalah foto lembar jawaban pilihan ganda.

    Tugasmu:
    1. Baca semua nomor jawaban.
    2. Deteksi jawaban siswa (A/B/C/D/E).
    3. Bandingkan dengan kunci ini: {key_string} (0=A, 1=B, dst).
    
    Output JSON STRICT:
    {{
        "score": <angka>,
        "total": <total_soal>,
        "correct": <jumlah_benar>,
        "answers": [0, 1, 2, ...],  // Jawaban siswa yang terbaca
        "detail": [
            {{"no": 1, "student": 1, "key": 2, "correct": false}}
        ]
    }}
    """

    model = get_vision_model()

    try:
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        return response.text.replace("```json", "").replace("```", "").strip()
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'