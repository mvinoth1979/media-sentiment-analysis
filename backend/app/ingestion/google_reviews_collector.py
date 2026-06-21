"""Google Business Reviews collector using the Google Places API v1.

Workflow:
1. If ``google_places_id`` is empty:  POST to ``places:searchText`` to resolve it,
   then save the resolved ID back to ``brand_configs``.
2. GET ``places/{places_id}`` with ``X-Goog-FieldMask: id,displayName,reviews``.
3. Map up to 5 reviews to article dicts compatible with the pipeline.

Gracefully returns [] when:
- ``GOOGLE_PLACES_API_KEY`` env var / setting is absent.
- ``google_reviews_enabled`` is False.
- The Places API returns an error or no results.
"""

import hashlib
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

log = logging.getLogger(__name__)

_PLACES_BASE = "https://places.googleapis.com/v1"
_TIMEOUT = 12.0
_MAX_REVIEWS = 5


def _content_hash(brand_id: str, author: str, publish_time: str) -> str:
    """SHA256 of ``brand_id:author:publish_time`` — stable across runs."""
    raw = f"{brand_id}:{author}:{publish_time}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _save_places_id(brand_id: str, places_id: str) -> None:
    """Persist the resolved places_id back to brand_configs so the next run skips search."""
    try:
        from app.storage.postgres import get_db
        db = get_db()
        db.table("brand_configs").update({"google_places_id": places_id}).eq("brand_id", brand_id).execute()
        log.info("Brand %s: saved resolved google_places_id=%s", brand_id[:8], places_id)
    except Exception as e:
        log.warning("Brand %s: could not save google_places_id: %s", brand_id[:8], e)


def _resolve_places_id(brand_name: str, api_key: str) -> str | None:
    """POST to places:searchText to resolve a brand name to a Places ID."""
    url = f"{_PLACES_BASE}/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName",
    }
    body = {"textQuery": brand_name, "maxResultCount": 1}
    try:
        resp = httpx.post(url, json=body, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        places = resp.json().get("places", [])
        if not places:
            log.info("Places text search returned no results for '%s'", brand_name)
            return None
        resolved_id = places[0].get("id", "")
        log.info("Resolved '%s' to places_id=%s", brand_name, resolved_id)
        return resolved_id or None
    except Exception as e:
        log.warning("Places text search failed for '%s': %s", brand_name, e)
        return None


def _fetch_place_reviews(places_id: str, api_key: str) -> dict:
    """GET place details including reviews."""
    url = f"{_PLACES_BASE}/places/{places_id}"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "id,displayName,reviews",
    }
    try:
        resp = httpx.get(url, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        log.warning("Places fetch failed for id=%s: HTTP %d — %s",
                    places_id, e.response.status_code, e.response.text[:300])
        return {}
    except Exception as e:
        log.warning("Places fetch failed for id=%s: %s", places_id, e)
        return {}


def _map_review_to_article(review: dict, brand_id: str, places_id: str) -> dict | None:
    """Convert a single Google Places review dict to a pipeline article dict."""
    author = review.get("authorAttribution", {}).get("displayName", "")
    publish_time = review.get("publishTime", "")
    text_obj = review.get("text") or review.get("originalText") or {}
    body = text_obj.get("text", "").strip()
    rating = review.get("rating")

    if not body:
        return None

    # Build a title from the rating star representation
    stars = int(rating) if rating else 0
    star_str = f"{'★' * stars}{'☆' * (5 - stars)}" if stars else ""
    title = f"Google Review {star_str}".strip() if star_str else "Google Review"
    if len(title) > 200:
        title = title[:200]

    # Normalise publish_time to ISO 8601
    try:
        published_at = datetime.fromisoformat(
            publish_time.replace("Z", "+00:00")
        ).isoformat()
    except (ValueError, AttributeError):
        published_at = datetime.now(tz=timezone.utc).isoformat()

    return {
        "brand_id": brand_id,
        "content_hash": _content_hash(brand_id, author, publish_time),
        "story_hash": _content_hash(brand_id, places_id, publish_time),
        "portal_id": "google_business",
        "portal_name": "Google Business",
        "url": f"https://maps.google.com/?cid={places_id}",
        "title": title,
        "body": body[:2000],
        "author": author,
        "published_at": published_at,
        "language": "en",
        "source_type": "google_review",
        "source_credibility": 0.70,
        "is_regulatory_source": False,
        "reach_metadata": {
            "rating": rating,
            "places_id": places_id,
        },
    }


def collect_google_reviews_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 5 Google Business reviews for a brand.

    Returns an empty list when:
    - The ``GOOGLE_PLACES_API_KEY`` setting is not configured.
    - ``google_reviews_enabled`` is False in the brand config.
    - The Places API returns an error or no reviews.
    """
    api_key = settings.google_places_api_key
    if not api_key:
        log.warning("GOOGLE_PLACES_API_KEY not set in Railway Variables — skipping Google reviews for brand %s", brand_id[:8])
        return []

    if not config.get("google_reviews_enabled", False):
        return []

    brand_id = brand["id"]
    brand_name = brand.get("name", "")
    places_id = config.get("google_places_id", "").strip()

    # Resolve the Places ID if it is not already saved
    if not places_id:
        if not brand_name:
            log.warning("Brand %s has no name — cannot resolve Places ID", brand_id[:8])
            return []
        places_id = _resolve_places_id(brand_name, api_key)
        if not places_id:
            return []
        _save_places_id(brand_id, places_id)

    # Fetch place details + reviews
    place_data = _fetch_place_reviews(places_id, api_key)
    raw_reviews = place_data.get("reviews", [])

    if not raw_reviews:
        log.warning(
            "Brand %s: Places API returned no reviews for places_id=%s. "
            "If the key is valid, check that Google Places API (New) 'Advanced' plan is enabled — "
            "the free/Essentials plan does not return reviews.",
            brand_id[:8], places_id,
        )
        return []

    articles: list[dict] = []
    for review in raw_reviews[:_MAX_REVIEWS]:
        article = _map_review_to_article(review, brand_id, places_id)
        if article:
            articles.append(article)

    log.info("Brand %s: Google reviews collected %d items", brand_id[:8], len(articles))
    return articles
