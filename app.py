from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers (termasuk batch)
from routers import generate, tutor,analysis, chat, batch

app = FastAPI(title="LYNX AI Backend (FULL GEMINI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTER ROUTES
app.include_router(generate.router, prefix="/generate", tags=["Generate Soal"])
app.include_router(tutor.router, prefix="/tutor", tags=["AI Tutor"])
app.include_router(chat.router, prefix="/tutor", tags=["Deep Tutor / Chat"]) # Chat Multimodal
app.include_router(batch.router, prefix="/grade", tags=["Batch Processing"]) # <--- FITUR BARU
app.include_router(analysis.router, prefix="/analysis", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "LYNX AI (Gemini Version) is running 🚀"}