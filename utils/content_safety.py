from typing import Tuple


BANNED_KEYWORDS = [
    "bunuh diri",
    "bom",
    "narkoba",
    # tambahin kalau mau
]


def is_safe_text(text: str) -> Tuple[bool, str]:
    lower = text.lower()
    for kw in BANNED_KEYWORDS:
        if kw in lower:
            return False, f"Teks mengandung kata terlarang: '{kw}'"
    return True, ""