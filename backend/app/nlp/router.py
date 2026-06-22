"""
NLP router — orchestrates code extractors + API tier selection + LLM calls.

Execution order per article:
  1. Code extractors (zero cost, always): states, topics, keywords, issue_category
  2. Tier routing (select_tier): decide which API to use
  3. Tier 0: Google reviews with star → code-only sentiment, no LLM
     Tier 0: ≤8 word text → default neutral, no LLM
  4. Language detection (FastText)
  5. Re-route based on confirmed language (Indic → Gemini paid)
  6. LLM call via appropriate tier with fallback chain
  7. Merge: code-extracted fields override LLM where code is more reliable

Fallback chain:
  GEMINI_PAID  → Groq
  GEMINI_FREE  → Gemini paid → Groq
  GROQ         → Gemini free → Gemini paid
"""

import logging
from app.nlp.language_detector import detect_language
from app.nlp.gemini_handler import analyse_with_gemini
from app.nlp.groq_handler import analyse_with_groq
from app.nlp.schemas import NLPResult
from app.nlp.circuit_breaker import is_open, trip, COOLDOWN_SECONDS
from app.nlp.api_router import APIRouter, NLPTier, select_tier
from app.nlp.code_extractors import (
    extract_states_mentioned,
    extract_topics,
    extract_keywords,
    classify_issue_category,
    sentiment_from_star_rating,
)
from app.pipeline.rate_limiter import acquire_nlp_slot

log = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"en", "ta", "hi", "gu", "bn", "kn"}


def _call_gemini(
    text: str, language: str, source_type: str, title: str, body: str, paid: bool
) -> tuple[NLPResult | None, bool]:
    pair = APIRouter.get_gemini_client(paid=paid)
    if pair is None:
        return None, False  # key not configured or rate-limited
    client, label = pair
    return analyse_with_gemini(
        text, language, source_type,
        title=title, body=body,
        client=client, client_label=label,
    )


def _call_groq(
    text: str, language: str, source_type: str, title: str, body: str
) -> tuple[NLPResult | None, bool]:
    pair = APIRouter.get_groq_client()
    if pair is None:
        return None, False  # no Groq key or all rate-limited
    client, label = pair
    return analyse_with_groq(
        text, language, source_type,
        title=title, body=body,
        client=client, client_label=label,
    )


def analyse_article(article: dict) -> NLPResult | None:
    if is_open():
        return None

    acquire_nlp_slot()

    source_type = article.get("source_type") or "news"
    title       = article.get("title", "") or ""
    body        = article.get("body",  "") or ""
    text        = f"{title} {body}".strip()
    word_count  = len(text.split())
    language    = article.get("language", "en") or "en"

    # ── Step 1: Code extractions (always, zero cost) ──────────────────────────
    states   = extract_states_mentioned(text)
    topics   = extract_topics(text)
    keywords = extract_keywords(text)
    issue_cat, issue_conf = classify_issue_category(text)

    # ── Step 2: Tier 0 — no LLM needed ───────────────────────────────────────
    reach_meta  = article.get("reach_metadata") or {}
    star_rating = reach_meta.get("rating")
    has_star    = star_rating is not None

    tier = select_tier(source_type, language, word_count, has_star)

    if tier == NLPTier.NONE:
        if has_star:
            score, label = sentiment_from_star_rating(star_rating)
            model = "code-star-rating"
            conf  = 0.95
        else:
            score, label, model, conf = 0.0, "neutral", "code-short-text", 0.30

        return NLPResult(
            sentiment_score=score,
            sentiment_label=label,
            states_mentioned=states,
            topics=topics,
            keywords=keywords,
            issue_category=issue_cat if issue_conf >= 0.45 else "other",
            confidence=conf,
            model_used=model,
            source_type=source_type,
        )

    # ── Step 3: Language detection (FastText) ─────────────────────────────────
    detected_lang, lang_conf = detect_language(text)
    if lang_conf > 0.75:
        language = detected_lang
    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    # Re-select tier now that we have confirmed language (Indic → paid)
    tier = select_tier(source_type, language, word_count, has_star)

    # ── Step 4: LLM call with fallback chain ──────────────────────────────────
    result: NLPResult | None = None
    any_rate_limited = False

    if tier == NLPTier.GEMINI_PAID:
        result, rl = _call_gemini(text, language, source_type, title, body, paid=True)
        any_rate_limited = any_rate_limited or rl
        if result is None:
            # Paid rate-limited → fall back to Groq
            result, rl = _call_groq(text, language, source_type, title, body)
            any_rate_limited = any_rate_limited or rl

    elif tier == NLPTier.GEMINI_FREE:
        result, rl = _call_gemini(text, language, source_type, title, body, paid=False)
        any_rate_limited = any_rate_limited or rl
        if result is None:
            # Free rate-limited → try paid
            result, rl = _call_gemini(text, language, source_type, title, body, paid=True)
            any_rate_limited = any_rate_limited or rl
        if result is None:
            # Both Gemini tiers failed → Groq as last resort
            result, rl = _call_groq(text, language, source_type, title, body)
            any_rate_limited = any_rate_limited or rl

    elif tier == NLPTier.GROQ:
        result, rl = _call_groq(text, language, source_type, title, body)
        any_rate_limited = any_rate_limited or rl
        if result is None:
            # Groq exhausted → Gemini free → paid
            result, rl = _call_gemini(text, language, source_type, title, body, paid=False)
            any_rate_limited = any_rate_limited or rl
        if result is None:
            result, rl = _call_gemini(text, language, source_type, title, body, paid=True)
            any_rate_limited = any_rate_limited or rl

    # ── Step 5: All providers failed ─────────────────────────────────────────
    if result is None:
        if any_rate_limited:
            log.warning(
                "All NLP providers rate-limited (source=%s, lang=%s) — "
                "circuit breaker open for %ds",
                source_type, language, COOLDOWN_SECONDS,
            )
            trip()
        return None

    # ── Step 6: Merge code-extracted fields ───────────────────────────────────
    # states_mentioned: code regex is more reliable than LLM (no hallucination)
    result.states_mentioned = states

    # topics/keywords: code extraction is adequate; prefer LLM if it returned more
    result.topics   = topics   if topics   else result.topics
    result.keywords = keywords if keywords else result.keywords

    # issue_category: use code result if high confidence AND LLM returned generic "other"
    if issue_conf >= 0.65 and result.issue_category in ("other", "", None):
        result.issue_category = issue_cat
    elif issue_conf >= 0.88:
        # Very high confidence code result overrides LLM (e.g., clear SEBI/RBI article)
        result.issue_category = issue_cat

    result.source_type = source_type
    return result
