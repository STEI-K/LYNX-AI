from typing import Optional

import google.generativeai as genai
from openai import OpenAI

from .config import GEMINI_FLASH_API_KEY, GEMINI_PRO_API_KEY, OPENAI_API_KEY


def get_gemini_flash_model(model_name: str = "gemini-1.5-flash"):
    """
    Fast / murah – cocok buat:
    - generate banyak soal PG
    - quick suggestions
    """
    if not GEMINI_FLASH_API_KEY:
        raise RuntimeError("GEMINI_FLASH_API_KEY is not set in .env")

    genai.configure(api_key=GEMINI_FLASH_API_KEY)
    return genai.GenerativeModel(model_name)


def get_gemini_pro_model(model_name: str = "gemini-1.5-pro"):
    """
    Lebih pintar / reasoning kuat – cocok buat:
    - essay feedback
    - deep tutor
    - vision grading lembar jawaban
    """
    if not GEMINI_PRO_API_KEY:
        raise RuntimeError("GEMINI_PRO_API_KEY is not set in .env")

    genai.configure(api_key=GEMINI_PRO_API_KEY)
    return genai.GenerativeModel(model_name)


def get_openai_client() -> Optional[OpenAI]:
    """
    Client OpenAI – bisa dipakai untuk essay grading / alternatif model.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return OpenAI(api_key=OPENAI_API_KEY)