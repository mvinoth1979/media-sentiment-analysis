"""Trustpilot review collector — scrapes the public review page.

No API key required. Trustpilot embeds review data as JSON in a
<script id="__NEXT_DATA__"> block on https://www.trustpilot.com/review/{domain}.

Returns [] when:
- trustpilot_enabled is False
- trustpilot_domain is not set
- page returns non-200 or JSON structure changes
"""

import hashlib
import json
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_BASE_URL  = "https://www.trustpilot.com/review"
_TIMEOUT   = 20.0
_MAX_REVIEWS = 20
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _content_hash(brand_id: str, review_id: str) -> str:
    raw = f"{brand_id}:tp:{review_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _fetch_page(domain: str) -> list[dict]:
    """Fetch public Trustpilot review page and extract reviews from __NEXT_DATA__."""
    url = f"{_BASE_URL}/{domain}"
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
    except Exception as e:
        log.warning("Trustpilot: HTTP error for '%s': %s", domain, e)
        return []

    if resp.status_code != 200:
        log.warning("Trustpilot: HTTP %d for '%s'", resp.status_code, domain)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        log.warning("Trustpilot: __NEXT_DATA__ not found for '%s'", domain)
        return []

    try:
        data = json.loads(tag.string)
    except json.JSONDecodeError as e:
        log.warning("Trustpilot: JSON parse error for '%s': %s", domain, e)
        return []

    # Path: props.pageProps.reviews (standard Next.js SSR hydration)
    reviews = (
        data.get("props", {})
            .get("pageProps", {})
            .get("reviews", [])
    )
    if not reviews:
        log.info("Trustpilot: 0 reviews in __NEXT_DATA__ for '%s'", domain)
    return reviews


def _map_review(review: dict, brand_id: str, domain: str) -> dict | None:
    review_id = review.get("id") or ""
    body = (review.get("text") or "").strip()
    title_text = (review.get("title") or "").strip()
    stars = int((review.get("rating") or {}).get("value") or 0)
    author = (review.get("consumer") or {}).get("displayName", "Anonymous")
    published_raw = (review.get("dates") or {}).get("publishedDate", "")

    if not body and not title_text:
        return None

    full_body = f"{title_text}\n\n{body}".strip() if title_text else body

    try:
        published_at = datetime.fromisoformat(
            published_raw.replace("Z", "+00:00")
        ).isoformat()
    except (ValueError, AttributeError):
        published_at = datetime.now(tz=timezone.utc).isoformat()

    star_str = f"{'★' * stars}{'☆' * (5 - stars)}" if stars else ""
    display_title = f"Trustpilot Review {star_str}".strip()

    return {
        "brand_id":           brand_id,
        "content_hash":       _content_hash(brand_id, review_id or (author + published_raw)),
        "story_hash":         _content_hash(brand_id, domain + published_raw),
        "portal_id":          "trustpilot",
        "portal_name":        "Trustpilot",
        "url":                f"https://www.trustpilot.com/review/{domain}",
        "title":              display_title,
        "body":               full_body[:2000],
        "author":             author,
        "published_at":       published_at,
        "language":           "en",
        "source_type":        "trustpilot_review",
        "source_credibility": 0.80,
        "is_regulatory_source": False,
        "reach_metadata":     {"rating": stars},
    }


def collect_trustpilot_for_brand(brand: dict, config: dict) -> list[dict]:
    """Scrape up to 20 Trustpilot reviews for a brand.

    Returns [] when trustpilot_enabled is False or trustpilot_domain is missing.
    No API key required — uses public page scraping.
    """
    if not config.get("trustpilot_enabled", False):
        return []

    brand_id = brand["id"]
    domain = (config.get("trustpilot_domain") or "").strip()
    if not domain:
        log.warning("Brand %s: trustpilot_domain not set", brand_id[:8])
        return []

    raw_reviews = _fetch_page(domain)
    articles: list[dict] = []
    for review in raw_reviews[:_MAX_REVIEWS]:
        article = _map_review(review, brand_id, domain)
        if article:
            articles.append(article)

    log.info("Brand %s: Trustpilot scraped %d reviews from '%s'", brand_id[:8], len(articles), domain)
    return articles
