from services.gemini_client import get_text_model

def tutor_service(question, subject, level, history):
    # Setup Prompt
    prompt = f"""
    Kamu adalah AI Tutor untuk pelajaran {subject}, level siswa {level}.

    Riwayat percakapan:
    {history}

    Pertanyaan siswa:
    {question}

    Berikan jawaban step-by-step, jelas, mudah dimengerti,
    dan tanyakan kembali apakah siswa paham.
    """

    # Panggil Model
    model = get_text_model()
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Maaf, terjadi kesalahan pada AI Tutor: {str(e)}"