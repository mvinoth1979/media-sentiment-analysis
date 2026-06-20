import json
import re
import time
from google import genai
from app.config import settings
from app.nlp.schemas import NLPResult

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
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _strip_fences(raw: str) -> str:
    return re.sub(r"^```(?:json)?\s*", "", raw).rstrip("`").strip()


def _parse_label(label: str) -> str:
    normalized = label.lower().strip()
    return normalized if normalized in _VALID_LABELS else "neutral"


_SOURCE_CONTEXT = {
    "news": (
        "This is a news article. Use journalistic framing to assess brand sentiment. "
        "Extract Indian states mentioned in the text carefully — they are significant."
    ),
    "youtube_video": (
        "This is a YouTube video title and description. The title may use clickbait phrasing — "
        "weight the description more heavily than the title when judging true sentiment. "
        "Focus on the creator's opinion about the brand or product."
    ),
    "youtube_comment": (
        "This is a short YouTube comment. Emojis carry strong sentiment (😤😡=negative, 😊❤️=positive). "
        "Slang and mixed languages (Hinglish, Tanglish) are intentional — focus on emotional tone. "
        "states_mentioned will almost always be empty. Confidence should reflect text brevity."
    ),
}

_PROMPT = """Analyse the sentiment of the following text for the brand/product mentions it contains.

Source context: {source_context}

Return ONLY valid JSON with this exact schema:
{{
  "sentiment_score": <float from -1.0 (very negative) to +1.0 (very positive)>,
  "sentiment_label": <"positive" | "negative" | "neutral">,
  "entities": [<named entities: brands, people, locations, products>],
  "topics": [<topics from: product_quality, pricing, customer_service, leadership, campaign, legal, expansion, financial, other>],
  "keywords": [<up to 8 significant keywords>],
  "states_mentioned": [<Indian states or UTs explicitly named or clearly implied by a city/region in the text. Use only full official state names from this list: {states}. Empty list if none found.>],
  "confidence": <float 0.0 to 1.0>
}}

Language: {language}
Text:
{text}"""


_COMPETITOR_PROMPT = """You are a competitive intelligence analyst for Indian markets.

Brand: {brand_name}
Brand keywords: {keywords}

Entities frequently co-mentioned with this brand in Indian news and social media:
{entity_list}

Task: Identify the 3–5 closest DIRECT competitors to this brand.
Rules:
- Include only genuine competitors (same product/service category, competing for same customers)
- Exclude: government bodies, regulatory authorities, news outlets, raw material suppliers, banks/lenders
- Prefer names already in the entity list above (they are confirmed to appear in coverage)
- Use your own knowledge of the Indian market to fill gaps when the entity list is sparse

Return ONLY valid JSON, no explanation:
{{"competitors": ["Name1", "Name2", "Name3"]}}"""


def discover_competitors(brand_name: str, keywords: list[str], entities: list[str]) -> list[str]:
    entity_list = ", ".join(entities[:20]) if entities else "No entities found in coverage yet."
    prompt = _COMPETITOR_PROMPT.format(
        brand_name=brand_name,
        keywords=", ".join(keywords[:10]),
        entity_list=entity_list,
    )
    for attempt in range(3):
        try:
            response = _get_client().models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            raw = _strip_fences(response.text.strip())
            data = json.loads(raw)
            competitors = [str(c).strip() for c in data.get("competitors", []) if c]
            return competitors[:5]
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                time.sleep(2 ** attempt * 5)
                continue
            break
    return []


def analyse_with_gemini(text: str, language: str,
                        source_type: str = "news") -> tuple[NLPResult | None, bool]:
    """Returns (result, was_rate_limited). was_rate_limited is True only if every
    attempt failed due to a 429/rate-limit response, so callers can distinguish
    quota exhaustion from genuine parsing/content failures."""
    context = _SOURCE_CONTEXT.get(source_type, _SOURCE_CONTEXT["news"])
    prompt = _PROMPT.format(
        source_context=context,
        states=_INDIAN_STATES,
        language=language,
        text=text[:3000],
    )
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
                states_mentioned=data.get("states_mentioned", []),
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
