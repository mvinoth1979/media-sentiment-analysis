from langdetect import detect, LangDetectException


def detect_language(text: str) -> tuple[str, float]:
    if not text or not text.strip():
        return "unknown", 0.0
    try:
        lang = detect(text[:500])
        return lang, 0.99
    except LangDetectException:
        return "unknown", 0.0
