"""Google Play Store reviews collector.

Uses google-play-scraper (no API key, completely free, no rate limits).
Fetches the latest N reviews for a brand's Android app.

Requires in brand_configs:
  play_store_enabled = true
  play_store_app_id  = "com.maruti.marutisuzuki"  (from the Play Store URL)

Returns [] gracefully when:
- play_store_enabled is False.
- play_store_app_id is not set.
- The app is not found or has no reviews.
"""

import hashlib
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

_MAX_REVIEWS = 10


def _content_hash(brand_id: str, key: str) -> str:
    return hashlib.sha256(f"{brand_id}:{key}".encode()).hexdigest()


def collect_playstore_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect latest Play Store reviews for a brand's Android app."""
    if not config.get("play_store_enabled", False):
        return []

    app_id     = (config.get("play_store_app_id") or "").strip()
    brand_id   = brand["id"]
    brand_name = brand.get("name", "")

    if not app_id:
        log.warning("Brand %s: play_store_enabled but play_store_app_id not set", brand_id[:8])
        return []

    try:
        from google_play_scraper import reviews as gps_reviews, Sort
        result, _ = gps_reviews(
            app_id,
            lang="en",
            country="in",
            sort=Sort.NEWEST,
            count=_MAX_REVIEWS,
        )
    except Exception as e:
        log.error("Play Store fetch failed for brand %s (app=%s): %s", brand_id[:8], app_id, e)
        return []

    articles: list[dict] = []
    for r in result:
        body = (r.get("content") or "").strip()
        if not body:
            continue

        review_id = r.get("reviewId") or ""
        rating    = r.get("score", 0)
        author    = r.get("userName", "Anonymous")
        at        = r.get("at")

        if at and hasattr(at, "astimezone"):
            published_at = at.astimezone(timezone.utc).isoformat()
            publish_key  = at.isoformat()
        else:
            published_at = datetime.now(tz=timezone.utc).isoformat()
            publish_key  = review_id or body[:40]

        stars    = int(rating) if rating else 0
        star_str = f"{'★' * stars}{'☆' * (5 - stars)}" if stars else ""
        title    = f"Play Store Review {star_str}".strip() if star_str else "Play Store Review"

        articles.append({
            "brand_id":           brand_id,
            "content_hash":       _content_hash(brand_id, review_id or publish_key),
            "story_hash":         _content_hash(brand_id, app_id + publish_key),
            "portal_id":          "google_play_store",
            "portal_name":        "Google Play Store",
            "url":                f"https://play.google.com/store/apps/details?id={app_id}",
            "title":              title,
            "body":               body[:2000],
            "author":             author,
            "published_at":       published_at,
            "language":           "en",
            "source_type":        "play_store_review",
            "source_credibility": 0.65,
            "is_regulatory_source": False,
            "reach_metadata": {
                "rating":      rating,
                "app_id":      app_id,
                "thumbs_up":   r.get("thumbsUpCount", 0),
                "app_version": r.get("reviewCreatedVersion", ""),
            },
        })

    log.info("Brand %s (%s): Play Store reviews collected %d / %d",
             brand_id[:8], brand_name, len(articles), len(result))
    return articles
