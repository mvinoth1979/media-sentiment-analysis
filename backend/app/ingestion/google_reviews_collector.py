"""Google Business Reviews collector using Places API (New) v1.

Strategy:
- Uses places.googleapis.com/v1/places:searchText and /v1/places/{id}
  (the new API, required for Google Cloud projects created after 2024).
- Fetches up to 5 reviews per run; content_hash deduplication prevents
  re-storing reviews already in the DB.

Requires in Google Cloud Console:
  APIs & Services → Enable → "Places API (New)"  (places.googleapis.com)
  Billing must be active.  Reviews field costs ~$0.035/request (Advanced SKU).

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

_TEXTSEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_DETAILS_BASE   = "https://places.googleapis.com/v1/places"
_TIMEOUT        = 12.0
_MAX_REVIEWS    = 5


def _content_hash(brand_id: str, author: str, publish_key: str) -> str:
    raw = f"{brand_id}:{author}:{publish_key}"
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
    """Text-search via Places API (New) to get a place ID for a brand name."""
    try:
        resp = httpx.post(
            _TEXTSEARCH_URL,
            json={"textQuery": brand_name},
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "places.id,places.displayName",
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            err = data["error"]
            log.warning("Places text search '%s': %d %s", brand_name, err.get("code"), err.get("message", ""))
            return None
        places = data.get("places", [])
        if not places:
            log.warning("Places text search '%s': no results", brand_name)
            return None
        pid = places[0].get("id", "")
        log.info("Resolved '%s' to place_id=%s", brand_name, pid)
        return pid or None
    except Exception as e:
        log.warning("Places text search failed for '%s': %s", brand_name, e)
        return None


def _fetch_place_reviews(places_id: str, api_key: str) -> list[dict]:
    """Call Place Details (New) to get up to 5 most recent reviews."""
    try:
        resp = httpx.get(
            f"{_DETAILS_BASE}/{places_id}",
            params={"languageCode": "en"},
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "id,displayName,rating,userRatingCount,reviews",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            err = data["error"]
            log.warning(
                "Places Details API error %d for place_id=%s: %s",
                err.get("code"), places_id, err.get("message", ""),
            )
            return []

        reviews = data.get("reviews", [])
        if not reviews:
            log.info("place_id=%s: no reviews returned", places_id)
        return reviews

    except httpx.HTTPStatusError as e:
        log.warning("Places Details HTTP %d for place_id=%s — %s",
                    e.response.status_code, places_id, e.response.text[:300])
        return []
    except Exception as e:
        log.warning("Places Details failed for place_id=%s: %s", places_id, e)
        return []


def _map_review(review: dict, brand_id: str, places_id: str) -> dict | None:
    """Convert a Places API (New) review dict to a pipeline article dict."""
    author      = review.get("authorAttribution", {}).get("displayName", "")
    rating      = review.get("rating")
    body        = (review.get("text", {}).get("text") or "").strip()
    publish_iso = review.get("publishTime", "")
    relative    = review.get("relativePublishTimeDescription", "")

    if not body:
        return None

    if publish_iso:
        try:
            published_at = datetime.fromisoformat(publish_iso.replace("Z", "+00:00")).isoformat()
            publish_key  = publish_iso
        except (ValueError, TypeError):
            published_at = datetime.now(tz=timezone.utc).isoformat()
            publish_key  = body[:40]
    else:
        published_at = datetime.now(tz=timezone.utc).isoformat()
        publish_key  = body[:40]

    stars    = int(rating) if rating else 0
    star_str = f"{'★' * stars}{'☆' * (5 - stars)}" if stars else ""
    title    = f"Google Review {star_str}".strip() if star_str else "Google Review"

    return {
        "brand_id":          brand_id,
        "content_hash":      _content_hash(brand_id, author, publish_key),
        "story_hash":        _content_hash(brand_id, places_id, publish_key),
        "portal_id":         "google_business",
        "portal_name":       "Google Business",
        "url":               f"https://maps.google.com/?cid={places_id}",
        "title":             title,
        "body":              body[:2000],
        "author":            author,
        "published_at":      published_at,
        "language":          "en",
        "source_type":       "google_review",
        "source_credibility": 0.70,
        "is_regulatory_source": False,
        "reach_metadata": {
            "rating":        rating,
            "places_id":     places_id,
            "relative_time": relative,
        },
    }


def collect_google_reviews_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 5 most recent Google Business reviews for a brand."""
    api_key   = settings.google_places_api_key
    brand_id  = brand["id"]
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
