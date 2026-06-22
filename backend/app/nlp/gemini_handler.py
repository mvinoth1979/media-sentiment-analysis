"""
Gemini NLP handler.

Prompts have been trimmed to remove fields now handled by code_extractors:
  - states_mentioned  (regex + city map — more accurate than LLM)
  - topics            (keyword dict)
  - keywords          (frequency count)

This saves ~130 tokens per article call. The JSON schemas now only ask for
fields where LLM adds genuine value: sentiment scores, entities, editorial
tone, issue_category, and creator_type.

Client selection is delegated to APIRouter — this module only builds prompts
and parses responses.
"""

import json as _json
import logging
import re
import time
from google import genai
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

_GEMINI_MODELS = [settings.gemini_model, "gemini-2.5-flash", "gemini-flash-latest"]


def _get_client():
    """Backward-compat client for AI summary and competitor discovery (paid tier)."""
    from app.nlp.api_router import APIRouter
    result = APIRouter.get_gemini_client(paid=True)
    if result:
        return result[0]
    # If paid is rate-limited, try free as last resort
    result = APIRouter.get_gemini_client(paid=False)
    if result:
        return result[0]
    # Absolute fallback — create directly (no rate-limit awareness)
    return genai.Client(api_key=settings.gemini_api_key or settings.gemini_free_api_key)


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
    "news": (
        "News article — use journalistic framing. "
        "Weight body sentiment more than headline."
    ),
    "youtube_video": (
        "YouTube video title+description — description carries more weight than "
        "clickbait title. Focus on the creator's stance toward the brand."
    ),
    "youtube_comment": (
        "Short YouTube comment. Emojis signal sentiment (😤😡=negative, 😊❤️=positive). "
        "Slang and Hinglish are intentional. Keep confidence low for very short text."
    ),
    "reddit_post": (
        "Reddit post from an Indian subreddit. Upvotes indicate community agreement. "
        "Read the overall narrative, not just the post author's framing."
    ),
    "reddit_comment": (
        "Short Reddit comment. Sarcasm and irony are common. "
        "Hinglish is intentional. Keep confidence low for brief text."
    ),
    "google_review": (
        "Google Business review. Star rating anchors sentiment strongly. "
        "Text may be brief."
    ),
}

# ── Slim prompt: news (headline + body split, editorial tone) ─────────────────
# Removed from schema: states_mentioned, topics, keywords (code_extractors handles these)
_PROMPT_NEWS = """Analyse sentiment of this news content for brand/product mentions.

Source: {source_context}

HEADLINE: {title}

BODY: {body}

Return ONLY valid JSON — no markdown, no explanation:
{{
  "sentiment_score": <float -1.0 to +1.0, overall body-weighted>,
  "headline_sentiment_score": <float -1.0 to +1.0, headline only>,
  "body_sentiment_score": <float -1.0 to +1.0, body only>,
  "sentiment_label": <"positive" | "negative" | "neutral">,
  "editorial_tone": <"factual" | "positive_frame" | "negative_frame" | "critical">,
  "entities": [<named entities: brands, people, organisations, products>],
  "issue_category": <"financial_performance"|"regulatory_compliance"|"product_quality"|"leadership_governance"|"crisis_controversy"|"awards_recognition"|"csr_sustainability"|"policy_government"|"competitive_landscape"|"customer_experience"|"brand_advocacy"|"market_opportunity"|"other">,
  "confidence": <float 0.0 to 1.0>
}}

Language: {language}"""

# ── Slim prompt: YouTube video / Reddit post ──────────────────────────────────
_PROMPT_SOCIAL_POST = """Analyse the sentiment of this content toward the brand or product mentioned.

Source: {source_context}

Return ONLY valid JSON:
{{
  "sentiment_score": <float -1.0 to +1.0>,
  "sentiment_label": <"positive" | "negative" | "neutral">,
  "entities": [<named entities: brands, people, products>],
  "issue_category": <"financial_performance"|"regulatory_compliance"|"product_quality"|"leadership_governance"|"crisis_controversy"|"awards_recognition"|"csr_sustainability"|"policy_government"|"competitive_landscape"|"customer_experience"|"brand_advocacy"|"market_opportunity"|"other">,
  "creator_type": <for youtube_video only: "journalist"|"reviewer"|"influencer"|"customer"|"industry_expert"|"activist"|"competitor_affiliate"|"unknown". Use "unknown" for all other sources.>,
  "confidence": <float 0.0 to 1.0>
}}

Language: {language}
Text:
{text}"""

# ── Ultra-slim prompt: short comments ────────────────────────────────────────
# Comments (youtube_comment, reddit_comment) only need core sentiment.
# issue_category is omitted — comments rarely appear in TopIssuesTable.
_PROMPT_COMMENT = """Sentiment of this comment toward the brand/product:

Return ONLY valid JSON:
{{"sentiment_score": <float -1.0 to +1.0>, "sentiment_label": <"positive"|"negative"|"neutral">, "confidence": <float 0.0-1.0>}}

Text: {text}"""


def _build_prompt(
    text: str,
    language: str,
    source_type: str,
    title: str,
    body: str,
) -> tuple[str, bool]:
    """
    Returns (prompt, is_structured_news).
    is_structured_news=True when the response will include headline/body scores.
    """
    ctx = _SOURCE_CONTEXT.get(source_type, _SOURCE_CONTEXT["news"])

    if source_type in ("youtube_comment", "reddit_comment"):
        return _PROMPT_COMMENT.format(text=text[:1500]), False

    if source_type == "news" and title and body:
        return _PROMPT_NEWS.format(
            source_context=ctx,
            title=title[:400],
            body=body[:2600],
            language=language,
        ), True

    # YouTube video, Reddit post, blog, Google review
    return _PROMPT_SOCIAL_POST.format(
        source_context=ctx,
        language=language,
        text=text[:3000],
    ), False


def _parse_response(
    data: dict,
    source_type: str,
    is_structured: bool,
    model: str,
) -> NLPResult:
    hs = _clip(data.get("headline_sentiment_score")) if is_structured else None
    bs = _clip(data.get("body_sentiment_score")) if is_structured else None
    is_comment = source_type in ("youtube_comment", "reddit_comment")

    return NLPResult(
        sentiment_score=max(-1.0, min(1.0, float(data["sentiment_score"]))),
        sentiment_label=_parse_label(data.get("sentiment_label", "neutral")),
        entities=data.get("entities", []),
        model_used=model,
        confidence=float(data.get("confidence", 0.0)),
        source_type=source_type,
        headline_sentiment_score=hs,
        body_sentiment_score=bs,
        editorial_tone=_parse_tone(data.get("editorial_tone", "")) if is_structured else "",
        issue_category=_parse_category(data.get("issue_category", "other")) if not is_comment else "other",
        creator_type=_parse_creator_type(data.get("creator_type", "unknown")) if source_type == "youtube_video" else "unknown",
    )


def analyse_with_gemini(
    text: str,
    language: str,
    source_type: str = "news",
    *,
    title: str = "",
    body: str = "",
    client: genai.Client | None = None,
    client_label: str = "gemini_paid",
) -> tuple[NLPResult | None, bool]:
    """
    Returns (result, was_rate_limited).

    Pass `client` and `client_label` from APIRouter for free/paid routing.
    Falls back to the paid singleton when called without a client (AI summary path).
    """
    if client is None:
        client = _get_client()
        client_label = "gemini_paid"

    prompt, is_structured = _build_prompt(text, language, source_type, title, body)
    rate_limited = False

    from app.nlp.api_router import APIRouter
    for model in _GEMINI_MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                raw = _strip_fences(response.text.strip())
                data = _json.loads(raw)
                return _parse_response(data, source_type, is_structured, model), False

            except Exception as e:
                err = str(e)
                if "404" in err:
                    break  # model not found → try next model
                if "429" in err or "rate" in err.lower() or "quota" in err.lower():
                    rate_limited = True
                    APIRouter.mark_rate_limited(client_label, seconds=65)
                    backoff = 2 ** attempt * 5
                    log.warning("Gemini '%s' rate-limited (attempt %d) — waiting %ds", client_label, attempt + 1, backoff)
                    time.sleep(backoff)
                    continue
                log.warning("Gemini error (%s/%s, attempt %d): %s", client_label, model, attempt + 1, err[:200])
                break  # non-retryable error

    return None, rate_limited


# ── Competitor discovery (paid tier, called once per brand) ───────────────────

_COMPETITOR_PROMPT = """You are a competitive intelligence analyst for Indian markets.

Brand: {brand_name}
Brand keywords: {keywords}

Entities frequently co-mentioned with this brand in Indian news and social media:
{entity_list}

Task: Identify the 3–5 closest DIRECT competitors to this brand.
Rules:
- Include only genuine competitors (same product/service category, competing for same customers)
- Exclude: government bodies, regulatory authorities, news outlets, raw material suppliers, banks/lenders
- Prefer names already in the entity list above (confirmed to appear in coverage)
- Use your knowledge of the Indian market to fill gaps when the entity list is sparse

Return ONLY valid JSON, no explanation:
{{"competitors": ["Name1", "Name2", "Name3"]}}"""


def discover_competitors(brand_name: str, keywords: list[str], entities: list[str]) -> list[str]:
    entity_list = ", ".join(entities[:20]) if entities else "No entities found yet."
    prompt = _COMPETITOR_PROMPT.format(
        brand_name=brand_name,
        keywords=", ".join(keywords[:10]),
        entity_list=entity_list,
    )
    client = _get_client()
    for model in _GEMINI_MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                raw = _strip_fences(response.text.strip())
                data = _json.loads(raw)
                competitors = [str(c).strip() for c in data.get("competitors", []) if c]
                return competitors[:5]
            except Exception as e:
                err = str(e)
                if "404" in err:
                    break
                if "429" in err or "rate" in err.lower():
                    time.sleep(2 ** attempt * 5)
                    continue
                log.warning("Competitor discovery error (%s, attempt %d): %s", model, attempt + 1, err[:200])
                break
    return []
