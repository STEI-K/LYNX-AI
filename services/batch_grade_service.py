import time
import json
import requests
import firebase_admin
from firebase_admin import firestore
from services.essay_service import grade_essay_service
from services.vision_essay_service import grade_essay_vision, extract_text_from_image, extract_text_from_pdf
from services.vision_pg_service import grade_pg_vision, feedback_pg_vision

# --- INIT FIREBASE ---
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app()
    except:
        pass

def _get_db():
    try:
        return firestore.client()
    except:
        return None

def process_batch_grading(submissions: list, grading_type: str = "essay", soal_url: str = None, rubric: str = None):
    """
    Memproses penilaian massal DAN menyimpan hasilnya ke database 'submissions'.
    """
    results = []
    db = _get_db()
    
    print(f"🚀 Memulai Batch Grading ({grading_type.upper()}) - Total: {len(submissions)}")
    
    for sub in submissions:
        # PENTING: Frontend harus kirim ID dokumen submission agar bisa di-update
        submission_doc_id = sub.get("submission_id") or sub.get("id")
        student_id = sub.get("student_id")
        
        result_json = "{}"
        score = 0
        feedback = ""
        
        try:
            # --- TIPE 1: ESSAY TEKS ---
            if grading_type == "essay":
                # if soal_url is a PDF use PDF extractor else use image extractor
                if soal_url and 'pdf' in str(soal_url).lower():
                    question = extract_text_from_pdf(_download_pdf(soal_url))
                else:
                    question = extract_text_from_image(_download_image(soal_url))
                rubric = sub.get("rubric")

                answer = sub.get("answer")
                max_score = sub.get("max_score", 100)
                
                result_raw = grade_essay_service(question, rubric, answer, max_score)
                # Parsing score untuk disimpan terpisah
                try:
                    parsed = json.loads(result_raw)
                    score = parsed.get("score", 0)
                    feedback = parsed.get("suggestions", "") or parsed.get("strengths", "")
                except:
                    pass
                result_json = result_raw
                time.sleep(1) 

            # --- TIPE 2: PG TEKS ---
            elif grading_type == "pg":
                if soal_url and 'pdf' in str(soal_url).lower():
                    question = extract_text_from_pdf(_download_pdf(soal_url))
                else:
                    question = extract_text_from_image(_download_image(soal_url))
                keys = parse_input(sub.get("rubric"))
                answers = parse_input(sub.get("answer"))
                max_score = sub.get("max_score", 100)
                
                total_soal = len(keys)
                if total_soal == 0:
                    score = 0
                    feedback = "Error: Kunci jawaban kosong."
                else:
                    correct_count = 0
                    wrong_details = []
                    for i, key in enumerate(keys):
                        student_ans = answers[i] if i < len(answers) else "-"
                        if student_ans == key:
                            correct_count += 1
                        else:
                            wrong_details.append(f"No {i+1}")
                    
                    score = (correct_count / total_soal) * max_score
                    score = round(score, 2)
                    
                    if len(wrong_details) == 0:
                        feedback = "Sempurna!"
                    else:
                        feedback = f"Salah {len(wrong_details)} soal."
                    feedback = feedback + "\n" + feedback_pg_vision(soal=question, jawaban_siswa=answers, key_list=keys)
                
                result_json = json.dumps({
                    "score": score, 
                    "feedback": feedback,
                    "correct_count": correct_count
                })

            # --- TIPE 3: VISION ESSAY ---
            elif grading_type == "vision_essay":
                image_url = sub.get("file_url")
                if soal_url and 'pdf' in str(soal_url).lower():
                    question = extract_text_from_pdf(_download_pdf(soal_url))
                else:
                    question = extract_text_from_image(_download_image(soal_url))
                keys = parse_input(sub.get("rubric"))
                answers = parse_input(sub.get("answer"))
                max_score = sub.get("max_score", 100)
                rubric = sub.get("rubric")
                max_score = sub.get("max_score", 100)
                
                img_bytes = _download_image(image_url)
                if img_bytes:
                    result_raw = grade_essay_vision(img_bytes, question, rubric, max_score)
                    try:
                        parsed = json.loads(result_raw)
                        score = parsed.get("score", 0)
                    except: pass
                    result_json = result_raw
                    time.sleep(1)
                else:
                    result_json = '{"error": "Gagal download gambar"}'

            # --- TIPE 4: VISION PG / LJK ---
            elif grading_type == "vision_pg":
                image_url = sub.get("file_url")
                if soal_url and 'pdf' in str(soal_url).lower():
                    question = extract_text_from_pdf(_download_pdf(soal_url))
                else:
                    question = extract_text_from_image(_download_image(soal_url))
                keys = parse_input(sub.get("rubric"))
                answers = parse_input(sub.get("answer"))
                max_score = sub.get("max_score", 100)
                key_list = sub.get("key_list", []) # List kunci jawaban
                img_bytes = _download_image(image_url)
                
                if img_bytes:
                    result_raw = grade_pg_vision(img_bytes, key_list, soal=question)
                    try:
                        parsed = json.loads(result_raw)
                        score = parsed.get("score", 0)
                        feedback = parsed.get("feedback", "")
                    except: pass
                    result_json = result_raw
                    time.sleep(1)
                else:
                    result_json = '{"error": "Gagal download gambar"}'

            else:
                result_json = '{"error": "Tipe grading tidak valid"}'

            # --- DATABASE UPDATE (CRUCIAL UPDATE) ---
            if db and submission_doc_id:
                # Update dokumen submissions di Firestore
                db.collection('submissions').document(submission_doc_id).update({
                    "score": score,
                    "feedback": feedback,
                    "status": "graded", # Tandai sudah dinilai
                    "grading_details": json.loads(result_json) if isinstance(result_json, str) else result_json,
                    "graded_at": firestore.SERVER_TIMESTAMP
                })
                print(f"💾 Database Updated: {submission_doc_id} -> Score: {score}")

            # Simpan Sukses ke Response
            results.append({
                "submission_id": submission_doc_id,
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
    try:
        if not url: return None
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.content
    except Exception as e:
        print(f"Download Error: {e}")
    return None

def _download_pdf(url):
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
    return [x.strip().upper() for x in str(text).split(',')]