import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_FLASH_API_KEY = os.getenv("GEMINI_FLASH_API_KEY")
GEMINI_PRO_API_KEY = os.getenv("GEMINI_PRO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")


def ensure_keys():
    missing = []
    if not GEMINI_FLASH_API_KEY:
        missing.append("GEMINI_FLASH_API_KEY")
    if not GEMINI_PRO_API_KEY:
        missing.append("GEMINI_PRO_API_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        # Jangan raise di import, tapi kasih warning
        print(f"[WARN] Missing API keys in .env: {', '.join(missing)}")


ensure_keys()