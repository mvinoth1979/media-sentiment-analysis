"""Team-BHP collector — searches team-bhp.com for each keyword and extracts
ownership reviews and road-test articles.

brand_configs.team_bhp_keywords: TEXT[] of model/sub-brand names
  e.g. ['Maruti Swift', 'Maruti Baleno', 'Maruti Grand Vitara']

For each keyword the collector:
  1. Searches https://www.team-bhp.com/?s={keyword}
  2. Collects up to 3 article cards per keyword (title + excerpt + URL)
  3. De-duplication is handled by content_hash as usual

source_type: "team_bhp_review"
source_credibility: 0.80 (community of experienced automotive enthusiasts)
"""

import hashlib
import logging
import random
import time
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_SEARCH_URL   = "https://www.team-bhp.com/?s={query}"
_TIMEOUT      = 20.0
_MAX_PER_KW   = 3     # articles per keyword
_RETRY_STATUS = {429, 502, 503}
_RETRY_DELAYS = [3.0, 7.0]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control":   "max-age=0",
    "Connection":      "keep-alive",
    "Sec-Fetch-Dest":  "document",
    "Sec-Fetch-Mode":  "navigate",
    "Sec-Fetch-Site":  "none",
    "Sec-Fetch-User":  "?1",
    "Referer":         "https://www.google.com/",
}


def _content_hash(brand_id: str, url: str) -> str:
    return hashlib.sha256(f"{brand_id}:tbhp:{url}".encode()).hexdigest()


def _fetch(url: str) -> httpx.Response | None:
    try:
        return httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
    except Exception as e:
        log.warning("Team-BHP: request error: %s", e)
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
            log.warning("Team-BHP: HTTP %d attempt %d — retrying", resp.status_code, attempt + 1)
            continue
        log.warning("Team-BHP: HTTP %d for %s", resp.status_code, url)
        return None
    return None


def _parse_search_results(soup: BeautifulSoup, keyword: str, brand_id: str) -> list[dict]:
    """Extract article cards from Team-BHP WordPress search results page."""
    articles: list[dict] = []

    # Team-BHP uses WordPress — standard article/entry structure
    cards = (
        soup.select("article.post")
        or soup.select("div.post")
        or soup.select("li.post")
        or soup.select("div[class*='entry']")
    )

    for card in cards[:_MAX_PER_KW]:
        try:
            # Title + URL
            title_el = (
                card.find("h2", class_=lambda c: c and "title" in c.lower())
                or card.find("h1", class_=lambda c: c and "title" in c.lower())
                or card.find("h2")
                or card.find("h3")
            )
            if not title_el:
                continue
            link_el = title_el.find("a") or card.find("a", href=True)
            if not link_el:
                continue

            title = title_el.get_text(separator=" ").strip()
            url   = link_el.get("href", "").strip()
            if not url or not url.startswith("http"):
                continue

            # Excerpt / body
            excerpt_el = (
                card.find(class_=lambda c: c and ("excerpt" in c.lower() or "summary" in c.lower()))
                or card.find("p")
            )
            body = (excerpt_el.get_text(separator=" ") if excerpt_el else "").strip()
            if not body:
                body = title  # fallback — title only

            # Date
            date_el = card.find("time") or card.find(class_=lambda c: c and "date" in c.lower())
            published_raw = date_el.get("datetime", "") if date_el else ""
            try:
                published_at = datetime.fromisoformat(
                    published_raw.replace("Z", "+00:00")
                ).isoformat()
            except (ValueError, AttributeError):
                published_at = datetime.now(tz=timezone.utc).isoformat()

            articles.append({
                "brand_id":           brand_id,
                "content_hash":       _content_hash(brand_id, url),
                "story_hash":         _content_hash(brand_id, url),
                "portal_id":          "team_bhp",
                "portal_name":        "Team-BHP",
                "url":                url,
                "title":              title[:300],
                "body":               body[:2000],
                "author":             "Team-BHP",
                "published_at":       published_at,
                "language":           "en",
                "source_type":        "team_bhp_review",
                "source_credibility": 0.80,
                "is_regulatory_source": False,
                "reach_metadata":     {"keyword": keyword},
            })
        except Exception as e:
            log.debug("Team-BHP: card parse error: %s", e)
            continue

    return articles


def collect_teambhp_for_brand(brand: dict, config: dict) -> list[dict]:
    """Search Team-BHP for each configured keyword and return articles.

    Returns [] when team_bhp_enabled is False or keywords list is empty.
    """
    if not config.get("team_bhp_enabled", False):
        return []

    brand_id = brand["id"]
    keywords: list[str] = config.get("team_bhp_keywords") or []
    if not keywords:
        log.warning("Brand %s: team_bhp_keywords is empty", brand_id[:8])
        return []

    all_articles: list[dict] = []
    seen_urls: set[str] = set()

    for keyword in keywords:
        query = keyword.strip()
        if not query:
            continue

        search_url = _SEARCH_URL.format(query=query.replace(" ", "+"))
        resp = _fetch_with_retry(search_url)
        if resp is None:
            log.warning("Brand %s: Team-BHP search failed for '%s'", brand_id[:8], keyword)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        cards = _parse_search_results(soup, keyword, brand_id)

        for article in cards:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                all_articles.append(article)

        # Polite delay between keyword searches
        if keywords.index(keyword) < len(keywords) - 1:
            time.sleep(1.5 + random.uniform(0, 1))

    log.info(
        "Brand %s: Team-BHP collected %d articles across %d keywords",
        brand_id[:8], len(all_articles), len(keywords),
    )
    return all_articles
