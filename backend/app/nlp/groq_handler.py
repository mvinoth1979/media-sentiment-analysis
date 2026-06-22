"""
Groq NLP handler (LLaMA 3.1 8B Instant — free tier).

Used for Tier 1 routing: EN social comments, YouTube/Reddit posts, EN blogs.
Prompt schemas match gemini_handler.py slim format — no states/topics/keywords.

Client selection delegated to APIRouter (supports round-robin across 2 keys).
"""

import json
import logging
import re
from groq import Groq
from app.config import settings
from app.nlp.schemas import NLPResult

log = logging.getLogger(__name__)

_VALID_LABELS = {"positive", "negative", "neutral"}
_VALID_TONES  = {"factual", "positive_frame", "negative_frame", "critical"}
_VALID_CREATOR_TYPES = {
    "journalist", "reviewer", "influencer", "customer",
    "industry_expert", "activist", "competitor_affiliate", "unknown",
}
_VALID_CATEGORIES = {
    "financial_performance", "regulatory_compliance", "product_quality",
    "leadership_governance", "crisis_controversy", "awards_recognition",
    "csr_sustainability", "policy_government", "competitive_landscape",
    "customer_experience", "brand_advocacy", "market_opportunity", "other",
}

_GROQ_MODEL = "llama-3.1-8b-instant"


def _get_client() -> Groq:
    """Direct client — used only as fallback if APIRouter has no keys configured."""
    return Groq(api_key=settings.groq_api_key)


def _strip_fences(raw: str) -> str:
    return re.sub(r"^```(?:json)?\s*", "", raw).rstrip("`").strip()


def _parse_label(label: str) -> str:
    n = label.lower().strip()
    return n if n in _VALID_LABELS else "neutral"


def _parse_tone(tone: str) -> str:
    n = tone.lower().strip().replace(" ", "_")
    return n if n in _VALID_TONES else "factual"


def _parse_category(cat: str) -> str:
    n = cat.lower().strip().replace(" ", "_")
    return n if n in _VALID_CATEGORIES else "other"


def _parse_creator_type(ct: str) -> str:
    n = ct.lower().strip().replace(" ", "_")
    return n if n in _VALID_CREATOR_TYPES else "unknown"


def _clip(v) -> float | None:
    if v is None:
        return None
    try:
        return max(-1.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return None


_SOURCE_CONTEXT = {
    "news": "News article — journalistic framing, body sentiment more important than headline.",
    "youtube_video": "YouTube video — description more reliable than clickbait title; focus on creator's opinion.",
    "youtube_comment": "Short YouTube comment — emojis carry sentiment; Hinglish intentional.",
    "reddit_post": "Reddit post — upvotes signal community agreement; read overall narrative.",
    "reddit_comment": "Short Reddit comment — sarcasm common; Hinglish intentional.",
    "google_review": "Google Business review — star rating anchors sentiment.",
}

_SYSTEM = (
    "You are a sentiment analysis engine. "
    "Return ONLY valid JSON. No explanation, no markdown, no code fences."
)

# ── Slim prompts (matching gemini_handler slim format) ────────────────────────

_USER_NEWS = """Analyse sentiment of this news content for brand/product mentions.

Source: {source_context}

HEADLINE: {title}
BODY: {body}

Return JSON:
{{
  "sentiment_score": float -1 to 1 (body-weighted overall),
  "headline_sentiment_score": float -1 to 1,
  "body_sentiment_score": float -1 to 1,
  "sentiment_label": "positive"|"negative"|"neutral",
  "editorial_tone": "factual"|"positive_frame"|"negative_frame"|"critical",
  "entities": [strings],
  "issue_category": "financial_performance"|"regulatory_compliance"|"product_quality"|"leadership_governance"|"crisis_controversy"|"awards_recognition"|"csr_sustainability"|"policy_government"|"competitive_landscape"|"customer_experience"|"brand_advocacy"|"market_opportunity"|"other",
  "confidence": float 0-1
}}

Language: {language}"""

_USER_SOCIAL_POST = """Analyse sentiment of this content toward the brand or product.

Source: {source_context}

Return JSON:
{{"sentiment_score": float -1 to 1, "sentiment_label": "positive"|"negative"|"neutral",
"entities": [strings],
"issue_category": "financial_performance"|"regulatory_compliance"|"product_quality"|"leadership_governance"|"crisis_controversy"|"awards_recognition"|"csr_sustainability"|"policy_government"|"competitive_landscape"|"customer_experience"|"brand_advocacy"|"market_opportunity"|"other",
"creator_type": "journalist"|"reviewer"|"influencer"|"customer"|"industry_expert"|"activist"|"competitor_affiliate"|"unknown",
"confidence": float 0-1}}

Language: {language}
Text: {text}"""

_USER_COMMENT = """Sentiment of this comment toward the brand/product:

Return JSON only: {{"sentiment_score": float -1 to 1, "sentiment_label": "positive"|"negative"|"neutral", "confidence": float 0-1}}

Text: {text}"""


def analyse_with_groq(
    text: str,
    language: str,
    source_type: str = "news",
    *,
    title: str = "",
    body: str = "",
    client: Groq | None = None,
    client_label: str = "groq_0",
) -> tuple[NLPResult | None, bool]:
    """
    Returns (result, was_rate_limited).

    Pass `client` and `client_label` from APIRouter for round-robin rotation.
    """
    from app.nlp.api_router import APIRouter

    if client is None:
        pool_result = APIRouter.get_groq_client()
        if pool_result is None:
            log.warning("No Groq client available — all keys missing or rate-limited")
            return None, False
        client, client_label = pool_result

    ctx = _SOURCE_CONTEXT.get(source_type, _SOURCE_CONTEXT["news"])
    is_comment = source_type in ("youtube_comment", "reddit_comment")
    use_structured = bool(title and body and source_type == "news")

    if is_comment:
        user_prompt = _USER_COMMENT.format(text=text[:1500])
    elif use_structured:
        user_prompt = _USER_NEWS.format(
            source_context=ctx,
            title=title[:300],
            body=body[:1700],
            language=language,
        )
    else:
        user_prompt = _USER_SOCIAL_POST.format(
            source_context=ctx,
            language=language,
            text=text[:2000],
        )

    try:
        resp = client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=400,
        )
        raw = _strip_fences(resp.choices[0].message.content.strip())
        data = json.loads(raw)

        hs = _clip(data.get("headline_sentiment_score")) if use_structured else None
        bs = _clip(data.get("body_sentiment_score")) if use_structured else None

        return NLPResult(
            sentiment_score=max(-1.0, min(1.0, float(data["sentiment_score"]))),
            sentiment_label=_parse_label(data.get("sentiment_label", "neutral")),
            entities=data.get("entities", []),
            model_used=f"groq-{_GROQ_MODEL}",
            confidence=float(data.get("confidence", 0.0)),
            source_type=source_type,
            headline_sentiment_score=hs,
            body_sentiment_score=bs,
            editorial_tone=_parse_tone(data.get("editorial_tone", "")) if use_structured else "",
            issue_category=_parse_category(data.get("issue_category", "other")) if not is_comment else "other",
            creator_type=_parse_creator_type(data.get("creator_type", "unknown")) if source_type == "youtube_video" else "unknown",
        ), False

    except Exception as e:
        err_str = str(e)
        log.error("Groq error (%s): %s — %s", client_label, type(e).__name__, err_str[:300])
        is_rate_limited = "429" in err_str or "rate limit" in err_str.lower()
        if is_rate_limited:
            APIRouter.mark_rate_limited(client_label, seconds=65)
        return None, is_rate_limited
