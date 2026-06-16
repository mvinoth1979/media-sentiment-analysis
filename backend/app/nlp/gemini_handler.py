import json
import re
import time
from google import genai
from app.config import settings
from app.nlp.schemas import NLPResult

_client = None
_VALID_LABELS = {"positive", "negative", "neutral"}


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _strip_fences(raw: str) -> str:
    return re.sub(r"^```(?:json)?\s*", "", raw).rstrip("`").strip()


def _parse_label(label: str) -> str:
    normalized = label.lower().strip()
    return normalized if normalized in _VALID_LABELS else "neutral"


_PROMPT = """Analyse the sentiment of the following news article text for the brand/product mentions it contains.

Return ONLY valid JSON with this exact schema:
{{
  "sentiment_score": <float from -1.0 (very negative) to +1.0 (very positive)>,
  "sentiment_label": <"positive" | "negative" | "neutral">,
  "entities": [<named entities: brands, people, locations, products>],
  "topics": [<topics from: product_quality, pricing, customer_service, leadership, campaign, legal, expansion, financial, other>],
  "keywords": [<up to 8 significant keywords>],
  "confidence": <float 0.0 to 1.0>
}}

Article language: {language}
Article text:
{text}"""


def analyse_with_gemini(text: str, language: str) -> tuple[NLPResult | None, bool]:
    """Returns (result, was_rate_limited). was_rate_limited is True only if every
    attempt failed due to a 429/rate-limit response, so callers can distinguish
    quota exhaustion from genuine parsing/content failures."""
    prompt = _PROMPT.format(language=language, text=text[:3000])
    rate_limited = False
    for attempt in range(3):
        try:
            response = _get_client().models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            raw = _strip_fences(response.text.strip())
            data = json.loads(raw)
            return NLPResult(
                sentiment_score=max(-1.0, min(1.0, float(data["sentiment_score"]))),
                sentiment_label=_parse_label(data["sentiment_label"]),
                entities=data.get("entities", []),
                topics=data.get("topics", []),
                keywords=data.get("keywords", []),
                model_used="gemini-2.0-flash",
                confidence=float(data.get("confidence", 0.0)),
            ), False
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                rate_limited = True
                time.sleep(2 ** attempt * 5)
                continue
            return None, False
    return None, rate_limited
