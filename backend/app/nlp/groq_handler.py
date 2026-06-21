import json
import logging
import re
from groq import Groq
from app.config import settings
from app.nlp.schemas import NLPResult

log = logging.getLogger(__name__)

_client = None
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

_INDIAN_STATES = (
    "Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa, Gujarat, "
    "Haryana, Himachal Pradesh, Jharkhand, Karnataka, Kerala, Madhya Pradesh, "
    "Maharashtra, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Rajasthan, "
    "Sikkim, Tamil Nadu, Telangana, Tripura, Uttar Pradesh, Uttarakhand, West Bengal, "
    "Delhi, Jammu & Kashmir, Ladakh, Chandigarh, Puducherry"
)


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def _strip_fences(raw: str) -> str:
    return re.sub(r"^```(?:json)?\s*", "", raw).rstrip("`").strip()


def _parse_label(label: str) -> str:
    normalized = label.lower().strip()
    return normalized if normalized in _VALID_LABELS else "neutral"


def _parse_tone(tone: str) -> str:
    normalized = tone.lower().strip().replace(" ", "_")
    return normalized if normalized in _VALID_TONES else "factual"


def _parse_category(cat: str) -> str:
    normalized = cat.lower().strip().replace(" ", "_")
    return normalized if normalized in _VALID_CATEGORIES else "other"


def _parse_creator_type(ct: str) -> str:
    normalized = ct.lower().strip().replace(" ", "_")
    return normalized if normalized in _VALID_CREATOR_TYPES else "unknown"


def _clip(v) -> float | None:
    if v is None:
        return None
    try:
        return max(-1.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return None


_SOURCE_CONTEXT = {
    "news": "News article — use journalistic framing, extract Indian states carefully.",
    "youtube_video": (
        "YouTube video title+description — weight description over clickbait title, "
        "focus on creator's opinion about the brand."
    ),
    "youtube_comment": (
        "Short YouTube comment — emojis signal sentiment (😤😡=negative, 😊❤️=positive), "
        "slang/Hinglish is intentional, states_mentioned usually empty."
    ),
    "reddit_post": (
        "Reddit post from an Indian subreddit — upvotes signal community agreement; "
        "extract brand sentiment from community reaction, not just post author."
    ),
    "reddit_comment": (
        "Short Reddit comment — sarcasm/irony common; Hinglish intentional; "
        "states_mentioned usually empty; weight tone heavily."
    ),
    "google_review": (
        "Google Business review — star rating anchors sentiment (4-5=positive, 1-2=negative, "
        "3=neutral); text may be brief; states_mentioned usually empty."
    ),
}

_SYSTEM = (
    "You are a sentiment analysis engine. "
    "Return ONLY valid JSON. No explanation, no markdown, no code fences."
)

_USER_NEWS = """Analyse sentiment of this news content for brand/product mentions.

Source: {source_context}

HEADLINE: {title}
BODY: {body}

Return JSON: {{
  "sentiment_score": float -1 to 1 (overall body-weighted),
  "headline_sentiment_score": float -1 to 1 (headline only),
  "body_sentiment_score": float -1 to 1 (body only),
  "sentiment_label": "positive"|"negative"|"neutral",
  "editorial_tone": "factual"|"positive_frame"|"negative_frame"|"critical",
  "entities": [strings], "topics": [strings], "keywords": [strings],
  "states_mentioned": [Indian state/UT names — only from: {states}. Empty list if none.],
  "issue_category": "financial_performance"|"regulatory_compliance"|"product_quality"|"leadership_governance"|"crisis_controversy"|"awards_recognition"|"csr_sustainability"|"policy_government"|"competitive_landscape"|"customer_experience"|"brand_advocacy"|"market_opportunity"|"other",
  "confidence": float 0-1
}}

Language: {language}"""

_USER_COMBINED = """Analyse sentiment of this text for brand/product mentions.

Source: {source_context}

Return JSON: {{"sentiment_score": float -1 to 1, "sentiment_label": "positive"|"negative"|"neutral",
"entities": [strings], "topics": [strings], "keywords": [strings],
"states_mentioned": [Indian state/UT names from text — use only: {states}. Empty list if none.],
"issue_category": "financial_performance"|"regulatory_compliance"|"product_quality"|"leadership_governance"|"crisis_controversy"|"awards_recognition"|"csr_sustainability"|"policy_government"|"competitive_landscape"|"customer_experience"|"brand_advocacy"|"market_opportunity"|"other",
"creator_type": "journalist"|"reviewer"|"influencer"|"customer"|"industry_expert"|"activist"|"competitor_affiliate"|"unknown" (for youtube_video: classify creator; use "unknown" for all non-video sources),
"confidence": float 0-1}}

Language: {language}
Text: {text}"""


def analyse_with_groq(
    text: str,
    language: str,
    source_type: str = "news",
    *,
    title: str = "",
    body: str = "",
) -> tuple[NLPResult | None, bool]:
    """Returns (result, was_rate_limited)."""
    use_structured = bool(title and body and source_type == "news")
    context = _SOURCE_CONTEXT.get(source_type, _SOURCE_CONTEXT["news"])

    if use_structured:
        user_prompt = _USER_NEWS.format(
            source_context=context,
            title=title[:300],
            body=body[:1700],
            states=_INDIAN_STATES,
            language=language,
        )
    else:
        user_prompt = _USER_COMBINED.format(
            source_context=context,
            states=_INDIAN_STATES,
            language=language,
            text=text[:2000],
        )

    try:
        resp = _get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=600,
        )
        raw = _strip_fences(resp.choices[0].message.content.strip())
        data = json.loads(raw)

        hs = _clip(data.get("headline_sentiment_score")) if use_structured else None
        bs = _clip(data.get("body_sentiment_score")) if use_structured else None

        return NLPResult(
            sentiment_score=max(-1.0, min(1.0, float(data["sentiment_score"]))),
            sentiment_label=_parse_label(data["sentiment_label"]),
            entities=data.get("entities", []),
            topics=data.get("topics", []),
            keywords=data.get("keywords", []),
            states_mentioned=data.get("states_mentioned", []),
            model_used="groq-llama-3.1-8b-instant",
            confidence=float(data.get("confidence", 0.0)),
            source_type=source_type,
            headline_sentiment_score=hs,
            body_sentiment_score=bs,
            editorial_tone=_parse_tone(data.get("editorial_tone", "")) if use_structured else "",
            issue_category=_parse_category(data.get("issue_category", "other")),
            creator_type=_parse_creator_type(data.get("creator_type", "unknown")) if source_type == "youtube_video" else "unknown",
        ), False
    except Exception as e:
        log.error("Groq error: %s — %s", type(e).__name__, str(e)[:300])
        rate_limited = "429" in str(e) or "rate limit" in str(e).lower()
        return None, rate_limited
