import os
import time
import requests
import uuid
import base64
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from services.gemini_client import (
    get_text_model, 
    upload_file_to_gemini
)
from utils.prompt_loader import build_deep_tutor_system_prompt
from utils.content_safety import is_safe_text

# Konfigurasi Folder Temp
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def deep_tutor_service(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    subject: Optional[str] = None,
    student_level: Optional[str] = None,
    file_url: Optional[str] = None,
    file_base64: Optional[str] = None,
    mime_type: Optional[str] = None
) -> Dict[str, Any]:
    
    # 0. Debug Log
    print(f"\n[DEBUG] Pertanyaan Masuk: {question}")
    
    # 1. Safety Check
    safe, reason = is_safe_text(question)
    if not safe:
        return {"answer": "Maaf, konten terdeteksi melanggar kebijakan.", "safety_reason": reason}

    # 2. Intent Detection
    lower_q = question.lower()
    
    img_triggers = ["buatkan gambar", "bikin gambar", "generate image", "create image", "gambar dari", "lukiskan"]
    if any(k in lower_q for k in img_triggers):
        print("[DEBUG] -> Masuk Jalur Image Generation (POLLINATIONS BYPASS)")
        return _handle_image_generation_hackathon(question)

    vid_triggers = ["buatkan video", "bikin video", "generate video", "create video"]
    if any(k in lower_q for k in vid_triggers):
        print("[DEBUG] -> Masuk Jalur Video Generation (REST API)")
        return _handle_video_generation_rest(question)

    # 3. Chat Normal
    print("[DEBUG] -> Masuk Jalur Chat/Tutor Normal")
    return _handle_text_chat_multimodal(
        question, history, subject, student_level, file_url, file_base64, mime_type
    )

def _handle_text_chat_multimodal(question, history, subject, student_level, file_url, file_base64, mime_type):
    temp_file_path = None
    
    try:
        model = get_text_model()
        
        # Setup Prompt System
        system_instruction = build_deep_tutor_system_prompt()
        context_parts = [system_instruction]
        if subject: context_parts.append(f"MATA KULIAH: {subject}")
        if student_level: context_parts.append(f"LEVEL: {student_level}")
        if history:
            context_parts.append("\n--- RIWAYAT ---")
            for h in history:
                role = "user" if h.get("role") == "user" else "model"
                context_parts.append(f"{role.upper()}: {h.get('content')}")

        prompt_content = [question]

        # Handling File
        if file_url:
            print(f"[DEBUG] Downloading URL: {file_url}")
            temp_file_path = _download_file(file_url)
        elif file_base64:
            print(f"[DEBUG] Decoding Base64 File...")
            temp_file_path = _save_base64_file(file_base64, mime_type)

        if temp_file_path:
            gemini_file = upload_file_to_gemini(temp_file_path, mime_type)
            prompt_content.insert(0, gemini_file)
            context_parts.append("\n[USER MELAMPIRKAN FILE]")

        # Generate
        full_system_prompt = "\n\n".join(context_parts)
        response = model.generate_content([full_system_prompt] + prompt_content)
        return {"answer": response.text, "type": "text"}

    except Exception as e:
        error_msg = f"ERROR SYSTEM: {str(e)}"
        print(f"❌ {error_msg}")
        return {"answer": error_msg, "debug": str(e)}
        
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try: os.remove(temp_file_path)
            except: pass

def _download_file(url: str) -> str:
    try:
        # User-Agent palsu agar tidak diblokir server (Error 403 Fix)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, stream=True, timeout=15, headers=headers)
        response.raise_for_status()
        
        ext = ".tmp"
        if "." in url.split("/")[-1]:
            possible_ext = "." + url.split("/")[-1].split("?")[0].split(".")[-1]
            if len(possible_ext) < 6:
                ext = possible_ext
            
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(TEMP_DIR, filename)
        
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filepath
    except Exception as e:
        raise RuntimeError(f"Gagal download file: {str(e)}")

def _save_base64_file(base64_string: str, mime_type: str = None) -> str:
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        file_data = base64.b64decode(base64_string)
        ext = ".bin"
        if mime_type:
            if "pdf" in mime_type: ext = ".pdf"
            elif "image" in mime_type: ext = ".jpg"
            elif "text" in mime_type: ext = ".txt"
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(TEMP_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(file_data)
        return filepath
    except Exception as e:
        raise RuntimeError(f"Gagal decode Base64: {str(e)}")

# --- HACKATHON BYPASS GENERATORS ---

def _handle_image_generation_hackathon(prompt):
    """
    Generate Image menggunakan Pollinations.ai (FREE, NO KEY).
    Sangat cocok untuk Hackathon karena cepat dan unlimited.
    """
    try:
        # Bersihkan prompt agar URL safe
        clean_prompt = prompt.replace("buatkan gambar", "").replace("generate image", "").strip()
        
        # URL Magic (Model Flux/SDXL otomatis)
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=768&nologo=true&model=flux"
        
        # Download hasil gambar
        response = requests.get(url, timeout=20)
        
        if response.status_code == 200:
            # Convert to Base64 untuk dikirim ke frontend
            b64_image = base64.b64encode(response.content).decode('utf-8')
            return {
                "answer": "Berikut gambar yang kamu minta (Generated by LYNX Vision):",
                "image_base64": b64_image,
                "type": "image_generation",
                "source": "Pollinations.ai"
            }
        else:
            return {"answer": f"Gagal generate gambar. Server merespon: {response.status_code}"}
            
    except Exception as e:
        return {"answer": f"Error Image Gen: {str(e)}"}

def _handle_video_generation_rest(prompt):
    """
    Generate Video menggunakan Veo.
    Jika gagal (karena akun gratis), akan memberikan pesan simulasi yang elegan.
    """
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview:predictLongRunning?key={GEMINI_API_KEY}"
        
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"aspectRatio": "16:9"}
        }
        
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if response.status_code != 200:
            # Fallback Elegan untuk Hackathon
            return {
                "answer": "⚠️ Fitur Video Generation (Veo) memerlukan akses Enterprise/Billing aktif. \n"
                          "Namun, sistem mengenali permintaan Anda. Dalam mode Production, video akan muncul di sini.",
                "status": "simulation_mode",
                "error_detail": response.text
            }
            
        return {
            "answer": "Permintaan video sedang diproses oleh Veo 3.1. Mohon tunggu.",
            "status": "processing_veo"
        }
        
    except Exception as e:
        return {"answer": f"Error Video Gen: {str(e)}"}