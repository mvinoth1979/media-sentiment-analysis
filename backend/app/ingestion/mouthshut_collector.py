"""MouthShut review collector — httpx + BeautifulSoup scraping.

Hardening over v1:
- Full browser-like headers (Sec-Fetch-*, Referer, Accept-Encoding)
- 3-attempt retry with 2 s / 5 s delays on 429/503/502
- Mobile-URL fallback (m.mouthshut.com) if desktop URL is blocked

brand_configs.mouthshut_slug: e.g. "amul-dairy-reviews-925925714"
URL:  https://www.mouthshut.com/product-reviews/{slug}
"""

import hashlib
import json
import logging
import random
import time
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_TIMEOUT     = 20.0
_MAX_REVIEWS = 5
_RETRY_STATUS = {429, 502, 503}
_RETRY_DELAYS = [2.0, 5.0]

_DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.6367.82 Mobile Safari/537.36"
)

_COMMON_HEADERS = {
    "Accept":                  "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language":         "en-IN,en;q=0.9",
    "Accept-Encoding":         "gzip, deflate, br",
    "Cache-Control":           "max-age=0",
    "Connection":              "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest":          "document",
    "Sec-Fetch-Mode":          "navigate",
    "Sec-Fetch-Site":          "none",
    "Sec-Fetch-User":          "?1",
    "Referer":                 "https://www.google.com/",
}


def _desktop_headers() -> dict:
    return {**_COMMON_HEADERS, "User-Agent": _DESKTOP_UA}


def _mobile_headers() -> dict:
    return {
        **_COMMON_HEADERS,
        "User-Agent": _MOBILE_UA,
        "Sec-CH-UA-Mobile": "?1",
    }


def _fetch(url: str, headers: dict) -> httpx.Response | None:
    """Single attempt — returns Response or None on exception."""
    try:
        return httpx.get(url, headers=headers, timeout=_TIMEOUT, follow_redirects=True)
    except Exception as e:
        log.warning("MouthShut: request error %s: %s", url, e)
        return None


def _fetch_with_retry(slug: str) -> httpx.Response | None:
    """Try desktop URL with retries, then mobile URL as fallback."""
    desktop_url = f"https://www.mouthshut.com/product-reviews/{slug}"
    mobile_url  = f"https://m.mouthshut.com/product-reviews/{slug}"

    for attempt, (url, headers) in enumerate([
        (desktop_url, _desktop_headers()),
        (desktop_url, _desktop_headers()),   # retry same URL
        (mobile_url,  _mobile_headers()),    # mobile fallback
    ]):
        if attempt > 0:
            delay = _RETRY_DELAYS[attempt - 1] + random.uniform(0, 1)
            time.sleep(delay)

        resp = _fetch(url, headers)
        if resp is None:
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in _RETRY_STATUS:
            log.warning("MouthShut: HTTP %d on attempt %d for slug=%s — retrying", resp.status_code, attempt + 1, slug)
            continue
        log.warning("MouthShut: HTTP %d for slug=%s", resp.status_code, slug)
        return None  # 403/404 — no point retrying

    return None


# ── parsers ────────────────────────────────────────────────────────────────

def _content_hash(brand_id: str, author: str, published_at: str) -> str:
    return hashlib.sha256(f"{brand_id}:{author}:{published_at}".encode()).hexdigest()


def _parse_json_ld(soup: BeautifulSoup) -> list[dict]:
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                for item in data:
                    if item.get("review"):
                        return item["review"]
            elif data.get("@type") in ("Product", "Organization") and data.get("review"):
                return data["review"]
        except Exception:
            continue
    return []


def _map_review(review: dict, brand_id: str, slug: str) -> dict | None:
    try:
        stars = int(float((review.get("reviewRating") or {}).get("ratingValue") or 0))
        body  = (review.get("reviewBody") or "").strip()
        author = (review.get("author") or {}).get("name", "") if isinstance(review.get("author"), dict) else str(review.get("author", ""))
        published_raw = review.get("datePublished", "")
        if not body:
            return None
        try:
            published_at = datetime.fromisoformat(published_raw).isoformat()
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc).isoformat()
        star_str = f"{'★' * stars}{'☆' * (5 - stars)}"
        return {
            "brand_id":           brand_id,
            "content_hash":       _content_hash(brand_id, author, published_raw),
            "story_hash":         _content_hash(brand_id, slug, published_raw),
            "portal_id":          "mouthshut",
            "portal_name":        "MouthShut",
            "url":                f"https://www.mouthshut.com/product-reviews/{slug}",
            "title":              f"MouthShut Review {star_str}".strip(),
            "body":               body[:2000],
            "author":             author,
            "published_at":       published_at,
            "language":           "en",
            "source_type":        "mouthshut_review",
            "source_credibility": 0.65,
            "is_regulatory_source": False,
            "reach_metadata":     {"rating": stars},
        }
    except Exception as e:
        log.warning("MouthShut: map error: %s", e)
        return None


def _html_fallback(soup: BeautifulSoup, brand_id: str, slug: str) -> list[dict]:
    url = f"https://www.mouthshut.com/product-reviews/{slug}"
    blocks = (
        soup.select("div.reviewsList div.review")
        or soup.select("div[class*='review-block']")
        or soup.select("div[class*='review']")
    )
    articles = []
    for block in blocks[:_MAX_REVIEWS]:
        try:
            body_el = block.find("p") or block
            body = (body_el.get_text(separator=" ") or "").strip()
            if not body or len(body) < 15:
                continue
            author_el = block.find(class_=lambda c: c and "author" in c.lower())
            author = author_el.get_text().strip() if author_el else "Anonymous"
            published_at = datetime.now(tz=timezone.utc).isoformat()
            articles.append({
                "brand_id":           brand_id,
                "content_hash":       _content_hash(brand_id, author, body[:40]),
                "story_hash":         _content_hash(brand_id, slug, body[:40]),
                "portal_id":          "mouthshut",
                "portal_name":        "MouthShut",
                "url":                url,
                "title":              "MouthShut Review",
                "body":               body[:2000],
                "author":             author,
                "published_at":       published_at,
                "language":           "en",
                "source_type":        "mouthshut_review",
                "source_credibility": 0.65,
                "is_regulatory_source": False,
                "reach_metadata":     {"rating": 0},
            })
        except Exception:
            continue
    return articles


# ── public entry point ─────────────────────────────────────────────────────

def collect_mouthshut_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 5 MouthShut reviews. Returns [] on skip/error."""
    if not config.get("mouthshut_enabled", False):
        return []

    brand_id = brand["id"]
    slug = (config.get("mouthshut_slug") or "").strip()
    if not slug:
        log.warning("Brand %s: mouthshut_slug not set", brand_id[:8])
        return []

    resp = _fetch_with_retry(slug)
    if resp is None:
        log.warning("Brand %s: MouthShut all attempts failed for slug=%s", brand_id[:8], slug)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    raw  = _parse_json_ld(soup)
    articles = [a for r in raw[:_MAX_REVIEWS] if (a := _map_review(r, brand_id, slug))]

    if not articles:
        articles = _html_fallback(soup, brand_id, slug)

    log.info("Brand %s: MouthShut collected %d reviews (slug=%s)", brand_id[:8], len(articles), slug)
    return articles
