"""AmbitionBox employee review collector — public page scraping.

AmbitionBox is a Next.js app. Reviews are embedded in:
  1. <script id="__NEXT_DATA__"> JSON (primary)
  2. JSON-LD structured data (fallback)
  3. HTML selectors (last resort)

brand_configs.ambitionbox_slug: e.g. "tata-motors"
URL: https://www.ambitionbox.com/reviews/{slug}-reviews

source_type: "ambitionbox_review"
source_credibility: 0.70 (verified employee reviews)
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
_MAX_REVIEWS = 10
_RETRY_STATUS = {429, 502, 503}
_RETRY_DELAYS = [2.0, 5.0]

_DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_HEADERS = {
    "User-Agent":              _DESKTOP_UA,
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

_BASE_URL = "https://www.ambitionbox.com/reviews"


def _review_url(slug: str) -> str:
    """AmbitionBox review pages follow the pattern /reviews/{slug}-reviews."""
    return f"{_BASE_URL}/{slug}-reviews"


def _content_hash(brand_id: str, review_id: str) -> str:
    return hashlib.sha256(f"{brand_id}:ab:{review_id}".encode()).hexdigest()


# ── fetch ──────────────────────────────────────────────────────────────────

def _fetch(url: str) -> httpx.Response | None:
    try:
        return httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
    except Exception as e:
        log.warning("AmbitionBox: request error: %s", e)
        return None


def _fetch_with_retry(slug: str) -> httpx.Response | None:
    url = _review_url(slug)
    for attempt in range(3):
        if attempt > 0:
            time.sleep(_RETRY_DELAYS[attempt - 1] + random.uniform(0, 1))
        resp = _fetch(url)
        if resp is None:
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in _RETRY_STATUS:
            log.warning("AmbitionBox: HTTP %d attempt %d — retrying", resp.status_code, attempt + 1)
            continue
        log.warning("AmbitionBox: HTTP %d for slug=%s", resp.status_code, slug)
        return None
    return None


# ── parsers ────────────────────────────────────────────────────────────────

def _extract_next_data_reviews(soup: BeautifulSoup) -> list[dict]:
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        return []
    try:
        data = json.loads(tag.string)
        pp = data.get("props", {}).get("pageProps", {})
        # AmbitionBox nests reviews under several possible keys
        reviews = (
            pp.get("reviews")
            or pp.get("companyReviews")
            or pp.get("reviewsList")
            or []
        )
        if isinstance(reviews, dict):
            reviews = reviews.get("reviews") or reviews.get("data") or []
        return reviews if isinstance(reviews, list) else []
    except Exception as e:
        log.debug("AmbitionBox: __NEXT_DATA__ parse error: %s", e)
        return []


def _extract_json_ld_reviews(soup: BeautifulSoup) -> list[dict]:
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                for item in data:
                    if item.get("review"):
                        return item["review"]
            elif data.get("review"):
                return data["review"]
        except Exception:
            continue
    return []


def _map_next_data_review(review: dict, brand_id: str, slug: str) -> dict | None:
    """Map AmbitionBox __NEXT_DATA__ review dict."""
    try:
        review_id = str(review.get("id") or review.get("reviewId") or "")
        rating    = int(float(review.get("rating") or review.get("overallRating") or 0))
        title     = (review.get("title") or review.get("reviewHeadline") or "").strip()
        pros      = (review.get("pros") or review.get("goodThings") or "").strip()
        cons      = (review.get("cons") or review.get("improvements") or "").strip()
        body_raw  = (review.get("description") or review.get("reviewText") or "").strip()
        designation = (review.get("designation") or review.get("jobTitle") or "Employee").strip()
        date_raw  = (
            review.get("createdDate")
            or review.get("reviewDate")
            or review.get("datePublished")
            or ""
        )
        author = (review.get("reviewer") or {}).get("name", "") if isinstance(review.get("reviewer"), dict) else designation

        # Build body from whatever fields are present
        parts = []
        if title:
            parts.append(title)
        if pros:
            parts.append(f"Pros: {pros}")
        if cons:
            parts.append(f"Cons: {cons}")
        if body_raw:
            parts.append(body_raw)
        body = "\n".join(parts).strip()

        if not body:
            return None

        try:
            published_at = datetime.fromisoformat(date_raw.replace("Z", "+00:00")).isoformat()
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc).isoformat()

        star_str = f"{'★' * rating}{'☆' * (5 - rating)}" if rating else ""
        return {
            "brand_id":           brand_id,
            "content_hash":       _content_hash(brand_id, review_id or body[:40]),
            "story_hash":         _content_hash(brand_id, slug + (date_raw or body[:20])),
            "portal_id":          "ambitionbox",
            "portal_name":        "AmbitionBox",
            "url":                _review_url(slug),
            "title":              f"AmbitionBox Review {star_str} — {designation}".strip(),
            "body":               body[:2000],
            "author":             author or designation,
            "published_at":       published_at,
            "language":           "en",
            "source_type":        "ambitionbox_review",
            "source_credibility": 0.70,
            "is_regulatory_source": False,
            "reach_metadata":     {"rating": rating},
        }
    except Exception as e:
        log.warning("AmbitionBox: map error: %s", e)
        return None


def _map_json_ld_review(review: dict, brand_id: str, slug: str) -> dict | None:
    try:
        rating = int(float((review.get("reviewRating") or {}).get("ratingValue") or 0))
        body   = (review.get("reviewBody") or "").strip()
        author = (review.get("author") or {}).get("name", "Employee") if isinstance(review.get("author"), dict) else "Employee"
        date_raw = review.get("datePublished", "")
        if not body:
            return None
        try:
            published_at = datetime.fromisoformat(date_raw).isoformat()
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc).isoformat()
        star_str = f"{'★' * rating}{'☆' * (5 - rating)}" if rating else ""
        return {
            "brand_id":           brand_id,
            "content_hash":       _content_hash(brand_id, author + date_raw),
            "story_hash":         _content_hash(brand_id, slug + date_raw),
            "portal_id":          "ambitionbox",
            "portal_name":        "AmbitionBox",
            "url":                _review_url(slug),
            "title":              f"AmbitionBox Review {star_str}".strip(),
            "body":               body[:2000],
            "author":             author,
            "published_at":       published_at,
            "language":           "en",
            "source_type":        "ambitionbox_review",
            "source_credibility": 0.70,
            "is_regulatory_source": False,
            "reach_metadata":     {"rating": rating},
        }
    except Exception as e:
        log.warning("AmbitionBox: JSON-LD map error: %s", e)
        return None


def _html_fallback(soup: BeautifulSoup, brand_id: str, slug: str) -> list[dict]:
    blocks = (
        soup.select("[class*='reviewCard']")
        or soup.select("[class*='review-tile']")
        or soup.select("[data-testid*='review']")
        or soup.select("[class*='pros-cons']")
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
                "content_hash":       _content_hash(brand_id, body[:50]),
                "story_hash":         _content_hash(brand_id, slug + body[:30]),
                "portal_id":          "ambitionbox",
                "portal_name":        "AmbitionBox",
                "url":                _review_url(slug),
                "title":              "AmbitionBox Employee Review",
                "body":               body[:2000],
                "author":             "Employee",
                "published_at":       published_at,
                "language":           "en",
                "source_type":        "ambitionbox_review",
                "source_credibility": 0.70,
                "is_regulatory_source": False,
                "reach_metadata":     {"rating": 0},
            })
        except Exception:
            continue
    return articles


# ── public entry point ─────────────────────────────────────────────────────

def collect_ambitionbox_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 10 AmbitionBox employee reviews. Returns [] on skip/error."""
    if not config.get("ambitionbox_enabled", False):
        return []

    brand_id = brand["id"]
    slug = (config.get("ambitionbox_slug") or "").strip()
    if not slug:
        log.warning("Brand %s: ambitionbox_slug not set", brand_id[:8])
        return []

    resp = _fetch_with_retry(slug)
    if resp is None:
        log.warning("Brand %s: AmbitionBox all attempts failed for slug=%s", brand_id[:8], slug)
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    # 1. __NEXT_DATA__
    raw = _extract_next_data_reviews(soup)
    articles = [a for r in raw[:_MAX_REVIEWS] if (a := _map_next_data_review(r, brand_id, slug))]

    # 2. JSON-LD
    if not articles:
        raw_ld = _extract_json_ld_reviews(soup)
        articles = [a for r in raw_ld[:_MAX_REVIEWS] if (a := _map_json_ld_review(r, brand_id, slug))]

    # 3. HTML fallback
    if not articles:
        articles = _html_fallback(soup, brand_id, slug)

    log.info("Brand %s: AmbitionBox collected %d reviews (slug=%s)", brand_id[:8], len(articles), slug)
    return articles
