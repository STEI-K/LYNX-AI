import json
import os
import base64
import textwrap
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from services.gemini_client import get_text_model
from utils.prompt_loader import build_flashcard_prompt

def generate_flashcards_service(topic: str):
    """
    Service khusus untuk generate flashcard dalam format JSON + PDF PPT Style.
    """
    print(f"[DEBUG] Generating Flashcards for: {topic}")
    
    # 1. Generate Content via AI
    prompt = build_flashcard_prompt(topic)
    model = get_text_model()
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # 2. Generate PDF (PPT Style)
        pdf_base64 = _create_flashcard_pdf(data.get("cards", []), topic)
        
        # 3. Gabungkan hasil
        data["pdf_base64"] = pdf_base64
        return data
        
    except json.JSONDecodeError:
        return {"error": "Gagal parsing JSON dari AI. Coba lagi."}
    except Exception as e:
        return {"error": f"System Error: {str(e)}"}

def _create_flashcard_pdf(cards, topic):
    """
    Membuat PDF Landscape (PPT Style).
    Halaman 1: Pertanyaan
    Halaman 2: Jawaban
    ... dst
    """
    buffer = BytesIO()
    # Ukuran Landscape A4 (mirip slide PPT)
    width, height = landscape(A4) 
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    
    c.setTitle(f"Flashcards - {topic}")
    
    for i, card in enumerate(cards):
        # --- HALAMAN DEPAN (PERTANYAAN) ---
        _draw_slide(c, width, height, card['front'], f"Card {i+1} - Question", is_question=True)
        c.showPage() # Pindah Halaman
        
        # --- HALAMAN BELAKANG (JAWABAN) ---
        _draw_slide(c, width, height, card['back'], f"Card {i+1} - Answer", is_question=False)
        c.showPage() # Pindah Halaman

    c.save()
    
    # Convert ke Base64 agar mudah dikirim via API
    pdf_bytes = buffer.getvalue()
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    buffer.close()
    return pdf_base64

def _draw_slide(c, width, height, text, footer_text, is_question):
    """Helper untuk menggambar satu slide/halaman"""
    
    # Background Color (Opsional: Sedikit abu-abu untuk Jawaban biar beda)
    if not is_question:
        c.setFillColorRGB(0.95, 0.95, 0.95) # Abu sangat muda
        c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Setup Font
    c.setFillColorRGB(0, 0, 0) # Teks Hitam
    font_name = "Helvetica-Bold" if is_question else "Helvetica"
    font_size = 28 if is_question else 24
    c.setFont(font_name, font_size)
    
    # Text Wrapping (Agar tidak keluar layar jika panjang)
    # Rata-rata A4 landscape muat sekitar 50-60 karakter per baris dengan font besar
    wrapped_text = textwrap.wrap(text, width=50) 
    
    # Hitung posisi tengah vertikal
    line_height = font_size * 1.5
    total_text_height = len(wrapped_text) * line_height
    current_y = (height / 2) + (total_text_height / 2) - line_height
    
    # Draw Text Centered
    for line in wrapped_text:
        c.drawCentredString(width / 2, current_y, line)
        current_y -= line_height
        
    # Footer (Nomor Halaman / Label)
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width / 2, 30, footer_text)