import os
import json
import time
from services.gemini_client import get_text_model, upload_file_to_gemini
from utils.prompt_loader import build_generate_soal_prompt, build_document_summary_prompt

def generate_soal_service(subject, topic, difficulty, total, types, language):
    # Menggunakan prompt baru yang sudah ada poin penilaiannya
    prompt = build_generate_soal_prompt(
        subject, topic, difficulty, total, types, language
    )

    model = get_text_model()
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.7, "response_mime_type": "application/json"} 
        )
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return {"error": str(e)}

def generate_summary_service(file_path: str, mime_type: str):
    """
    Menerima path file lokal (hasil upload atau download URL),
    Upload ke Gemini, lalu minta ringkasan.
    """
    print(f"[DEBUG] Generating Summary for: {file_path} ({mime_type})")
    
    model = get_text_model()
    prompt = build_document_summary_prompt()
    
    try:
        # 1. Upload File ke Gemini
        gemini_file = upload_file_to_gemini(file_path, mime_type)
        
        # 2. Generate Content
        response = model.generate_content([prompt, gemini_file])
        
        return {
            "summary": response.text,
            "source_file": gemini_file.uri
        }
        
    except Exception as e:
        return {"error": f"Gagal meringkas dokumen: {str(e)}"}