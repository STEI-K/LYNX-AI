from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- IMPORT ROUTERS ---
# Pastikan 'chat' ditambahkan di sini!
from routers import generate, tutor, grade_essay, grade_image, analysis, chat

app = FastAPI(title="LYNX AI Backend (FULL GEMINI)")

# --- CORS CONFIG ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER ROUTES ---

# 1. Soal Generator
app.include_router(generate.router, prefix="/generate", tags=["Generate Soal"])

# 2. AI Tutor (Standard) -> Endpoint: /tutor/
app.include_router(tutor.router, prefix="/tutor", tags=["AI Tutor"])

# 3. Deep Tutor & Multimodal (NEW) -> Endpoint: /tutor/deep-tutor
# Kita taruh di bawah prefix /tutor agar url-nya menjadi: http://.../tutor/deep-tutor
app.include_router(chat.router, prefix="/tutor", tags=["Deep Tutor / Chat"])

# 4. Grading Features
app.include_router(grade_essay.router, prefix="/grade/essay", tags=["Essay Grader"])
app.include_router(grade_image.router, prefix="/grade/image", tags=["Vision Grader"])

# 5. Analytics
app.include_router(analysis.router, prefix="/analysis", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "LYNX AI (Gemini Version) is running 🚀"}