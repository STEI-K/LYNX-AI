import json
import firebase_admin
from firebase_admin import firestore
from services.gemini_client import get_text_model
from utils.prompt_loader import build_student_performance_prompt

def _get_db():
    try:
        return firestore.client()
    except:
        return None

def analysis_performace_service(student_id: str, student_name: str, grade_level: str):
    """
    Versi UPDATE: Otomatis tarik nilai dari Firebase 'submissions'.
    """
    db = _get_db()
    if not db:
        return {"error": "Database connection failed"}

    # 1. Tarik Data Nilai Siswa dari Firebase
    try:
        # Ambil semua submission milik siswa yang sudah dinilai ('graded')
        docs = db.collection('submissions')\
                 .where('student_id', '==', student_id)\
                 .where('status', '==', 'graded')\
                 .stream()

        # 2. Agregasi Nilai (Hitung Rata-rata per Mapel)
        subjects_map = {} # Format: {'mtk': [80, 90], 'fisika': [70]}
        
        for doc in docs:
            data = doc.to_dict()
            subj = data.get('subject_id', 'Umum') # Gunakan ID Mapel atau Nama
            score = data.get('score', 0)
            
            if subj not in subjects_map:
                subjects_map[subj] = []
            subjects_map[subj].append(score)
        
        if not subjects_map:
            return {"error": "Belum ada data nilai untuk siswa ini di database."}

        # Hitung Rata-rata
        final_scores = []
        for subj, val_list in subjects_map.items():
            avg = sum(val_list) / len(val_list)
            final_scores.append({
                "subject": subj,
                "score": round(avg, 2),
                "target": 75 # Bisa ditarik dari DB subjects jika mau lebih canggih
            })

    except Exception as e:
        return {"error": f"Gagal tarik data Firebase: {str(e)}"}

    # 3. Kirim ke AI
    print(f"[DEBUG] Analyzing for {student_name}: {final_scores}")
    prompt = build_student_performance_prompt(student_name, grade_level, final_scores)
    model = get_text_model()
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return {"error": f"AI Error: {str(e)}"}