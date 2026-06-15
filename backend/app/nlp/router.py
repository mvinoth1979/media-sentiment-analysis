from app.nlp.language_detector import detect_language
from app.nlp.gemini_handler import analyse_with_gemini
from app.nlp.groq_handler import analyse_with_groq
from app.nlp.schemas import NLPResult
from app.pipeline.rate_limiter import acquire_nlp_slot

SUPPORTED_LANGUAGES = {"en", "ta"}


def analyse_article(article: dict) -> NLPResult | None:
    acquire_nlp_slot()
    text = f"{article.get('title', '')} {article.get('body', '')}".strip()
    declared_lang = article.get("language", "")

    detected_lang, lang_conf = detect_language(text)
    language = detected_lang if lang_conf > 0.75 else declared_lang

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    result = analyse_with_gemini(text, language)
    if result is None:
        result = analyse_with_groq(text, language)

    return result
