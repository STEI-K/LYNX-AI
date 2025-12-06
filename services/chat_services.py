import os
import requests
import uuid
import base64
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from services.gemini_client import (
    get_text_model, 
    upload_file_to_gemini,
    API_KEY as GEMINI_API_KEY
)
from services.flashcard_service import generate_flashcards_service
from utils.prompt_loader import build_chat_system_prompt
from utils.content_safety import is_safe_text

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def chat_service(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    subject: Optional[str] = None,
    file_url: Optional[str] = None,
    file_base64: Optional[str] = None,
    mime_type: Optional[str] = None
) -> Dict[str, Any]:
    
    # 1. Safety Check
    safe, reason = is_safe_text(question)
    if not safe:
        return {"answer": "Maaf, konten melanggar kebijakan safety.", "safety_reason": reason}

    lower_q = question.lower()
    
    # --- FITUR 1: FLASHCARD GENERATION ---
    flashcard_triggers = ["buatkan flashcard", "bikin flashcard", "generate flashcard", "kartu belajar"]
    if any(k in lower_q for k in flashcard_triggers):
        print("[DEBUG] -> Masuk Jalur Flashcard Generation")
        return _handle_flashcard_generation(question)

    # --- FITUR 4: GENERAL CHAT ---
    print("[DEBUG] -> Masuk Jalur Chat Normal")
    return _handle_text_chat(question, history, subject, file_url, file_base64, mime_type)


def _handle_text_chat(question, history, subject, file_url, file_base64, mime_type):
    temp_file_path = None
    try:
        model = get_text_model()
        
        system_instruction = build_chat_system_prompt()
        context_parts = [system_instruction]
        
        if subject: 
            context_parts.append(f"KONTEKS MATA KULIAH: {subject}")
            
        if history:
            context_parts.append("\n--- RIWAYAT CHAT ---")
            for h in history:
                role = "user" if h.get("role") == "user" else "model"
                context_parts.append(f"{role.upper()}: {h.get('content')}")

        prompt_content = [question]

        if file_url:
            temp_file_path = _download_file(file_url)
        elif file_base64:
            temp_file_path = _save_base64_file(file_base64, mime_type)

        if temp_file_path:
            gemini_file = upload_file_to_gemini(temp_file_path, mime_type)
            prompt_content.insert(0, gemini_file)
            context_parts.append("[USER MELAMPIRKAN FILE]")

        full_prompt = "\n\n".join(context_parts)
        response = model.generate_content([full_prompt] + prompt_content)
        return {"answer": response.text, "type": "text"}

    except Exception as e:
        return {"answer": f"Error Chat: {str(e)}", "type": "error"}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def _handle_flashcard_generation(prompt):
    """
    Handler khusus yang memanggil Service Flashcard.
    """
    try:
        # Bersihkan prompt agar tersisa topiknya saja
        clean_topic = prompt.lower().replace("buatkan flashcard", "").replace("tentang", "").strip()
        if not clean_topic: clean_topic = "Topik Umum"
        
        # PANGGIL SERVICE (KOKI) DISINI
        flashcard_data = generate_flashcards_service(clean_topic)
        
        if "error" in flashcard_data:
            return {"answer": f"Gagal: {flashcard_data['error']}", "type": "error"}

        return {
            "answer": f"Flashcard topik '{clean_topic}' siap! Saya juga menyertakan file PDF siap cetak.",
            "type": "flashcard",
            "data": {
                "topic": flashcard_data.get("topic"),
                "cards": flashcard_data.get("cards"),
                "pdf_base64": flashcard_data.get("pdf_base64")
            }
        }
    except Exception as e:
        return {"answer": f"Error Flashcard Handler: {str(e)}", "type": "error"}

def _download_file(url: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, stream=True, timeout=15, headers=headers)
    filename = f"{uuid.uuid4()}.tmp"
    filepath = os.path.join(TEMP_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(response.content)
    return filepath

def _save_base64_file(base64_string: str, mime_type: str = None) -> str:
    if "," in base64_string: base64_string = base64_string.split(",")[1]
    file_data = base64.b64decode(base64_string)
    ext = ".bin"
    if mime_type:
        if "pdf" in mime_type: ext = ".pdf"
        elif "image" in mime_type: ext = ".jpg"
    filepath = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{ext}")
    with open(filepath, "wb") as f:
        f.write(file_data)
    return filepath