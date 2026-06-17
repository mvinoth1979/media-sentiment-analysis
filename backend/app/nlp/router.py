import logging
from app.nlp.language_detector import detect_language
from app.nlp.gemini_handler import analyse_with_gemini
from app.nlp.groq_handler import analyse_with_groq
from app.nlp.schemas import NLPResult
from app.nlp.circuit_breaker import is_open, trip, COOLDOWN_SECONDS
from app.pipeline.rate_limiter import acquire_nlp_slot

log = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"en", "ta", "hi", "gu", "bn", "kn"}


def analyse_article(article: dict) -> NLPResult | None:
    if is_open():
        return None

    acquire_nlp_slot()
    text = f"{article.get('title', '')} {article.get('body', '')}".strip()
    declared_lang = article.get("language", "")

    detected_lang, lang_conf = detect_language(text)
    language = detected_lang if lang_conf > 0.75 else declared_lang

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    result, gemini_limited = analyse_with_gemini(text, language)
    if result is not None:
        return result

    result, groq_limited = analyse_with_groq(text, language)
    if result is None and gemini_limited and groq_limited:
        log.warning("Both Gemini and Groq rate-limited — opening NLP circuit breaker for %ds",
                     COOLDOWN_SECONDS)
        trip()

    return result
