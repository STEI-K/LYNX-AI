from services.gemini_client import client

def tutor_service(question, subject, level, history):
    prompt = f"""
    Kamu adalah AI Tutor untuk pelajaran {subject}, level siswa {level}.

    Riwayat percakapan:
    {history}

    Pertanyaan siswa:
    {question}

    Berikan jawaban step-by-step, jelas, mudah dimengerti,
    dan tanyakan kembali apakah siswa paham.
    """

    resp = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return resp.text