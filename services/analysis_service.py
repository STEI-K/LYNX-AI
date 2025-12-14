import json
import firebase_admin
from firebase_admin import firestore
from services.gemini_client import get_text_model
from utils.prompt_loader import give_link_recommend

# Helper untuk koneksi DB (Singleton-like)
def _get_db():
    try:
        return firestore.client()
    except:
        return None

def analysis_performace_service(student_id: str, student_name: str, grade_level: str):
    """
    LOGIC BARU: Otomatis tarik nilai dari Firebase 'submissions' milik siswa.
    """
    db = _get_db()
    if not db:
        return {"error": "Gagal koneksi ke Database. Cek config Firebase."}

    # 1. Tarik Data Nilai Siswa dari Firebase
    try:
        # Ambil semua submission milik siswa yang sudah dinilai ('graded')
        docs = db.collection('submissions')\
                 .where('student_id', '==', student_id)\
                 .where('status', '==', 'graded')\
                 .stream()

        # 2. Agregasi Nilai (Hitung Rata-rata per Mapel)
        subjects_map = {} # Format: {'mtk': [80, 90], 'fisika': [70]}
        
        found_data = False
        for doc in docs:
            found_data = True
            data = doc.to_dict()
            # Gunakan subject_id sebagai kunci, atau subject_name jika ada
            subj = data.get('subject_id') or data.get('subject', 'Umum') 
            score = data.get('score', 0)
            
            if subj not in subjects_map:
                subjects_map[subj] = []
            subjects_map[subj].append(float(score))
        
        if not found_data:
            return {"error": f"Belum ada data nilai 'graded' untuk siswa ID: {student_id}"}

        # Hitung Rata-rata Akhir
        final_scores = []
        for subj, val_list in subjects_map.items():
            avg = sum(val_list) / len(val_list)
            final_scores.append({
                "subject": subj,
                "score": round(avg, 2),
                "target": 75 # Default KKM/Target
            })

    except Exception as e:
        return {"error": f"Error saat menarik data Firebase: {str(e)}"}

    # 3. Kirim Data Agregat ke AI
    print(f"[DEBUG] Analyzing Performance for {student_name}: {final_scores}")
    prompt = give_link_recommend(student_name, grade_level, final_scores)
    model = get_text_model()
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return {"error": f"AI Generation Error: {str(e)}"}