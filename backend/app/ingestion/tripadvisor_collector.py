"""TripAdvisor review collector — public listing page scraping.

TripAdvisor embeds review data as JSON-LD (primary) and also in
window.__WEB_CONTEXT__ / __SERVER_DATA__ scripts (fallback).

brand_configs.tripadvisor_listing_url: full listing page URL, e.g.
  https://www.tripadvisor.in/Attraction_Review-g297679-d3440016-...

source_type: "tripadvisor_review"
source_credibility: 0.82
"""

import hashlib
import json
import logging
import random
import re
import time
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_TIMEOUT      = 25.0
_MAX_REVIEWS  = 10
_RETRY_STATUS = {429, 502, 503}
_RETRY_DELAYS = [3.0, 8.0]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control":   "max-age=0",
    "Connection":      "keep-alive",
    "Sec-Fetch-Dest":  "document",
    "Sec-Fetch-Mode":  "navigate",
    "Sec-Fetch-Site":  "none",
    "Sec-Fetch-User":  "?1",
    "Referer":         "https://www.google.com/",
}


def _content_hash(brand_id: str, review_id: str) -> str:
    return hashlib.sha256(f"{brand_id}:ta:{review_id}".encode()).hexdigest()


# ── fetch ──────────────────────────────────────────────────────────────────

def _fetch(url: str) -> httpx.Response | None:
    try:
        return httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
    except Exception as e:
        log.warning("TripAdvisor: request error: %s", e)
        return None


def _fetch_with_retry(url: str) -> httpx.Response | None:
    for attempt in range(3):
        if attempt > 0:
            time.sleep(_RETRY_DELAYS[attempt - 1] + random.uniform(0, 1))
        resp = _fetch(url)
        if resp is None:
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in _RETRY_STATUS:
            log.warning("TripAdvisor: HTTP %d attempt %d — retrying", resp.status_code, attempt + 1)
            continue
        log.warning("TripAdvisor: HTTP %d for %s", resp.status_code, url)
        return None
    return None


# ── parsers ────────────────────────────────────────────────────────────────

def _extract_json_ld_reviews(soup: BeautifulSoup) -> list[dict]:
    """Primary: JSON-LD <script type='application/ld+json'> blocks."""
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


def _extract_server_data_reviews(soup: BeautifulSoup) -> list[dict]:
    """Fallback: TripAdvisor embeds review data in a window.__SERVER_DATA__ script."""
    for tag in soup.find_all("script"):
        text = tag.string or ""
        if "window.__SERVER_DATA__" not in text and "__WEB_CONTEXT__" not in text:
            continue
        # Extract the JSON payload assigned to the variable
        match = re.search(r'window\.__(?:SERVER_DATA|WEB_CONTEXT)__\s*=\s*(\{.*?\});?\s*(?:window|$)',
                          text, re.DOTALL)
        if not match:
            # Try greedy extraction
            start = text.find("{")
            if start == -1:
                continue
            try:
                data = json.loads(text[start:])
            except Exception:
                continue
        else:
            try:
                data = json.loads(match.group(1))
            except Exception:
                continue

        # Walk the nested structure to find reviews array
        def _find_reviews(obj: object, depth: int = 0) -> list[dict]:
            if depth > 6:
                return []
            if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "rating" in obj[0]:
                return obj
            if isinstance(obj, dict):
                if "reviews" in obj and isinstance(obj["reviews"], list):
                    return obj["reviews"]
                for v in obj.values():
                    result = _find_reviews(v, depth + 1)
                    if result:
                        return result
            return []

        reviews = _find_reviews(data)
        if reviews:
            return reviews

    return []


def _map_json_ld_review(review: dict, brand_id: str, listing_url: str) -> dict | None:
    try:
        rating    = int(float((review.get("reviewRating") or {}).get("ratingValue") or 0))
        body      = (review.get("reviewBody") or review.get("description") or "").strip()
        title_raw = (review.get("name") or review.get("headline") or "").strip()
        author    = (
            (review.get("author") or {}).get("name", "")
            if isinstance(review.get("author"), dict)
            else str(review.get("author", ""))
        )
        date_raw  = review.get("datePublished") or review.get("dateCreated") or ""

        full_body = f"{title_raw}\n\n{body}".strip() if title_raw else body
        if not full_body:
            return None

        try:
            published_at = datetime.fromisoformat(
                date_raw.replace("Z", "+00:00")
            ).isoformat()
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc).isoformat()

        review_id = review.get("@id") or (author + date_raw)
        star_str  = f"{'★' * rating}{'☆' * (5 - rating)}" if rating else ""

        return {
            "brand_id":           brand_id,
            "content_hash":       _content_hash(brand_id, review_id),
            "story_hash":         _content_hash(brand_id, listing_url + date_raw),
            "portal_id":          "tripadvisor",
            "portal_name":        "TripAdvisor",
            "url":                listing_url,
            "title":              f"TripAdvisor Review {star_str}".strip(),
            "body":               full_body[:2000],
            "author":             author,
            "published_at":       published_at,
            "language":           "en",
            "source_type":        "tripadvisor_review",
            "source_credibility": 0.82,
            "is_regulatory_source": False,
            "reach_metadata":     {"rating": rating},
        }
    except Exception as e:
        log.warning("TripAdvisor: map error: %s", e)
        return None


def _map_server_review(review: dict, brand_id: str, listing_url: str) -> dict | None:
    """Map a review dict from __SERVER_DATA__ (slightly different schema)."""
    try:
        rating    = int(float(review.get("rating") or review.get("bubbleRating") or 0))
        body      = (review.get("text") or review.get("body") or review.get("reviewBody") or "").strip()
        title_raw = (review.get("title") or review.get("headline") or "").strip()
        author    = (review.get("username") or review.get("userProfile", {}).get("displayName", "")
                     or "TripAdvisor User")
        date_raw  = (review.get("publishedDate") or review.get("travelDate") or
                     review.get("createdOn") or "")
        review_id = str(review.get("id") or review.get("reviewId") or "")

        full_body = f"{title_raw}\n\n{body}".strip() if title_raw else body
        if not full_body:
            return None

        try:
            published_at = datetime.fromisoformat(
                date_raw.replace("Z", "+00:00")
            ).isoformat()
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc).isoformat()

        star_str = f"{'★' * rating}{'☆' * (5 - rating)}" if rating else ""

        return {
            "brand_id":           brand_id,
            "content_hash":       _content_hash(brand_id, review_id or full_body[:40]),
            "story_hash":         _content_hash(brand_id, listing_url + date_raw),
            "portal_id":          "tripadvisor",
            "portal_name":        "TripAdvisor",
            "url":                listing_url,
            "title":              f"TripAdvisor Review {star_str}".strip(),
            "body":               full_body[:2000],
            "author":             author,
            "published_at":       published_at,
            "language":           "en",
            "source_type":        "tripadvisor_review",
            "source_credibility": 0.82,
            "is_regulatory_source": False,
            "reach_metadata":     {"rating": rating},
        }
    except Exception as e:
        log.warning("TripAdvisor: server-data map error: %s", e)
        return None


# ── public entry point ─────────────────────────────────────────────────────

def collect_tripadvisor_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect up to 10 TripAdvisor reviews. Returns [] on skip/error."""
    if not config.get("tripadvisor_enabled", False):
        return []

    brand_id = brand["id"]
    listing_url = (config.get("tripadvisor_listing_url") or "").strip()
    if not listing_url:
        log.warning("Brand %s: tripadvisor_listing_url not set", brand_id[:8])
        return []

    resp = _fetch_with_retry(listing_url)
    if resp is None:
        log.warning("Brand %s: TripAdvisor all attempts failed", brand_id[:8])
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    # 1. JSON-LD (most reliable)
    raw = _extract_json_ld_reviews(soup)
    articles = [a for r in raw[:_MAX_REVIEWS] if (a := _map_json_ld_review(r, brand_id, listing_url))]

    # 2. __SERVER_DATA__ / __WEB_CONTEXT__ fallback
    if not articles:
        raw2 = _extract_server_data_reviews(soup)
        articles = [a for r in raw2[:_MAX_REVIEWS] if (a := _map_server_review(r, brand_id, listing_url))]

    log.info("Brand %s: TripAdvisor collected %d reviews", brand_id[:8], len(articles))
    return articles
