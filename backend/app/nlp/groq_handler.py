import json
from groq import Groq
from app.config import settings
from app.nlp.schemas import NLPResult

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


_SYSTEM = (
    "You are a sentiment analysis engine. "
    "Return ONLY valid JSON. No explanation, no markdown, no code fences."
)

_USER = """Analyse sentiment of this news article text for brand/product mentions.

Return JSON: {{"sentiment_score": float -1 to 1, "sentiment_label": "positive"|"negative"|"neutral",
"entities": [strings], "topics": [strings], "keywords": [strings], "confidence": float 0-1}}

Language: {language}
Text: {text}"""


def analyse_with_groq(text: str, language: str) -> NLPResult | None:
    try:
        resp = _get_client().chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _USER.format(language=language, text=text[:2000])},
            ],
            temperature=0.1,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        return NLPResult(
            sentiment_score=float(data["sentiment_score"]),
            sentiment_label=data["sentiment_label"],
            entities=data.get("entities", []),
            topics=data.get("topics", []),
            keywords=data.get("keywords", []),
            model_used="groq-gemma2-9b-it",
            confidence=float(data.get("confidence", 0.0)),
        )
    except Exception:
        return None
