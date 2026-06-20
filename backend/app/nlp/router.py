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

    title = article.get("title", "") or ""
    body  = article.get("body",  "") or ""
    text  = f"{title} {body}".strip()
    source_type   = article.get("source_type") or "news"
    declared_lang = article.get("language", "")

    # Very short comments (YouTube or Reddit) default to neutral rather than
    # burning an NLP call that will return a low-confidence guess anyway.
    if source_type in ("youtube_comment", "reddit_comment") and len(text.split()) < 4:
        return NLPResult(
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence=0.3,
            model_used="short-text-default",
            source_type=source_type,
        )

    detected_lang, lang_conf = detect_language(text)
    language = detected_lang if lang_conf > 0.75 else declared_lang

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    # Pass title and body separately for news so both handlers can return
    # headline_sentiment_score, body_sentiment_score, and editorial_tone (A2 + B1).
    result, gemini_limited = analyse_with_gemini(
        text, language, source_type, title=title, body=body
    )
    if result is not None:
        result.source_type = source_type
        return result

    result, groq_limited = analyse_with_groq(
        text, language, source_type, title=title, body=body
    )
    if result is None and gemini_limited and groq_limited:
        log.warning("Both Gemini and Groq rate-limited — opening NLP circuit breaker for %ds",
                     COOLDOWN_SECONDS)
        trip()

    if result is not None:
        result.source_type = source_type
    return result
