import os
import time
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from services.gemini_client import (
    get_text_model, 
    get_image_generation_model, 
    get_video_generation_model,
    upload_file_to_gemini
)
from utils.prompt_loader import build_deep_tutor_system_prompt
from utils.content_safety import is_safe_text

def deep_tutor_service(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    subject: Optional[str] = None,
    student_level: Optional[str] = None,
    file_path: Optional[str] = None,
    mime_type: Optional[str] = None
) -> Dict[str, Any]:
    
    # 1. Safety Check
    safe, reason = is_safe_text(question)
    if not safe:
        return {"answer": "Maaf, konten terdeteksi melanggar kebijakan.", "safety_reason": reason}

    # --- INTENT DETECTION (Router Pintar) ---
    lower_q = question.lower()
    
    # A. FITUR GENERATE IMAGE
    if "buatkan gambar" in lower_q or "generate image" in lower_q:
        return _handle_image_generation(question)

    # B. FITUR GENERATE VIDEO
    if "buatkan video" in lower_q or "generate video" in lower_q:
        return _handle_video_generation(question)

    # C. FITUR CHAT NORMAL (Teks / Analisis File)
    return _handle_text_chat(question, history, subject, student_level, file_path, mime_type)


def _handle_image_generation(prompt):
    """Menangani permintaan pembuatan gambar"""
    try:
        model = get_image_generation_model()
        response = model.generate_content(prompt)
        
        # Ambil gambar dari respon
        if response.parts:
            for part in response.parts:
                if part.inline_data:
                    # Gambar dikembalikan sebagai base64 raw data
                    # Frontend tinggal render: <img src="data:image/jpeg;base64,...">
                    import base64
                    b64_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                    return {
                        "answer": "Berikut gambar yang kamu minta!",
                        "image_base64": b64_data,
                        "type": "image_generation"
                    }
        return {"answer": "Gagal membuat gambar. AI tidak mengembalikan data visual."}
    except Exception as e:
        return {"answer": f"Error Image Generation: {str(e)}"}


def _handle_video_generation(prompt):
    """Menangani permintaan pembuatan video (Veo)"""
    try:
        model = get_video_generation_model()
        # Veo butuh waktu, jadi kita return status processing
        # Note: Ini versi simplifikasi. Idealnya pakai async polling.
        operation = model.generate_videos(prompt=prompt)
        
        # Tunggu sebentar (Polling sederhana)
        print("⏳ Generating video (Veo)...")
        time.sleep(5) 
        
        return {
            "answer": "Permintaan video sedang diproses oleh Veo 3.1. Fitur ini membutuhkan waktu render.",
            "status": "processing",
            "note": "Video generation via API biasanya butuh polling operation ID."
        }
    except Exception as e:
        return {"answer": f"Error Video Generation: {str(e)}"}


def _handle_text_chat(question, history, subject, student_level, file_path, mime_type):
    """Chat Tutor Standard + Analisis File"""
    try:
        model = get_text_model()
        
        # Siapkan Prompt System
        system_instruction = build_deep_tutor_system_prompt()
        context_parts = [system_instruction]

        if subject: context_parts.append(f"MATA KULIAH: {subject}")
        if student_level: context_parts.append(f"LEVEL: {student_level}")

        # Masukkan History
        if history:
            context_parts.append("\n--- RIWAYAT ---")
            for h in history:
                role = "user" if h.get("role") == "user" else "model"
                context_parts.append(f"{role.upper()}: {h.get('content')}")

        # Masukkan File (Jika ada upload)
        prompt_content = [question]
        if file_path:
            # Upload file ke Gemini
            gemini_file = upload_file_to_gemini(file_path, mime_type)
            prompt_content.insert(0, gemini_file)
            context_parts.append("\n[USER MENGUPLOAD FILE UNTUK DIANALISIS]")

        # Gabung System Prompt
        full_system_prompt = "\n\n".join(context_parts)
        
        # Kirim ke AI (System Prompt + User Content)
        response = model.generate_content([full_system_prompt] + prompt_content)
        
        return {"answer": response.text, "type": "text"}

    except Exception as e:
        return {"answer": "Terjadi kesalahan sistem.", "debug": str(e)}