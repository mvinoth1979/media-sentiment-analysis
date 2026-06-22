"""Trustpilot review collector using the official public API.

Workflow:
1. If brand_configs.trustpilot_business_unit_id is empty:
   GET https://api.trustpilot.com/v1/business-units/find?name={domain}&apikey={key}
   -> saves the businessUnitId back to brand_configs
2. GET https://api.trustpilot.com/v1/business-units/{id}/reviews?apikey={key}&perPage=20&orderBy=createdat.desc
3. Maps each review to an article dict.

Returns [] when:
- trustpilot_enabled is False
- trustpilot_domain is not set
- TRUSTPILOT_API_KEY env var is not set
- API returns error
"""

import hashlib
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

log = logging.getLogger(__name__)

_TRUSTPILOT_BASE = "https://api.trustpilot.com/v1"
_TIMEOUT = 15.0
_MAX_REVIEWS = 20


def _content_hash(brand_id: str, author: str, created_at: str) -> str:
    raw = f"{brand_id}:{author}:{created_at}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _save_business_unit_id(brand_id: str, unit_id: str) -> None:
    try:
        from app.storage.postgres import get_db
        db = get_db()
        db.table("brand_configs").update({"trustpilot_business_unit_id": unit_id}).eq("brand_id", brand_id).execute()
        log.info("Brand %s: saved trustpilot_business_unit_id=%s", brand_id[:8], unit_id)
    except Exception as e:
        log.warning("Brand %s: could not save trustpilot_business_unit_id: %s", brand_id[:8], e)


def _resolve_business_unit(domain: str, api_key: str) -> str | None:
    url = f"{_TRUSTPILOT_BASE}/business-units/find"
    try:
        resp = httpx.get(url, params={"name": domain, "apikey": api_key}, timeout=_TIMEOUT)
        resp.raise_for_status()
        units = resp.json().get("businessUnits", [])
        if not units:
            log.info("Trustpilot: no business unit found for domain '%s'", domain)
            return None
        unit_id = units[0].get("id", "")
        log.info("Trustpilot: resolved domain '%s' to unit_id=%s", domain, unit_id)
        return unit_id or None
    except Exception as e:
        log.warning("Trustpilot: business unit lookup failed for '%s': %s", domain, e)
        return None


def _fetch_reviews(unit_id: str, api_key: str) -> list[dict]:
    url = f"{_TRUSTPILOT_BASE}/business-units/{unit_id}/reviews"
    params = {"apikey": api_key, "perPage": _MAX_REVIEWS, "orderBy": "createdat.desc"}
    try:
        resp = httpx.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("reviews", [])
    except Exception as e:
        log.warning("Trustpilot: reviews fetch failed for unit_id=%s: %s", unit_id, e)
        return []


def _map_review(review: dict, brand_id: str, domain: str) -> dict | None:
    stars = int(review.get("stars") or 0)
    text_obj = review.get("text") or {}
    body = (text_obj.get("review") or "").strip()
    author = (review.get("consumer") or {}).get("displayName", "")
    created_at = review.get("createdAt", "")

    if not body:
        return None

    star_str = f"{'★' * stars}{'☆' * (5 - stars)}"
    title = f"Trustpilot Review {star_str}"

    try:
        published_at = datetime.fromisoformat(created_at.replace("Z", "+00:00")).isoformat()
    except (ValueError, AttributeError):
        published_at = datetime.now(tz=timezone.utc).isoformat()

    return {
        "brand_id": brand_id,
        "content_hash": _content_hash(brand_id, author, created_at),
        "story_hash": _content_hash(brand_id, domain, created_at),
        "portal_id": "trustpilot",
        "portal_name": "Trustpilot",
        "url": f"https://www.trustpilot.com/review/{domain}",
        "title": title,
        "body": body[:2000],
        "author": author,
        "published_at": published_at,
        "language": "en",
        "source_type": "trustpilot_review",
        "source_credibility": 0.80,
        "is_regulatory_source": False,
        "reach_metadata": {"rating": stars},
    }


def collect_trustpilot_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 20 Trustpilot reviews for a brand.

    Returns [] when trustpilot_enabled is False, domain is missing,
    or the API key is not configured.
    """
    api_key = settings.trustpilot_api_key
    brand_id = brand["id"]

    if not api_key:
        log.warning("TRUSTPILOT_API_KEY not set — skipping Trustpilot for brand %s", brand_id[:8])
        return []

    if not config.get("trustpilot_enabled", False):
        return []

    domain = (config.get("trustpilot_domain") or "").strip()
    if not domain:
        log.warning("Brand %s: trustpilot_domain not set", brand_id[:8])
        return []

    unit_id = (config.get("trustpilot_business_unit_id") or "").strip()
    if not unit_id:
        unit_id = _resolve_business_unit(domain, api_key)
        if not unit_id:
            return []
        _save_business_unit_id(brand_id, unit_id)

    raw_reviews = _fetch_reviews(unit_id, api_key)
    articles: list[dict] = []
    for review in raw_reviews[:_MAX_REVIEWS]:
        article = _map_review(review, brand_id, domain)
        if article:
            articles.append(article)

    log.info("Brand %s: Trustpilot collected %d reviews", brand_id[:8], len(articles))
    return articles
