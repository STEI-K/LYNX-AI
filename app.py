from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers (HAPUS 'tutor')
from routers import generate, analysis, chat, batch

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

# GANTI routing lama 'tutor' menjadi 'chat' yang baru
app.include_router(chat.router, prefix="/chat", tags=["General Chat & Assistant"]) 

app.include_router(batch.router, prefix="/grade", tags=["Batch Processing"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "LYNX AI is running "}