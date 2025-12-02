from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import generate, grade_llm, analysis, chat, grade_image

app = FastAPI(title="LYNX AI Backend (EduSync)")

# CORS – sesuaikan origin frontend kamu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ganti ke origin FE di production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(generate.router, prefix="/generate", tags=["Generate"])
app.include_router(grade_llm.router, prefix="/grade/llm", tags=["LLM Essay Grader"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(chat.router, prefix="/chat", tags=["Chat / Deep Tutor"])
app.include_router(grade_image.router, prefix="/grade/image", tags=["Image Grader"])

@app.get("/")
def root():
    return {"message": "LYNX AI is running 🚀"}