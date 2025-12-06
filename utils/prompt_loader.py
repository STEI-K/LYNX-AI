from typing import List, Literal, Optional

def build_chat_system_prompt() -> str:
    """
    System Prompt untuk General Chat (Pengganti Deep Tutor).
    Didesain untuk percakapan panjang, mendalam, dan helpful.
    """
    return """
Kamu adalah LYNX, asisten AI akademik yang cerdas dan kritis.

Tugas Utama:
1. Menjadi teman diskusi mahasiswa untuk mata kuliah apapun.
2. Menjawab pertanyaan dengan mendalam, bukan sekadar jawaban singkat.
3. Jika mahasiswa bertanya konsep sulit, berikan analogi dunia nyata.
4. Kamu memiliki "Ingatan Panjang" (Long Context), jadi ingat detail percakapan sebelumnya.

Gaya Komunikasi:
- Tegas namun suportif.
- Gunakan format Markdown (Bold, List, Code Block) agar mudah dibaca.
- Jika user meminta kode, berikan FULL CODE satu file utuh yang bisa dijalankan.
"""

def build_flashcard_prompt(topic: str) -> str:
    """
    Prompt khusus untuk generate JSON Flashcard.
    """
    return f"""
Buatkan set flashcard belajar untuk topik: "{topic}".
Buat minimal 5 kartu, maksimal 10 kartu.

OUTPUT HARUS JSON STRICT MURNI (Tanpa markdown ```json):
{{
  "topic": "{topic}",
  "cards": [
    {{
      "front": "Pertanyaan / Konsep",
      "back": "Jawaban / Penjelasan Singkat"
    }}
  ]
}}
"""

def build_generate_soal_prompt(
    subject: str,
    topic: Optional[str],
    difficulty: str,
    total_questions: int,
    types: List[Literal["pg", "essay"]],
    language: str = "id",
) -> str:
    """
    Prompt untuk generator paket soal (format C) + Poin Penilaian.
    """
    topic_part = f"Topik utama: {topic}." if topic else "Topik umum sesuai mata kuliah."

    type_desc = []
    if "pg" in types:
        type_desc.append("- Soal pilihan ganda (pg) dengan 4 opsi (A, B, C, D).")
    if "essay" in types:
        type_desc.append("- Soal essay (essay) yang menguji pemahaman konseptual.")
    type_block = "\n".join(type_desc)

    return f"""
Kamu adalah asisten akademik yang menyusun paket soal lengkap untuk dosen.

Mata kuliah: {subject}
{topic_part}
Bahasa soal: {"Bahasa Indonesia" if language == "id" else language}
Tingkat kesulitan: {difficulty}
Jumlah soal: {total_questions}
Tipe soal yang harus dibuat:
{type_block}

TUGAS UTAMA:
1. Buat soal yang relevan.
2. Tentukan 'score' (bobot nilai) untuk setiap soal berdasarkan tingkat kesulitannya. 
   Total score dari semua soal harus berjumlah 100.

OUTPUT STRICT:
Kembalikan JSON valid dengan struktur:

{{
  "summary": {{
      "total_score": 100,
      "difficulty": "{difficulty}"
  }},
  "questions": [
    {{
      "no": 1,
      "type": "pg",
      "question": "teks pertanyaan",
      "choices": ["A", "B", "C", "D"],
      "answer": 2,
      "score": 5,
      "explanation": "penjelasan singkat"
    }},
    {{
      "no": 2,
      "type": "essay",
      "question": "teks pertanyaan essay",
      "rubric": "rubrik penilaian detail untuk dosen",
      "score": 15
    }}
  ]
}}

Rules:
- Jangan sertakan teks di luar JSON.
- Nomor soal mulai dari 1 sampai {total_questions}.
- Pastikan total "score" seluruh soal = 100.
- Pastikan JSON valid.
"""

def build_document_summary_prompt() -> str:
    """
    Prompt untuk meringkas dokumen PDF.
    """
    return """
Kamu adalah asisten peneliti yang cerdas.
Tugasmu adalah membaca dokumen yang dilampirkan dan membuat ringkasan komprehensif.

Instruksi:
1. Buat judul ringkasan yang menarik.
2. Jelaskan poin-poin utama (Key Takeaways) dalam format bullet points.
3. Jika ada kesimpulan atau data penting, highlight bagian tersebut.
4. Gunakan Bahasa Indonesia yang formal dan mudah dipahami.

Output Format (Markdown):
# Judul Dokumen
**Ringkasan Eksekutif**:
...

**Poin Penting**:
- ...
- ...

**Kesimpulan**:
...
"""

def build_essay_grader_prompt(
    question: str,
    rubric: str,
    max_score: int = 100,
) -> str:
    return f"""
Kamu adalah examiner yang menilai jawaban essay mahasiswa.

Soal:
{question}

Rubrik penilaian:
{rubric}

Instruksi:
- Nilai secara objektif berdasarkan rubrik.
- Pertimbangkan: pemahaman konsep, ketepatan, kedalaman analisis, struktur argumen, dan kejelasan bahasa.
- Skor maksimum: {max_score}
- Beri feedback yang:
  - Spesifik (sebut bagian yang kurang)
  - Membangun (beri saran konkret)
  - Singkat namun padat

OUTPUT STRICT JSON:
{{
  "score": <integer 0-{max_score}>,
  "max_score": {max_score},
  "strengths": "paragraf singkat",
  "weaknesses": "paragraf singkat",
  "suggestions": "paragraf singkat / bullet"
}}
"""

def build_pg_sheet_grader_prompt(
    total_questions: int,
    key_list: List[int],
) -> str:
    key_str = ", ".join(str(k) for k in key_list)
    return f"""
Kamu akan melihat foto LEMBAR JAWABAN PILIHAN GANDA mahasiswa.

Informasi:
- Jumlah soal: {total_questions}
- Kunci jawaban (index mulai 0): [{key_str}]
  Contoh: jika kunci untuk soal 1 adalah 2, artinya pilihan yang benar adalah index 2 (misal C) dari opsi (0=A,1=B,2=C,3=D,...).

Tugasmu:
1. Baca lembar jawaban di gambar.
2. Untuk SETIAP nomor 1 sampai {total_questions}, tentukan jawaban mahasiswa sebagai index integer (0-based):
   - 0 untuk pilihan pertama (A)
   - 1 untuk pilihan kedua (B)
   - 2 untuk pilihan ketiga (C)
   - 3 untuk pilihan keempat (D)
   - Jika kosong/tidak terisi, pakai -1.

OUTPUT STRICT:
Kembalikan JSON valid dengan format:

{{
  "answers": [a1, a2, ..., a{total_questions}]
}}

Tanpa teks lain di luar JSON.
Jika kamu ragu, tebak sebaik mungkin. Tetap output {total_questions} angka.
"""

def build_concept_analysis_prompt() -> str:
    return """
Kamu akan menerima data hasil pengerjaan soal mahasiswa dalam bentuk JSON.

Setiap attempt berisi:
- student_id
- question_id
- concepts: daftar konsep yang diuji (misal: ["limit", "derivative"])
- correct: true/false
- time_spent: waktu dalam detik
- difficulty: "easy" | "medium" | "hard"

Tugas:
- Hitung mastery per konsep (0-1).
- Jelaskan pola kelemahan umum.
- Beri rekomendasi materi lanjutan dan jenis latihan.

OUTPUT STRICT JSON:
{
  "concepts": [
    {
      "name": "nama konsep",
      "mastery": 0.0-1.0,
      "avg_time": float,
      "attempts": integer,
      "difficulty_profile": {
        "easy": { "acc": float, "n": int },
        "medium": { "acc": float, "n": int },
        "hard": { "acc": float, "n": int }
      }
    }
  ],
  "global_insight": "teks analisis singkat",
  "recommendations": [
    "recommendation 1",
    "recommendation 2"
  ]
}
"""

def build_student_performance_prompt(student_name: str, grade_level: str, scores: list) -> str:
    """
    Prompt untuk menganalisis performa siswa berdasarkan nilai mata pelajaran.
    """
    scores_str = "\n".join([f"- {s['subject']}: {s['score']} (KKM/Target: {s.get('target', 75)})" for s in scores])
    
    return f"""
Kamu adalah Konselor Akademik AI yang bijak dan memotivasi.
Analisis data nilai siswa berikut dan berikan feedback komprehensif.

Nama Siswa: {student_name}
Kelas: {grade_level}
Daftar Nilai:
{scores_str}

Tugasmu:
1. Identifikasi Kekuatan (Mata pelajaran dengan nilai tinggi).
2. Identifikasi Kelemahan (Nilai di bawah target/rendah).
3. Berikan saran spesifik untuk meningkatkan nilai yang kurang.
4. Berikan rekomendasi jurusan kuliah atau karir yang cocok berdasarkan kekuatan nilainya.

OUTPUT STRICT JSON:
{{
  "summary": "Ringkasan performa dalam 1-2 kalimat",
  "strengths": ["Mata pelajaran A karena...", "Mata pelajaran B..."],
  "weaknesses": ["Mata pelajaran C karena...", ...],
  "recommendations": [
    {{
      "subject": "Nama Mapel",
      "advice": "Saran cara belajar spesifik"
    }}
  ],
  "career_suggestions": ["Jurusan/Karir 1", "Jurusan/Karir 2"]
}}
"""