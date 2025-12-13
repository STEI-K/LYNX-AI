import cv2
import numpy as np
import json

def grade_pg_vision(image_bytes: bytes, key_list: list = None):
    """
    Grading LJK dengan pendekatan 'Aggressive Header Cropping'.
    Sistem akan mencari blok konten besar di bagian atas (Header/Nama)
    dan membuangnya sebelum mencoba mendeteksi jawaban.
    """ 
    # 1. Decode Image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        return json.dumps({"error": "Gagal decode gambar."})

    try:
        # 2. Resize Lebar ke 1600px (Standar Presisi)
        # Kita butuh resolusi fix agar filter ukuran bubble (pixel) valid.
        target_w = 1600
        h, w = image.shape[:2]
        scale = target_w / w
        resized = cv2.resize(image, (target_w, int(h * scale)))
        
        # 3. HEADER REMOVAL (Potong Area Atas)
        roi_bubbles = crop_header_aggressive(resized)
        
        # 4. Scan Bubbles pada area bersih
        detected_answers = process_bubbles_grid(roi_bubbles)
        
        # 5. Grading
        score_data = calculate_score(detected_answers, key_list)
        return json.dumps(score_data)

    except Exception as e:
        return json.dumps({
            "error": f"Gagal Memproses LJK: {str(e)}",
            "hint": "Pastikan foto menampilkan seluruh lembar jawaban dengan pencahayaan cukup."
        })
    
def get_rubric_vision(image_bytes: bytes):
    """
    Ekstrak rubrik soal dari gambar (misal: LJK yang berisi rubrik).
    """
    # 1. Decode Image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        return json.dumps({"error": "Gagal decode gambar."})

    try:
        # 2. Resize Lebar ke 1600px (Standar Presisi)
        # Kita butuh resolusi fix agar filter ukuran bubble (pixel) valid.
        target_w = 1600
        h, w = image.shape[:2]
        scale = target_w / w
        resized = cv2.resize(image, (target_w, int(h * scale)))
        
        # 3. HEADER REMOVAL (Potong Area Atas)
        roi_bubbles = crop_header_aggressive(resized)
        
        # 4. Scan Bubbles pada area bersih
        detected_answers = process_bubbles_grid(roi_bubbles)
        return json.dumps({
            "answers": detected_answers
        })
    except Exception as e:
        return json.dumps({
            "error": f"Gagal Memproses LJK: {str(e)}",
            "hint": "Pastikan foto menampilkan seluruh lembar jawaban dengan pencahayaan cukup."
        })

def crop_header_aggressive(image):
    """
    Mencari elemen grafis dominan (kotak/teks tebal) di 35% area atas gambar,
    lalu memotong gambar di bawah elemen tersebut.
    Jika gagal deteksi, lakukan crop manual (blind crop) 20%.
    """
    img_h, img_w = image.shape[:2]
    
    # Ambil 35% bagian atas saja untuk dianalisa
    top_part_limit = int(img_h * 0.35)
    top_part = image[0:top_part_limit, :]
    
    gray = cv2.cvtColor(top_part, cv2.COLOR_BGR2GRAY)
    
    # Threshold & Dilasi Horizontal
    # Tujuannya menyatukan teks/garis kotak menjadi satu blok besar ("Blob")
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 3)) # Melebar horizontal
    dilated = cv2.dilate(thresh, kernel, iterations=2)
    
    cnts, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    max_y = 0
    found_something = False
    
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        
        # Filter: Hanya anggap "Header" jika ukurannya lumayan lebar (>30% lebar gambar)
        if w > (img_w * 0.3):
            # Simpan koordinat Y terbawah dari contour ini
            if (y + h) > max_y:
                max_y = y + h
            found_something = True

    # Tentukan titik potong
    if found_something and max_y > 50:
        # Tambah margin 30px ke bawah biar aman
        crop_y = max_y + 30
    else:
        # Fallback: Jika tidak nemu kotak jelas, potong paksa 20% atas
        crop_y = int(img_h * 0.20)
        
    # Validasi agar tidak motong sampai habis
    if crop_y >= (img_h * 0.8):
        crop_y = 0 # Batal crop kalau motongnya kejauhan (error safety)

    return image[crop_y:, :]

def process_bubbles_grid(image):
    """
    Mencari bubble dengan filter bentuk ketat, lalu mengelompokkannya
    berdasarkan kolom (X) dan baris (Y).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Adaptive Threshold (Tahan bayangan)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY_INV, 51, 15)

    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bubble_candidates = []
    
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        
        # FILTER KUNCI: Bubble LJK itu KECIL dan BULAT/KOTAK.
        # Kotak Registrasi (Header) pasti gagal di sini karena ukurannya besar atau AR-nya gepeng.
        # Pada lebar gambar 1600px, bubble biasanya 30-70px.
        if w >= 25 and h >= 25 and w <= 80 and h <= 80 and 0.75 <= ar <= 1.25:
            bubble_candidates.append(c)

    if not bubble_candidates:
        raise ValueError("Tidak ada bubble jawaban terdeteksi setelah crop.")

    # --- CLUSTERING KOLOM (Memisahkan Kolom 1, 2, 3) ---
    # 1. Sort berdasarkan X
    bubble_candidates = sorted(bubble_candidates, key=lambda c: cv2.boundingRect(c)[0])
    
    columns = []
    current_col = [bubble_candidates[0]]
    
    for i in range(1, len(bubble_candidates)):
        prev_x = cv2.boundingRect(current_col[-1])[0]
        curr_x = cv2.boundingRect(bubble_candidates[i])[0]
        
        # Gap besar horizontal (>150px) artinya pindah kolom soal
        if (curr_x - prev_x) > 120: 
            columns.append(current_col)
            current_col = []
        
        current_col.append(bubble_candidates[i])
    columns.append(current_col)
    
    final_answers = []
    
    # --- PROCESSING PER KOLOM ---
    for col in columns:
        # 2. Sort Vertical dalam satu kolom
        col = sorted(col, key=lambda c: cv2.boundingRect(c)[1])
        
        # 3. Clustering Baris (Row)
        rows = []
        curr_row = [col[0]]
        
        for i in range(1, len(col)):
            prev_y = cv2.boundingRect(curr_row[-1])[1]
            curr_y = cv2.boundingRect(col[i])[1]
            
            # Gap kecil vertical (<30px) artinya satu baris
            if abs(curr_y - prev_y) < 30:
                curr_row.append(col[i])
            else:
                rows.append(curr_row)
                curr_row = [col[i]]
        rows.append(curr_row)
        
        # 4. Baca Jawaban per Baris
        for row in rows:
            # Sort Kiri-Kanan (A,B,C,D,E)
            row = sorted(row, key=lambda c: cv2.boundingRect(c)[0])
            
            # Validasi jumlah opsi (misal 5 opsi A-E)
            # Jika noise masuk, biasanya jumlahnya aneh (1 atau 2). Kita skip.
            if len(row) >= 4: # Toleransi jika 1 bubble tidak terdeteksi
                bubble_vals = []
                for bubble in row:
                    mask = np.zeros(thresh.shape, dtype="uint8")
                    cv2.drawContours(mask, [bubble], -1, 255, -1)
                    mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                    total = cv2.countNonZero(mask)
                    bubble_vals.append(total)
                
                max_val = max(bubble_vals)
                max_idx = bubble_vals.index(max_val)
                
                # Threshold Hitam (relatif pixel count)
                if max_val < 450: 
                    final_answers.append("") # Kosong
                else:
                    map_ans = {0:"A", 1:"B", 2:"C", 3:"D", 4:"E"}
                    final_answers.append(map_ans.get(max_idx, ""))

    return final_answers

def calculate_score(student_answers, key_list):
    if not key_list:
        return {"answers": student_answers, "info": "Scan Only Mode"}
    
    correct_count = 0
    details = []
    wrong_numbers = [] # List untuk menampung nomor yang salah
    idx_to_char = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}
    
    # Loop aman
    loop_len = min(len(student_answers), len(key_list))
    
    for i in range(loop_len):
        key_raw = key_list[i]
        key_char = idx_to_char.get(int(key_raw), "?") if str(key_raw).isdigit() else str(key_raw)
        
        student_ans = student_answers[i]
        is_correct = (student_ans == key_char)
        if is_correct: 
            correct_count += 1
        else:
            # Catat nomor yang salah
            wrong_numbers.append(str(i + 1))
            
        details.append({
            "no": i + 1, "student_ans": student_ans, "key": key_char, 
            "status": "Correct" if is_correct else "Wrong"
        })
        
    score = (correct_count / len(key_list) * 100) if key_list else 0
    
    # Generate Feedback String
    if len(wrong_numbers) == 0:
        feedback = "Sempurna! Semua jawaban benar."
    else:
        # Jika salah banyak, mungkin dipotong biar tidak kepanjangan
        limit_display = 10
        if len(wrong_numbers) > limit_display:
            shown = ", ".join(wrong_numbers[:limit_display])
            feedback = f"Salah {len(wrong_numbers)} soal (No: {shown}, ...)"
        else:
            feedback = f"Salah {len(wrong_numbers)} soal (No: {', '.join(wrong_numbers)})."

    return {
        "score": round(score, 2),
        "max_score": 100,
        "correct_count": correct_count,
        "total_questions": len(key_list),
        "answers": student_answers,
        "details": details,
        "feedback": feedback
    }