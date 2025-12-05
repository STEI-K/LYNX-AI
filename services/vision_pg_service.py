import json
from services.gemini_client import get_vision_model

def grade_pg_vision(image_bytes: bytes, key_list: list):
    """
    Menilai Lembar Jawaban Komputer (LJK) atau kertas jawaban PG dari gambar.
    Menggunakan Gemini Vision untuk OCR + Grading.
    """
    
    # Format kunci jawaban agar mudah dibaca AI (misal: "1:A, 2:B, 3:C")
    # Asumsi key_list adalah [0, 1, 2] dimana 0=A, 1=B, dst.
    mapping = ["A", "B", "C", "D", "E"]
    formatted_keys = []
    for i, k in enumerate(key_list):
        if isinstance(k, int) and 0 <= k < len(mapping):
            val = mapping[k]
        else:
            val = str(k) # Fallback jika inputnya sudah huruf
        formatted_keys.append(f"No {i+1}: {val}")
    
    key_string = ", ".join(formatted_keys)
    
    prompt = f"""
    Kamu adalah Mesin Koreksi LJK (Lembar Jawab Komputer) Otomatis.
    
    Tugasmu:
    1. LIHAT gambar lembar jawaban siswa.
    2. BACA jawaban yang dipilih siswa (tanda silang/bulatan hitam) untuk setiap nomor.
    3. BANDINGKAN dengan Kunci Jawaban Resmi berikut:
       [{key_string}]
    
    Aturan Penilaian:
    - Jika jawaban siswa sesuai kunci -> BENAR.
    - Jika jawaban siswa beda / kosong / ganda -> SALAH.
    - Hitung Skor Akhir = (Jumlah Benar / Total Soal) * 100.
    
    OUTPUT HARUS JSON STRICT (Tanpa markdown ```json):
    {{
        "score": <float 0-100>,
        "max_score": 100,
        "total_questions": {len(key_list)},
        "correct_count": <int>,
        "answers": ["A", "B", ...],  // Jawaban siswa yang terbaca urut no 1, 2...
        "details": [
            {{"no": 1, "student_ans": "A", "key": "A", "status": "Correct"}},
            {{"no": 2, "student_ans": "C", "key": "B", "status": "Wrong"}}
        ],
        "feedback": "Salah di nomor X, Y. Jawaban benar adalah..."
    }}
    """

    model = get_vision_model()

    try:
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        # Bersihkan response dari markdown code block jika ada
        return response.text.replace("```json", "").replace("```", "").strip()
        
    except Exception as e:
        # Return JSON error agar frontend tidak crash
        return json.dumps({
            "score": 0,
            "error": f"Vision Processing Failed: {str(e)}",
            "feedback": "Gagal membaca gambar. Pastikan foto jelas."
        })