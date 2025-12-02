from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import generate, tutor, grade_essay, grade_image, analysis

app = FastAPI(title="LYNX AI Backend (FULL GEMINI)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTES
app.include_router(generate.router, prefix="/generate", tags=["Generate Soal"])
app.include_router(tutor.router, prefix="/tutor", tags=["AI Tutor"])
app.include_router(grade_essay.router, prefix="/grade/essay", tags=["Essay Grader"])
app.include_router(grade_image.router, prefix="/grade/image", tags=["Vision Grader"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "LYNX AI (Gemini Version) is running 🚀"}