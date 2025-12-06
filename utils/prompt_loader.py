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

OUTPUT STRICT:
Kembalikan JSON valid dengan struktur:

{{
  "questions": [
    {{
      "no": 1,
      "type": "pg",
      "question": "teks pertanyaan",
      "choices": ["A", "B", "C", "D"],
      "answer": 2,
      "explanation": "penjelasan mengapa jawaban benar"
    }},
    {{
      "no": 2,
      "type": "essay",
      "question": "teks pertanyaan essay",
      "rubric": "rubrik penilaian detail untuk dosen"
    }}
  ]
}}

Rules:
- Jangan sertakan teks di luar JSON.
- Nomor soal mulai dari 1 sampai {total_questions}.
- Untuk soal pg: selalu 4 opsi, index 'answer' mulai dari 0.
- Untuk essay: sertakan rubric yang jelas (indikator nilai tinggi vs rendah).
- Pastikan JSON valid.
"""

def build_essay_grader_prompt(question: str, rubric: str, max_score: int = 100) -> str:
    return f"""
Kamu adalah examiner yang menilai jawaban essay mahasiswa.

Soal: {question}
Rubrik: {rubric}
Max Score: {max_score}

OUTPUT STRICT JSON:
{{
  "score": <integer>,
  "max_score": {max_score},
  "strengths": "...",
  "weaknesses": "...",
  "suggestions": "..."
}}
"""

def build_pg_sheet_grader_prompt(total_questions: int, key_list: List[int]) -> str:
    key_str = ", ".join(str(k) for k in key_list)
    return f"""
Kamu akan melihat foto LEMBAR JAWABAN PILIHAN GANDA mahasiswa.
Jumlah soal: {total_questions}
Kunci jawaban (0=A, 1=B, dst): [{key_str}]

Tugas: Baca jawaban siswa dari gambar.

OUTPUT STRICT JSON:
{{
  "answers": [0, 1, -1, 2, ...] // Array integer sepanjang {total_questions}
}}
"""

def build_concept_analysis_prompt() -> str:
    return """
Analisis mastery konsep dari data JSON berikut.
OUTPUT STRICT JSON:
{
  "concepts": [{"name": "...", "mastery": 0.0-1.0}],
  "global_insight": "...",
  "recommendations": ["..."]
}
"""