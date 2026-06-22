"""Google Business Reviews collector using the Places Details API (legacy).

Strategy:
- Uses maps.googleapis.com/maps/api/place/details/json (legacy endpoint).
  The legacy API returns up to 5 reviews under the standard Contact SKU —
  no Advanced SKU required. The same place_id format works for both APIs.
- Fetches with reviews_sort=newest so each run captures the most recent reviews.
- content_hash deduplication (in the orchestrator's filter_new_articles) prevents
  re-storing reviews already in the DB.
- Until the DB has sufficient reviews, every pipeline run naturally seeds all
  available reviews.  Once the DB is populated, only truly new reviews pass the
  dedup filter.

Requires in Google Cloud Console:
  APIs & Services → Enable → "Places API"  (the legacy one, not "Places API New")
  Billing must be active.  Cost: ~$0.017 per request (Contact SKU).

Returns [] gracefully when:
- GOOGLE_PLACES_API_KEY is not set.
- google_reviews_enabled is False.
- The API returns an error or no reviews.
"""

import hashlib
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

log = logging.getLogger(__name__)

_LEGACY_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
_LEGACY_TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
_TIMEOUT = 12.0
_MAX_REVIEWS = 5


def _content_hash(brand_id: str, author: str, publish_time: str) -> str:
    raw = f"{brand_id}:{author}:{publish_time}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _save_places_id(brand_id: str, places_id: str) -> None:
    try:
        from app.storage.postgres import get_db
        db = get_db()
        db.table("brand_configs").update({"google_places_id": places_id}).eq("brand_id", brand_id).execute()
        log.info("Brand %s: saved resolved google_places_id=%s", brand_id[:8], places_id)
    except Exception as e:
        log.warning("Brand %s: could not save google_places_id: %s", brand_id[:8], e)


def _resolve_places_id(brand_name: str, api_key: str) -> str | None:
    """Text-search via legacy Places API to get a place_id for a brand name."""
    try:
        resp = httpx.get(
            _LEGACY_TEXTSEARCH_URL,
            params={"query": brand_name, "key": api_key},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK":
            log.warning("Places text search '%s': status=%s — %s",
                        brand_name, data.get("status"), data.get("error_message", ""))
            return None
        results = data.get("results", [])
        if not results:
            return None
        pid = results[0].get("place_id", "")
        log.info("Resolved '%s' to place_id=%s", brand_name, pid)
        return pid or None
    except Exception as e:
        log.warning("Places text search failed for '%s': %s", brand_name, e)
        return None


def _fetch_place_reviews(places_id: str, api_key: str) -> list[dict]:
    """Call legacy Place Details to get up to 5 most recent reviews."""
    try:
        resp = httpx.get(
            _LEGACY_DETAILS_URL,
            params={
                "place_id": places_id,
                "fields": "name,rating,reviews,user_ratings_total",
                "reviews_sort": "newest",
                "key": api_key,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "")

        if status == "REQUEST_DENIED":
            log.warning(
                "Places API REQUEST_DENIED for place_id=%s — "
                "Fix: Google Cloud Console → APIs & Services → Enable → 'Places API' (legacy). "
                "Error: %s",
                places_id, data.get("error_message", ""),
            )
            return []

        if status == "INVALID_REQUEST":
            log.warning("Places API INVALID_REQUEST for place_id=%s — %s",
                        places_id, data.get("error_message", ""))
            return []

        if status not in ("OK", "ZERO_RESULTS"):
            log.warning("Places API status=%s for place_id=%s — %s",
                        status, places_id, data.get("error_message", ""))
            return []

        reviews = data.get("result", {}).get("reviews", [])
        if not reviews:
            log.info("places_id=%s: no reviews returned (status=%s)", places_id, status)
        return reviews

    except httpx.HTTPStatusError as e:
        log.warning("Places Details HTTP %d for place_id=%s — %s",
                    e.response.status_code, places_id, e.response.text[:300])
        return []
    except Exception as e:
        log.warning("Places Details failed for place_id=%s: %s", places_id, e)
        return []


def _map_review(review: dict, brand_id: str, places_id: str) -> dict | None:
    """Convert a legacy Place Details review dict to a pipeline article dict."""
    author = review.get("author_name", "")
    rating = review.get("rating")
    body = (review.get("text") or "").strip()
    time_val = review.get("time")  # unix timestamp (int)
    relative_time = review.get("relative_time_description", "")

    if not body:
        return None

    # Convert unix timestamp → ISO 8601
    if time_val:
        try:
            published_at = datetime.fromtimestamp(int(time_val), tz=timezone.utc).isoformat()
            publish_key = str(time_val)
        except (ValueError, TypeError):
            published_at = datetime.now(tz=timezone.utc).isoformat()
            publish_key = body[:40]
    else:
        published_at = datetime.now(tz=timezone.utc).isoformat()
        publish_key = body[:40]

    stars = int(rating) if rating else 0
    star_str = f"{'★' * stars}{'☆' * (5 - stars)}" if stars else ""
    title = f"Google Review {star_str}".strip() if star_str else "Google Review"

    return {
        "brand_id": brand_id,
        "content_hash": _content_hash(brand_id, author, publish_key),
        "story_hash": _content_hash(brand_id, places_id, publish_key),
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
            "relative_time": relative_time,
        },
    }


def collect_google_reviews_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 5 most recent Google Business reviews for a brand.

    Deduplication happens upstream in filter_new_articles via content_hash,
    so repeated runs safely accumulate new reviews without duplicates.
    """
    api_key = settings.google_places_api_key
    brand_id = brand["id"]
    brand_name = brand.get("name", "")

    if not api_key:
        log.warning("GOOGLE_PLACES_API_KEY not set — skipping Google reviews for brand %s", brand_id[:8])
        return []

    if not config.get("google_reviews_enabled", False):
        return []

    places_id = (config.get("google_places_id") or "").strip()
    if not places_id:
        if not brand_name:
            log.warning("Brand %s: no google_places_id and no name — cannot resolve", brand_id[:8])
            return []
        places_id = _resolve_places_id(brand_name, api_key)
        if not places_id:
            return []
        _save_places_id(brand_id, places_id)

    raw_reviews = _fetch_place_reviews(places_id, api_key)
    articles: list[dict] = []
    for review in raw_reviews[:_MAX_REVIEWS]:
        article = _map_review(review, brand_id, places_id)
        if article:
            articles.append(article)

    log.info("Brand %s (%s): Google reviews collected %d / %d",
             brand_id[:8], brand_name, len(articles), len(raw_reviews))
    return articles
