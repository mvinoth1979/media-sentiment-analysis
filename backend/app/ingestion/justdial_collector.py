"""JustDial review collector using WAP endpoint scraping.

brand_configs.justdial_listing_url is the full JustDial business URL.
The WAP version (wap.justdial.com) is lighter and more scrapeable.

Returns up to 5 reviews.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_TIMEOUT = 15.0
_MAX_REVIEWS = 5
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Mobile Safari/537.36",
    "Accept": "text/html",
}


def _content_hash(brand_id: str, author: str, published_at: str) -> str:
    raw = f"{brand_id}:{author}:{published_at}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _to_wap_url(listing_url: str) -> str:
    return listing_url.replace("www.justdial.com", "wap.justdial.com")


def _parse_json_ld(soup: BeautifulSoup) -> list[dict]:
    script = soup.find("script", {"type": "application/ld+json"})
    if not script:
        return []
    try:
        data = json.loads(script.string or "")
        # May be a LocalBusiness or Product with review array
        if isinstance(data, list):
            for item in data:
                if item.get("review"):
                    return item["review"]
            return []
        return data.get("review") or []
    except Exception:
        return []


def _map_json_ld_review(review: dict, brand_id: str, listing_url: str) -> dict | None:
    try:
        stars = int(float((review.get("reviewRating") or {}).get("ratingValue") or 0))
        body = (review.get("reviewBody") or "").strip()
        author = (review.get("author") or {}).get("name", "")
        published_at_raw = review.get("datePublished", "")

        if not body:
            return None

        try:
            published_at = datetime.fromisoformat(published_at_raw).isoformat()
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc).isoformat()

        star_str = f"{'★' * stars}{'☆' * (5 - stars)}"
        title = f"JustDial Review {star_str}"

        return {
            "brand_id": brand_id,
            "content_hash": _content_hash(brand_id, author, published_at_raw),
            "story_hash": _content_hash(brand_id, listing_url, published_at_raw),
            "portal_id": "justdial",
            "portal_name": "JustDial",
            "url": listing_url,
            "title": title,
            "body": body[:2000],
            "author": author,
            "published_at": published_at,
            "language": "en",
            "source_type": "justdial_review",
            "source_credibility": 0.60,
            "is_regulatory_source": False,
            "reach_metadata": {"rating": stars},
        }
    except Exception as e:
        log.warning("JustDial: failed to map JSON-LD review: %s", e)
        return None


def collect_justdial_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 5 JustDial reviews for a brand.

    Returns [] when justdial_enabled is False, listing_url is missing,
    or any HTTP/parse error occurs (very common — bot detection).
    """
    brand_id = brand["id"]

    if not config.get("justdial_enabled", False):
        return []

    listing_url = (config.get("justdial_listing_url") or "").strip()
    if not listing_url:
        log.warning("Brand %s: justdial_listing_url not set", brand_id[:8])
        return []

    wap_url = _to_wap_url(listing_url)
    try:
        resp = httpx.get(wap_url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if resp.status_code != 200:
            log.warning("JustDial: HTTP %d for brand %s", resp.status_code, brand_id[:8])
            return []

        soup = BeautifulSoup(resp.text, "lxml")

        # Primary: JSON-LD
        raw_reviews = _parse_json_ld(soup)
        articles: list[dict] = []
        for review in raw_reviews[:_MAX_REVIEWS]:
            article = _map_json_ld_review(review, brand_id, listing_url)
            if article:
                articles.append(article)

        if articles:
            log.info("Brand %s: JustDial collected %d reviews (JSON-LD)", brand_id[:8], len(articles))
            return articles

        # Fallback: HTML selectors for WAP page structure
        review_blocks = (
            soup.select("div[class*='ratedesc']")
            or soup.select("p[class*='review']")
            or soup.select("span[class*='ratingstar']")
        )
        for block in review_blocks[:_MAX_REVIEWS]:
            try:
                body = block.get_text(separator=" ").strip()
                if not body or len(body) < 10:
                    continue
                published_at = datetime.now(tz=timezone.utc).isoformat()
                article = {
                    "brand_id": brand_id,
                    "content_hash": _content_hash(brand_id, "anonymous", body[:40]),
                    "story_hash": _content_hash(brand_id, listing_url, body[:40]),
                    "portal_id": "justdial",
                    "portal_name": "JustDial",
                    "url": listing_url,
                    "title": "JustDial Review",
                    "body": body[:2000],
                    "author": "JustDial User",
                    "published_at": published_at,
                    "language": "en",
                    "source_type": "justdial_review",
                    "source_credibility": 0.60,
                    "is_regulatory_source": False,
                    "reach_metadata": {"rating": 0},
                }
                articles.append(article)
            except Exception:
                continue

        log.info("Brand %s: JustDial collected %d reviews (HTML fallback)", brand_id[:8], len(articles))
        return articles
    except Exception as e:
        log.warning("JustDial: scrape failed for brand %s: %s", brand_id[:8], e)
        return []
