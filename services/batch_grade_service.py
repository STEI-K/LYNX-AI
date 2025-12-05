import time
import json
import requests
from services.essay_service import grade_essay_service
from services.vision_essay_service import grade_essay_vision
from services.vision_pg_service import grade_pg_vision

def process_batch_grading(submissions: list, grading_type: str = "essay"):
    """
    Memproses penilaian massal untuk berbagai tipe soal.
    
    Args:
        submissions (list): List jawaban siswa.
        grading_type (str): 'essay', 'pg', 'vision_essay', 'vision_pg'
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
                time.sleep(1) # Safety delay for AI

            # --- TIPE 2: PG TEKS (Pakai Logic - Cepat) ---
            elif grading_type == "pg":
                key = str(sub.get("rubric")).strip().upper() # Kunci Jawaban
                answer = str(sub.get("answer")).strip().upper() # Jawaban Siswa
                max_score = sub.get("max_score", 100)
                
                if answer == key:
                    score = max_score
                    feedback = "Jawaban Tepat."
                else:
                    score = 0
                    feedback = f"Salah. Kunci: {key}"
                
                result_json = json.dumps({
                    "score": score, 
                    "max_score": max_score, 
                    "feedback": feedback
                })

            # --- TIPE 3: VISION ESSAY (Gambar -> AI) ---
            elif grading_type == "vision_essay":
                image_url = sub.get("file_url")
                question = sub.get("question")
                rubric = sub.get("rubric")
                max_score = sub.get("max_score", 100)
                
                # 1. Download Gambar
                img_bytes = _download_image(image_url)
                
                # 2. Kirim ke Vision AI
                if img_bytes:
                    result_json = grade_essay_vision(img_bytes, question, rubric, max_score)
                    time.sleep(1)
                else:
                    result_json = '{"error": "Gagal download gambar"}'

            # --- TIPE 4: VISION PG / LJK (Gambar -> AI) ---
            elif grading_type == "vision_pg":
                image_url = sub.get("file_url")
                # Key list harus berupa array angka [0, 2, 4...]
                key_list = sub.get("key_list", []) 
                
                img_bytes = _download_image(image_url)
                
                if img_bytes:
                    result_json = grade_pg_vision(img_bytes, key_list)
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