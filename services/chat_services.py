# services/chat_services.py
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
        response_data = _handle_flashcard_generation(question)
        
        # Simpan Flashcard ke Firebase
        if session_id and response_data.get("type") != "error":
             _save_chat_pair_to_firebase(
                 session_id, user_id, question, 
                 answer="Flashcard Generated", # Judul akan ambil dari sini jika ini prompt pertama
                 response_type="flashcard",
                 response_data=response_data.get("data")
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
    
    # Simpan Text Chat ke Firebase
    if session_id and response_data.get("type") == "text":
        _save_chat_pair_to_firebase(
            session_id, user_id, question, 
            answer=response_data["answer"],
            response_type="text",
            file_url=file_url,   # [FIX] Kirim file_url ke fungsi save
            mime_type=mime_type  # [FIX] Kirim mime_type ke fungsi save
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
            # Pastikan mime_type dikirim ke Gemini agar dia tahu ini PDF atau Gambar
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
        docs = messages_ref.where('type', '==', 'text').order_by('timestamp', direction=firestore.Query.ASCENDING).limit_to_last(20).stream()
        
        history = []
        for doc in docs:
            data = doc.to_dict()
            history.append({"role": data.get("role"), "content": data.get("content")})
        return history
    except Exception as e:
        print(f"[ERROR] Fetch history: {e}")
        return []

def _generate_smart_title_from_answer(answer_text: str) -> str:
    """
    Mengambil intisari kalimat pertama dari jawaban AI sebagai judul.
    """
    try:
        # 1. Bersihkan Markdown
        clean = answer_text.replace('*', '').replace('#', '').replace('`', '').strip()
        # 2. Ambil kalimat pertama saja
        first_line = clean.split('\n')[0]
        # 3. Potong di tanda baca kalimat
        first_sentence = first_line.split('.')[0].strip()
        
        if len(first_sentence) < 3:
            return "Percakapan Baru"
            
        # 4. Batasi panjang maksimal 50 karakter agar muat di sidebar
        if len(first_sentence) > 50:
            return first_sentence[:47] + "..."
            
        # 5. Kapitalisasi huruf pertama
        return first_sentence[0].upper() + first_sentence[1:]
    except:
        return "Percakapan Baru"

def _save_chat_pair_to_firebase(session_id: str, user_id: str, question: str, answer: str, response_type: str = "text", response_data: Any = None, file_url: str = None, mime_type: str = None):
    """
    Menyimpan chat text maupun flashcard ke database.
    [CRITICAL FIX] Sekarang menyimpan image_url/file_url ke dokumen User agar preview tidak hilang.
    """
    db = _get_firestore_db()
    if not db: return
    
    try:
        doc_ref = db.collection('chat_rooms').document(session_id)
        doc_snap = doc_ref.get()
        batch = db.batch()
        
        # LOGIKA JUDUL
        current_data = doc_snap.to_dict() if doc_snap.exists else {}
        current_title = current_data.get("title")
        
        if not doc_snap.exists or current_title in ["Menulis judul...", "Percakapan Baru", None]:
            smart_title = _generate_smart_title_from_answer(answer)
            batch.set(doc_ref, {
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_updated": firestore.SERVER_TIMESTAMP,
                "title": smart_title,
                "user_id": user_id if user_id else "anonymous"
            }, merge=True)
        else:
            batch.set(doc_ref, {"last_updated": firestore.SERVER_TIMESTAMP}, merge=True)

        messages_ref = doc_ref.collection('messages')
        
        # --- Simpan User Message (DENGAN FILE DATA) ---
        user_msg_ref = messages_ref.document()
        
        user_payload = {
            "role": "user",
            "type": "text",
            "content": question,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        # [FIX] Simpan URL dan Mime Type agar frontend bisa merender ulang
        if file_url:
            user_payload["imageUrl"] = file_url
        if mime_type:
            user_payload["mimeType"] = mime_type

        batch.set(user_msg_ref, user_payload)
        
        # --- Simpan AI Message ---
        model_msg_ref = messages_ref.document()
        msg_data = {
            "role": "model",
            "type": response_type,
            "content": answer,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        if response_data:
            msg_data["data"] = response_data
            
        batch.set(model_msg_ref, msg_data)
        
        batch.commit()
        print(f"[INFO] Saved {response_type} to session {session_id} with file persistence.")
        
    except Exception as e:
        print(f"[ERROR] Save chat failed: {e}")