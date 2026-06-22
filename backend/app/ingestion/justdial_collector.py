"""JustDial review collector — WAP endpoint scraping.

Hardening over v1:
- Full browser-like headers (Sec-Fetch-*, Referer, Accept-Encoding)
- 3-attempt retry with 2 s / 5 s delays on 429/503/502
- Tries both wap.justdial.com and m.justdial.com if first is blocked

brand_configs.justdial_listing_url: full URL, e.g.
  https://www.justdial.com/Chennai/Brand/044P...
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

_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.6367.82 Mobile Safari/537.36"
)
_HEADERS = {
    "User-Agent":              _MOBILE_UA,
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
    "Sec-CH-UA-Mobile":        "?1",
    "Referer":                 "https://www.google.com/",
}


def _content_hash(brand_id: str, author: str, published_at: str) -> str:
    return hashlib.sha256(f"{brand_id}:{author}:{published_at}".encode()).hexdigest()


def _to_wap(url: str) -> str:
    return url.replace("www.justdial.com", "wap.justdial.com")


def _to_m(url: str) -> str:
    return url.replace("www.justdial.com", "m.justdial.com")


def _fetch(url: str) -> httpx.Response | None:
    try:
        return httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
    except Exception as e:
        log.warning("JustDial: request error %s: %s", url, e)
        return None


def _fetch_with_retry(listing_url: str) -> httpx.Response | None:
    """Try wap → wap retry → m.justdial fallback."""
    wap_url = _to_wap(listing_url)
    m_url   = _to_m(listing_url)

    for attempt, url in enumerate([wap_url, wap_url, m_url]):
        if attempt > 0:
            time.sleep(_RETRY_DELAYS[attempt - 1] + random.uniform(0, 1))

        resp = _fetch(url)
        if resp is None:
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in _RETRY_STATUS:
            log.warning("JustDial: HTTP %d attempt %d — retrying", resp.status_code, attempt + 1)
            continue
        log.warning("JustDial: HTTP %d for %s", resp.status_code, url)
        return None

    return None


# ── parsers ────────────────────────────────────────────────────────────────

def _parse_json_ld(soup: BeautifulSoup) -> list[dict]:
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                for item in data:
                    if item.get("review"):
                        return item["review"]
            else:
                reviews = data.get("review")
                if reviews:
                    return reviews
        except Exception:
            continue
    return []


def _map_review(review: dict, brand_id: str, listing_url: str) -> dict | None:
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
            "story_hash":         _content_hash(brand_id, listing_url, published_raw),
            "portal_id":          "justdial",
            "portal_name":        "JustDial",
            "url":                listing_url,
            "title":              f"JustDial Review {star_str}".strip(),
            "body":               body[:2000],
            "author":             author,
            "published_at":       published_at,
            "language":           "en",
            "source_type":        "justdial_review",
            "source_credibility": 0.60,
            "is_regulatory_source": False,
            "reach_metadata":     {"rating": stars},
        }
    except Exception as e:
        log.warning("JustDial: map error: %s", e)
        return None


def _html_fallback(soup: BeautifulSoup, brand_id: str, listing_url: str) -> list[dict]:
    blocks = (
        soup.select("div[class*='ratedesc']")
        or soup.select("p[class*='review']")
        or soup.select("div[class*='review']")
    )
    articles = []
    for block in blocks[:_MAX_REVIEWS]:
        try:
            body = block.get_text(separator=" ").strip()
            if not body or len(body) < 15:
                continue
            published_at = datetime.now(tz=timezone.utc).isoformat()
            articles.append({
                "brand_id":           brand_id,
                "content_hash":       _content_hash(brand_id, "jd-anon", body[:40]),
                "story_hash":         _content_hash(brand_id, listing_url, body[:40]),
                "portal_id":          "justdial",
                "portal_name":        "JustDial",
                "url":                listing_url,
                "title":              "JustDial Review",
                "body":               body[:2000],
                "author":             "JustDial User",
                "published_at":       published_at,
                "language":           "en",
                "source_type":        "justdial_review",
                "source_credibility": 0.60,
                "is_regulatory_source": False,
                "reach_metadata":     {"rating": 0},
            })
        except Exception:
            continue
    return articles


# ── public entry point ─────────────────────────────────────────────────────

def collect_justdial_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 5 JustDial reviews. Returns [] on skip/error."""
    if not config.get("justdial_enabled", False):
        return []

    brand_id = brand["id"]
    listing_url = (config.get("justdial_listing_url") or "").strip()
    if not listing_url:
        log.warning("Brand %s: justdial_listing_url not set", brand_id[:8])
        return []

    resp = _fetch_with_retry(listing_url)
    if resp is None:
        log.warning("Brand %s: JustDial all attempts failed", brand_id[:8])
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    raw  = _parse_json_ld(soup)
    articles = [a for r in raw[:_MAX_REVIEWS] if (a := _map_review(r, brand_id, listing_url))]

    if not articles:
        articles = _html_fallback(soup, brand_id, listing_url)

    log.info("Brand %s: JustDial collected %d reviews", brand_id[:8], len(articles))
    return articles
