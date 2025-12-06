import json
from services.gemini_client import get_text_model
from utils.prompt_loader import build_student_performance_prompt

def analysis_performace_service(student_name, grade_level, scores):
    """
    Menganalisis nilai raport siswa untuk memberikan feedback akademik.
    """
    # 1. Build Prompt
    prompt = build_student_performance_prompt(student_name, grade_level, scores)
    
    # 2. Call AI
    model = get_text_model()
    
    try:
        response = model.generate_content(prompt)
        # Cleaning JSON
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return {"error": f"Gagal menganalisis nilai: {str(e)}"}