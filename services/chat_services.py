import os
import requests
import uuid
import base64
import json
import time
from typing import List, Dict, Any, Optional

import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore

from services.gemini_client import (
    get_text_model, 
    upload_file_to_gemini,
    API_KEY as GEMINI_API_KEY
)
from services.flashcard_service import generate_flashcards_service
from utils.prompt_loader import build_chat_system_prompt
from utils.content_safety import is_safe_text

# --- SETUP TEMP FOLDER ---
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# --- INIT FIREBASE (Singleton) ---
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app()
        print("[INFO] Firebase Admin Initialized Successfully")
    except Exception as e:
        print(f"[WARNING] Gagal Init Firebase: {e}. Session Chat mungkin error.")

def _get_firestore_db():
    try:
        return firestore.client()
    except Exception as e:
        print(f"[ERROR] Firestore Client Error: {e}")
        return None

# --- MAIN SERVICE ---

def chat_service(
    question: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
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
        # Panggil handler flashcard
        response_data = _handle_flashcard_generation(question)
        
        # [UPDATE] Simpan Flashcard ke Firebase jika session ada
        if session_id and response_data.get("type") != "error":
             _save_chat_pair_to_firebase(
                 session_id, user_id, question, 
                 answer="[Flashcard Generated]", # Fallback text
                 response_type="flashcard",
                 response_data=response_data.get("data") # Simpan JSON datanya
             )
        return response_data

    # --- FITUR 2: PREPARE HISTORY ---
    db_history = []
    if session_id:
        db_history = _fetch_history_from_firebase(session_id)
        if not db_history and history: 
            db_history = history 

    final_history = db_history if session_id else (history or [])

    # --- FITUR 3: GENERAL CHAT ---
    print(f"[DEBUG] -> Masuk Jalur Chat Normal. Session: {session_id}")
    
    response_data = _handle_text_chat(question, final_history, subject, file_url, file_base64, mime_type)
    
    # [UPDATE] Simpan Text Chat ke Firebase
    if session_id and response_data.get("type") == "text":
        _save_chat_pair_to_firebase(
            session_id, user_id, question, 
            answer=response_data["answer"],
            response_type="text"
        )

    return response_data


def _handle_text_chat(question, history, subject, file_url, file_base64, mime_type):
    temp_file_path = None
    try:
        model = get_text_model()
        
        system_instruction = build_chat_system_prompt()
        context_parts = [system_instruction]
        
        if subject: 
            context_parts.append(f"KONTEKS MATA KULIAH: {subject}")
            
        if history:
            context_parts.append("\n--- RIWAYAT CHAT SEBELUMNYA ---")
            for h in history:
                role = "user" if h.get("role") == "user" else "model"
                content = h.get("content") or ""
                context_parts.append(f"{role.upper()}: {content}")

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
            try: os.remove(temp_file_path)
            except: pass

def _handle_flashcard_generation(prompt):
    try:
        clean_topic = prompt.lower().replace("buatkan flashcard", "").replace("tentang", "").strip()
        if not clean_topic: clean_topic = "Topik Umum"
        
        flashcard_data = generate_flashcards_service(clean_topic)
        
        if "error" in flashcard_data:
            return {"answer": f"Gagal: {flashcard_data['error']}", "type": "error"}

        return {
            "answer": f"Flashcard topik '{clean_topic}' siap!",
            "type": "flashcard",
            "data": {
                "topic": flashcard_data.get("topic"),
                "cards": flashcard_data.get("cards"),
                "pdf_base64": flashcard_data.get("pdf_base64")
            }
        }
    except Exception as e:
        return {"answer": f"Error Flashcard Handler: {str(e)}", "type": "error"}

# --- HELPER FILE IO ---
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

# --- FIREBASE HELPERS (UPDATED) ---

def _fetch_history_from_firebase(session_id: str) -> List[Dict]:
    db = _get_firestore_db()
    if not db: return []
    try:
        messages_ref = db.collection('chat_rooms').document(session_id).collection('messages')
        # Filter hanya pesan text agar tidak membingungkan Gemini dengan JSON flashcard
        docs = messages_ref.where('type', '==', 'text').order_by('timestamp', direction=firestore.Query.ASCENDING).limit_to_last(20).stream()
        
        history = []
        for doc in docs:
            data = doc.to_dict()
            history.append({"role": data.get("role"), "content": data.get("content")})
        return history
    except Exception as e:
        print(f"[ERROR] Fetch history: {e}")
        return []

def _save_chat_pair_to_firebase(session_id: str, user_id: str, question: str, answer: str, response_type: str = "text", response_data: Any = None):
    """
    Menyimpan chat text maupun flashcard ke database.
    """
    db = _get_firestore_db()
    if not db: return
    
    try:
        doc_ref = db.collection('chat_rooms').document(session_id)
        
        # 1. Cek & Create Room
        doc_snap = doc_ref.get()
        batch = db.batch()
        
        if not doc_snap.exists:
            auto_title = (question[:50] + '...') if len(question) > 50 else question
            batch.set(doc_ref, {
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_updated": firestore.SERVER_TIMESTAMP,
                "title": auto_title,
                "user_id": user_id if user_id else "anonymous"
            })
        else:
            batch.set(doc_ref, {"last_updated": firestore.SERVER_TIMESTAMP}, merge=True)

        messages_ref = doc_ref.collection('messages')
        
        # 2. Simpan User Message
        user_msg_ref = messages_ref.document()
        batch.set(user_msg_ref, {
            "role": "user",
            "type": "text",
            "content": question,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        # 3. Simpan AI Message (Bisa Text atau Flashcard)
        model_msg_ref = messages_ref.document()
        msg_data = {
            "role": "model",
            "type": response_type, # 'text' atau 'flashcard'
            "content": answer,     # Teks fallback untuk ditampilkan sekilas
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        # Jika ada data tambahan (misal JSON flashcard), simpan juga
        if response_data:
            msg_data["data"] = response_data
            
        batch.set(model_msg_ref, msg_data)
        
        batch.commit()
        print(f"[INFO] Saved {response_type} to session {session_id}")
        
    except Exception as e:
        print(f"[ERROR] Save chat failed: {e}")