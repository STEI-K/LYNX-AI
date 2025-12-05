import time
import json
import requests
from services.essay_service import grade_essay_service
from services.vision_essay_service import grade_essay_vision
from services.vision_pg_service import grade_pg_vision

def process_batch_grading(submissions: list, grading_type: str = "essay"):
    """
    Memproses penilaian massal untuk berbagai tipe soal.
    """
    results = []
    print(f"🚀 Memulai Batch Grading ({grading_type.upper()}) - Total: {len(submissions)}")
    
    for sub in submissions:
        student_id = sub.get("student_id")
        result_json = "{}"
        
        try:
            # --- TIPE 1: ESSAY TEKS (Pakai AI) ---
            if grading_type == "essay":
                question = sub.get("question")
                rubric = sub.get("rubric")
                answer = sub.get("answer")
                max_score = sub.get("max_score", 100)
                
                # AI Call
                result_json = grade_essay_service(question, rubric, answer, max_score)
                time.sleep(1) 

            # --- TIPE 2: PG TEKS (Pakai Logic - Cepat) ---
            elif grading_type == "pg":
                # Asumsi rubric = Kunci Jawaban (misal: "A,B,C" atau "A, B, C")
                # Asumsi answer = Jawaban Siswa (misal: "A,C,C")
                
                # 1. Parsing Input menjadi List
                

                keys = parse_input(sub.get("rubric"))
                answers = parse_input(sub.get("answer"))
                max_score = sub.get("max_score", 100)
                
                # Validasi Panjang
                total_soal = len(keys)
                if total_soal == 0:
                    score = 0
                    feedback = "Error: Kunci jawaban kosong."
                else:
                    correct_count = 0
                    wrong_details = []
                    
                    # Loop per nomor
                    for i, key in enumerate(keys):
                        # Ambil jawaban siswa untuk nomor ini (aman jika index out of range)
                        student_ans = answers[i] if i < len(answers) else "-"
                        
                        if student_ans == key:
                            correct_count += 1
                        else:
                            # Catat yang salah
                            wrong_details.append(f"No {i+1}: Jawab '{student_ans}', Kunci '{key}'")
                    
                    # Hitung Skor Akhir (Skala 100)
                    score = (correct_count / total_soal) * max_score
                    score = round(score, 2) # Bulatkan 2 desimal
                    
                    # Buat Feedback
                    if len(wrong_details) == 0:
                        feedback = "Sempurna! Semua jawaban benar."
                    else:
                        feedback = f"Salah {len(wrong_details)} dari {total_soal} soal. Detail: " + ", ".join(wrong_details)
                
                result_json = json.dumps({
                    "score": score, 
                    "max_score": max_score, 
                    "feedback": feedback,
                    "correct_count": correct_count,
                    "total_questions": total_soal
                })

            # --- TIPE 3: VISION ESSAY (Gambar -> AI) ---
            elif grading_type == "vision_essay":
                image_url = sub.get("file_url")
                question = sub.get("question")
                rubric = sub.get("rubric")
                max_score = sub.get("max_score", 100)
                
                img_bytes = _download_image(image_url)
                
                if img_bytes:
                    result_json = grade_essay_vision(img_bytes, question, rubric, max_score)
                    time.sleep(1)
                else:
                    result_json = '{"error": "Gagal download gambar"}'

            # --- TIPE 4: VISION PG / LJK (Gambar -> AI) ---
            elif grading_type == "vision_pg":
                image_url = sub.get("file_url")
                rubric = parse_input(sub.get("rubric", "")) 
                img_bytes = _download_image(image_url)
                
                if img_bytes:
                    result_json = grade_pg_vision(img_bytes, rubric)
                    time.sleep(1)
                else:
                    result_json = '{"error": "Gagal download gambar"}'

            else:
                result_json = '{"error": "Tipe grading tidak valid"}'

            # Simpan Sukses
            results.append({
                "student_id": student_id,
                "status": "success",
                "result": result_json
            })
            print(f"✅ Selesai: {student_id}")

        except Exception as e:
            print(f"❌ Error {student_id}: {e}")
            results.append({
                "student_id": student_id,
                "status": "failed",
                "error": str(e)
            })

    return {
        "summary": {
            "mode": grading_type,
            "total": len(submissions),
            "processed": len(results)
        },
        "details": results
    }

def _download_image(url):
    """Helper untuk download gambar dari URL"""
    try:
        if not url: return None
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.content
    except Exception as e:
        print(f"Download Error: {e}")
    return None


def parse_input(text):
    if not text: return []
    # Hapus spasi, uppercase, split koma
    return [x.strip().upper() for x in str(text).split(',')]