import json
from services.gemini_client import client

def grade_pg_vision(image_bytes: bytes, key_list: list):
    resp = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            {
                "mime_type": "image/jpeg",
                "data": image_bytes
            },
            """
            Ini adalah foto lembar jawaban pilihan ganda.

            Tugasmu:
            1. Baca semua nomor jawaban (tanpa format tertentu).
            2. Deteksi jawaban siswa per nomor (0-4).
            3. Bandingkan dengan kunci berikut:
            """ + json.dumps(key_list) + """
            4. Buat format output JSON seperti ini:

            {
                "score": <angka>,
                "total": <total_soal>,
                "correct": <jumlah benar>,
                "answers": [0,1,2,...],
                "detail": [
                    {"no": 1, "student": 1, "key": 2, "correct": true}
                ]
            }
            """
        ]
    )

    return resp.text