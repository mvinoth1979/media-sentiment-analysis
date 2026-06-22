"""MouthShut review collector using web scraping (httpx + BeautifulSoup).

brand_configs.mouthshut_slug is the URL slug, e.g.:
  "amul-dairy-reviews-925925714"
-> fetches https://www.mouthshut.com/product-reviews/{slug}

Rate limit: 1 request per run (conservative to avoid IP blocks).
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}


def _content_hash(brand_id: str, author: str, published_at: str) -> str:
    raw = f"{brand_id}:{author}:{published_at}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _parse_json_ld(soup: BeautifulSoup) -> list[dict]:
    script = soup.find("script", {"type": "application/ld+json"})
    if not script:
        return []
    try:
        data = json.loads(script.string or "")
        if data.get("@type") != "Product":
            return []
        return data.get("review") or []
    except Exception:
        return []


def _map_json_ld_review(review: dict, brand_id: str, slug: str) -> dict | None:
    try:
        stars = int(float(review.get("reviewRating", {}).get("ratingValue") or 0))
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
        title = f"MouthShut Review {star_str}"

        return {
            "brand_id": brand_id,
            "content_hash": _content_hash(brand_id, author, published_at_raw),
            "story_hash": _content_hash(brand_id, slug, published_at_raw),
            "portal_id": "mouthshut",
            "portal_name": "MouthShut",
            "url": f"https://www.mouthshut.com/product-reviews/{slug}",
            "title": title,
            "body": body[:2000],
            "author": author,
            "published_at": published_at,
            "language": "en",
            "source_type": "mouthshut_review",
            "source_credibility": 0.65,
            "is_regulatory_source": False,
            "reach_metadata": {"rating": stars},
        }
    except Exception as e:
        log.warning("MouthShut: failed to map JSON-LD review: %s", e)
        return None


def collect_mouthshut_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 5 MouthShut reviews for a brand.

    Returns [] when mouthshut_enabled is False, slug is missing,
    or any HTTP/parse error occurs.
    """
    brand_id = brand["id"]

    if not config.get("mouthshut_enabled", False):
        return []

    slug = (config.get("mouthshut_slug") or "").strip()
    if not slug:
        log.warning("Brand %s: mouthshut_slug not set", brand_id[:8])
        return []

    url = f"https://www.mouthshut.com/product-reviews/{slug}"
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if resp.status_code != 200:
            log.warning("MouthShut: HTTP %d for brand %s slug=%s", resp.status_code, brand_id[:8], slug)
            return []

        soup = BeautifulSoup(resp.text, "lxml")

        # Primary: JSON-LD structured data
        raw_reviews = _parse_json_ld(soup)
        articles: list[dict] = []
        for review in raw_reviews[:_MAX_REVIEWS]:
            article = _map_json_ld_review(review, brand_id, slug)
            if article:
                articles.append(article)

        if articles:
            log.info("Brand %s: MouthShut collected %d reviews (JSON-LD)", brand_id[:8], len(articles))
            return articles

        # Fallback: HTML parsing — look for common review block selectors
        review_blocks = (
            soup.select("div.reviewsList div.review")
            or soup.select("div[class*='review']")
        )
        for block in review_blocks[:_MAX_REVIEWS]:
            try:
                body_el = block.find("p") or block
                body = (body_el.get_text(separator=" ") or "").strip()
                if not body or len(body) < 10:
                    continue
                author_el = block.find(class_=lambda c: c and "author" in c.lower())
                author = author_el.get_text().strip() if author_el else "Anonymous"
                published_at = datetime.now(tz=timezone.utc).isoformat()
                article = {
                    "brand_id": brand_id,
                    "content_hash": _content_hash(brand_id, author, body[:40]),
                    "story_hash": _content_hash(brand_id, slug, body[:40]),
                    "portal_id": "mouthshut",
                    "portal_name": "MouthShut",
                    "url": url,
                    "title": "MouthShut Review",
                    "body": body[:2000],
                    "author": author,
                    "published_at": published_at,
                    "language": "en",
                    "source_type": "mouthshut_review",
                    "source_credibility": 0.65,
                    "is_regulatory_source": False,
                    "reach_metadata": {"rating": 0},
                }
                articles.append(article)
            except Exception:
                continue

        log.info("Brand %s: MouthShut collected %d reviews (HTML fallback)", brand_id[:8], len(articles))
        return articles
    except Exception as e:
        log.warning("MouthShut: scrape failed for brand %s: %s", brand_id[:8], e)
        return []
