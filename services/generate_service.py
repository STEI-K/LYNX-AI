import os
import json
import time
import uuid
from typing import List, Dict, Any
import cloudinary
import cloudinary.uploader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

from services.gemini_client import get_text_model, upload_file_to_gemini
from utils.prompt_loader import build_generate_soal_prompt, build_document_summary_prompt

# --- CONFIG CLOUDINARY ---
# Pastikan environment variables ini sudah diset di Railway/Local .env Anda
cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)

# --- CONFIG TEMP ---
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def generate_soal_service(subject, topic, difficulty, total, types, language):
    """
    Service utama untuk generate soal.
    Sekarang melakukan 3 hal sekaligus (Pipeline):
    1. Meminta AI membuat soal (JSON).
    2. Mengonversi JSON menjadi PDF (Soal & Rubrik).
    3. Mengupload PDF ke Cloudinary dan mengembalikan Link-nya.
    """
    # 1. GENERATE JSON VIA GEMINI
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
        soal_data = json.loads(clean_text)
        
        # 2. & 3. CONVERT TO PDF & UPLOAD TO CLOUDINARY
        # Kita panggil helper function di sini agar result langsung lengkap
        print(f"[INFO] Memulai generasi PDF & Upload untuk topik: {topic}")
        file_links = _generate_soal_json_to_pdf_to_cloudinary(soal_data)
        
        if "error" in file_links:
            # Jika upload gagal, jangan gagalkan seluruh request, tapi beri peringatan
            soal_data["file_error"] = file_links["error"]
        else:
            # Merge link ke dalam dictionary hasil
            soal_data["links"] = file_links
            
        return soal_data

    except Exception as e:
        return {"error": f"Critical Error di generate_soal_service: {str(e)}"}

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

# --- INTERNAL HELPERS (PDF & CLOUDINARY) ---

def _generate_soal_json_to_pdf_to_cloudinary(soal_data: dict, prefix: str = "doc") -> dict:
    """
    Mengubah data JSON soal menjadi 2 file PDF (Soal & Rubrik), 
    upload ke Cloudinary, dan mengembalikan URL-nya.
    """
    try:
        # 1. Generate Unique Filenames
        unique_id = str(uuid.uuid4())[:8]
        filename_soal = f"{prefix}_soal_{unique_id}.pdf"
        filename_rubric = f"{prefix}_rubrik_{unique_id}.pdf"
        
        path_soal = os.path.join(TEMP_DIR, filename_soal)
        path_rubric = os.path.join(TEMP_DIR, filename_rubric)
        
        # 2. Extract Data
        questions = soal_data.get("questions", [])
        summary = soal_data.get("summary", {})
        difficulty = summary.get("difficulty", "General")
        
        # 3. Create PDF Soal (Tanpa Kunci Jawaban)
        _create_pdf_document(
            filepath=path_soal,
            title=f"PAKET SOAL ({difficulty.upper()})",
            questions=questions,
            include_rubric=False
        )
        
        # 4. Create PDF Rubrik (Dengan Kunci & Skor)
        _create_pdf_document(
            filepath=path_rubric,
            title=f"KUNCI JAWABAN & RUBRIK ({difficulty.upper()})",
            questions=questions,
            include_rubric=True
        )
        
        # 5. Upload to Cloudinary
        print(f"[INFO] Uploading PDFs to Cloudinary: {unique_id}")
        res_soal = cloudinary.uploader.upload(path_soal, folder="lynx-ai/soal", resource_type="raw")
        res_rubric = cloudinary.uploader.upload(path_rubric, folder="lynx-ai/rubrik", resource_type="raw")
        
        # 6. Cleanup Temp Files
        if os.path.exists(path_soal): os.remove(path_soal)
        if os.path.exists(path_rubric): os.remove(path_rubric)
        
        return {
            "soal_pdf_url": res_soal.get("secure_url"),
            "rubric_pdf_url": res_rubric.get("secure_url")
        }

    except Exception as e:
        print(f"[ERROR] PDF/Cloudinary Failure: {e}")
        return {"error": str(e)}

def _create_pdf_document(filepath: str, title: str, questions: List[Dict], include_rubric: bool):
    """
    Helper function menggunakan ReportLab Platypus untuk membuat PDF rapi.
    Mendukung teks panjang (wrapping) dan format HTML sederhana.
    """
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle(
        'CustomTitle', 
        parent=styles['Heading1'], 
        alignment=TA_CENTER, 
        fontSize=18, 
        spaceAfter=20
    )
    style_q_num = ParagraphStyle(
        'QNumber',
        parent=styles['Heading3'], 
        fontSize=12,
        spaceBefore=10,
        spaceAfter=5
    )
    style_body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        leading=14, # Line spacing
        alignment=TA_JUSTIFY
    )
    style_box = ParagraphStyle(
        'Box',
        parent=styles['Code'],
        fontSize=10,
        backColor='#f0f0f0',
        borderColor='#333333',
        borderWidth=1,
        borderPadding=5,
        leading=12
    )

    story = []
    
    # 1. Header Title
    story.append(Paragraph(title, style_title))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Total Soal: {len(questions)}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # 2. Loop Questions
    for idx, q in enumerate(questions):
        no = q.get("no", idx + 1)
        q_text = q.get("question", "")
        q_type = q.get("type", "essay")
        score = q.get("score", 0)
        
        # Nomor Soal & Skor
        header_text = f"Soal {no}. ({q_type.upper()}) - Bobot: {score}"
        story.append(Paragraph(header_text, style_q_num))
        
        # Teks Pertanyaan
        story.append(Paragraph(q_text, style_body))
        story.append(Spacer(1, 10))
        
        # A. JIKA MODE SOAL (Untuk Siswa)
        if not include_rubric:
            if q_type == "pg":
                choices = q.get("choices", [])
                for i, choice in enumerate(choices):
                    # Pilihan A, B, C, D
                    label = chr(65 + i) # 0->A, 1->B
                    story.append(Paragraph(f"<b>{label}.</b> {choice}", style_body))
                story.append(Spacer(1, 15))
            else:
                # Space kosong untuk essay
                story.append(Paragraph("<i>Jawaban:</i>", style_body))
                story.append(Spacer(1, 50)) # Beri ruang kosong vertikal
                story.append(Paragraph("_" * 110, style_body)) # Garis bawah
                story.append(Spacer(1, 15))

        # B. JIKA MODE RUBRIK (Untuk Dosen)
        else:
            if q_type == "pg":
                # Tampilkan Jawaban Benar & Penjelasan
                ans_idx = q.get("answer", -1)
                
                # Konversi index angka ke huruf jika perlu, atau ambil string langsung
                if isinstance(ans_idx, int) and 0 <= ans_idx < 4:
                    ans_char = chr(65 + ans_idx)
                else:
                    ans_char = str(ans_idx)
                
                explanation = q.get("explanation", "Tidak ada penjelasan.")
                
                content = f"<b>Kunci Jawaban:</b> {ans_char}<br/><b>Penjelasan:</b> {explanation}"
                story.append(Paragraph(content, style_box))
            
            else: # Essay
                # Tampilkan Rubrik
                rubric_text = q.get("rubric", "Lihat rubrik standar.")
                story.append(Paragraph(f"<b>Rubrik Penilaian:</b><br/>{rubric_text}", style_box))
            
            story.append(Spacer(1, 15))

    # 3. Build PDF
    try:
        doc.build(story)
    except Exception as e:
        # Fallback jika error saat build PDF (misal font error)
        print(f"[ERROR] Failed building PDF: {e}")
        raise e