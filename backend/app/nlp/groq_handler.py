import json
import logging
import re
from groq import Groq
from app.config import settings
from app.nlp.schemas import NLPResult

log = logging.getLogger(__name__)

_client = None
_VALID_LABELS = {"positive", "negative", "neutral"}

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


_SYSTEM = (
    "You are a sentiment analysis engine. "
    "Return ONLY valid JSON. No explanation, no markdown, no code fences."
)

_USER = """Analyse sentiment of this news article text for brand/product mentions.

Return JSON: {{"sentiment_score": float -1 to 1, "sentiment_label": "positive"|"negative"|"neutral",
"entities": [strings], "topics": [strings], "keywords": [strings],
"states_mentioned": [Indian state/UT names from text — use only: {states}. Empty list if none.],
"confidence": float 0-1}}

Language: {language}
Text: {text}"""


def analyse_with_groq(text: str, language: str) -> tuple[NLPResult | None, bool]:
    """Returns (result, was_rate_limited) so callers can distinguish quota
    exhaustion from genuine parsing/content failures."""
    try:
        prompt = _USER.format(states=_INDIAN_STATES, language=language, text=text[:2000])
        resp = _get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=512,
        )
        raw = _strip_fences(resp.choices[0].message.content.strip())
        data = json.loads(raw)
        return NLPResult(
            sentiment_score=max(-1.0, min(1.0, float(data["sentiment_score"]))),
            sentiment_label=_parse_label(data["sentiment_label"]),
            entities=data.get("entities", []),
            topics=data.get("topics", []),
            keywords=data.get("keywords", []),
            states_mentioned=data.get("states_mentioned", []),
            model_used="groq-llama-3.1-8b-instant",
            confidence=float(data.get("confidence", 0.0)),
        ), False
    except Exception as e:
        log.error("Groq error: %s — %s", type(e).__name__, str(e)[:300])
        rate_limited = "429" in str(e) or "rate limit" in str(e).lower()
        return None, rate_limited
