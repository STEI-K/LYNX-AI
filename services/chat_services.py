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

# --- INIT FIREBASE (Singleton Pattern) ---
# Kode ini mencegah error "App already exists" saat auto-reload FastAPI
if not firebase_admin._apps:
    try:
        # Akan mencari environment variable GOOGLE_APPLICATION_CREDENTIALS secara otomatis
        # Pastikan Anda sudah setup credential di server/local
        firebase_admin.initialize_app()
        print("[INFO] Firebase Admin Initialized Successfully")
    except Exception as e:
        print(f"[WARNING] Gagal Init Firebase: {e}. Fitur Session Chat mungkin tidak berjalan.")

def _get_firestore_db():
    """Helper aman untuk mendapatkan client Firestore"""
    try:
        return firestore.client()
    except Exception as e:
        print(f"[ERROR] Firestore Client Error: {e}")
        return None

# --- MAIN SERVICE ---

def chat_service(
    question: str,
    session_id: Optional[str] = None,
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

    # --- FITUR 2: CHAT DENGAN SESSION ---
    # Jika session_id ada, kita load history dari Firebase
    db_history = []
    if session_id:
        print(f"[DEBUG] Fetching history for session: {session_id}")
        db_history = _fetch_history_from_firebase(session_id)
        
        # Jika DB kosong tapi user kirim history manual (fallback), pakai manual
        if not db_history and history: 
            db_history = history 

    # Gunakan db_history jika ada, kalau tidak pakai history dari parameter (untuk backward compatibility)
    final_history = db_history if session_id else (history or [])

    # --- FITUR 3: GENERAL CHAT ---
    print(f"[DEBUG] -> Masuk Jalur Chat Normal. Session: {session_id}")
    
    # Panggil Logic Chat
    response_data = _handle_text_chat(question, final_history, subject, file_url, file_base64, mime_type)
    
    # Simpan ke Firebase jika sukses dan session_id ada
    if session_id and response_data.get("type") == "text":
        _save_chat_pair_to_firebase(session_id, question, response_data["answer"])

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
                # Handle format history dari Firebase atau Frontend yang mungkin beda dikit
                content = h.get("content") or h.get("parts", [{}])[0].get("text", "")
                context_parts.append(f"{role.upper()}: {content}")

        prompt_content = [question]

        # Handle File Attachment
        if file_url:
            temp_file_path = _download_file(file_url)
        elif file_base64:
            temp_file_path = _save_base64_file(file_base64, mime_type)

        if temp_file_path:
            gemini_file = upload_file_to_gemini(temp_file_path, mime_type)
            prompt_content.insert(0, gemini_file)
            context_parts.append("[USER MELAMPIRKAN FILE]")

        full_prompt = "\n\n".join(context_parts)
        
        # Generate Content
        response = model.generate_content([full_prompt] + prompt_content)
        return {"answer": response.text, "type": "text"}

    except Exception as e:
        return {"answer": f"Error Chat: {str(e)}", "type": "error"}
    finally:
        # Cleanup temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

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

# --- HELPER FUNCTIONS (File IO) ---

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

# --- HELPER FUNCTIONS (Firebase) ---

def _fetch_history_from_firebase(session_id: str) -> List[Dict]:
    """Mengambil riwayat chat dari Firestore: chat_rooms/{session_id}/messages"""
    db = _get_firestore_db()
    if not db: return []
    
    try:
        # Struktur: Collection 'chat_rooms' -> Doc 'session_id' -> Subcollection 'messages'
        messages_ref = db.collection('chat_rooms').document(session_id).collection('messages')
        
        # Ambil 20 pesan terakhir agar konteks muat di Gemini
        docs = messages_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).limit_to_last(20).stream() 
        
        history = []
        for doc in docs:
            data = doc.to_dict()
            history.append({
                "role": data.get("role"),
                "content": data.get("content")
            })
        return history
    except Exception as e:
        print(f"[ERROR] Gagal fetch history Firebase: {e}")
        return []

def _save_chat_pair_to_firebase(session_id: str, question: str, answer: str):
    """Menyimpan pertanyaan user dan jawaban AI ke Firestore secara atomik"""
    db = _get_firestore_db()
    if not db: return
    
    try:
        doc_ref = db.collection('chat_rooms').document(session_id)
        messages_ref = doc_ref.collection('messages')
        
        batch = db.batch()
        
        # 1. Simpan User Message
        user_msg_ref = messages_ref.document() # Auto ID
        batch.set(user_msg_ref, {
            "role": "user",
            "content": question,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        # 2. Simpan Model Message
        model_msg_ref = messages_ref.document() # Auto ID
        batch.set(model_msg_ref, {
            "role": "model",
            "content": answer,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        # 3. Update 'last_updated' di Dokumen Room (agar bisa di-sort di frontend)
        # Set merge=True agar tidak menimpa field lain (misal title/user_id)
        batch.set(doc_ref, {"last_updated": firestore.SERVER_TIMESTAMP}, merge=True)
        
        batch.commit()
        print(f"[INFO] Chat saved to session {session_id}")
        
    except Exception as e:
        print(f"[ERROR] Gagal simpan chat ke Firebase: {e}")