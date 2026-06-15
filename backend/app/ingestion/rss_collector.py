import re
import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import feedparser


def keyword_matches(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        pattern = kw if kw.startswith("\\b") else re.escape(kw.lower())
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def _parse_date(entry) -> datetime:
    raw = entry.get("published") or entry.get("updated", "")
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def collect_portal(portal: dict, keywords: list[str], brand_id: str) -> list[dict]:
    try:
        feed = feedparser.parse(portal["rss_url"])
    except Exception:
        return []

    articles = []
    for entry in feed.entries:
        title = getattr(entry, "title", "") or ""
        body = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "")
        combined = f"{title} {body}"

        if not keyword_matches(combined, keywords):
            continue

        url = entry.get("link", "")
        content_hash = hashlib.sha256(f"{portal['id']}::{url}".encode()).hexdigest()

        articles.append({
            "brand_id": brand_id,
            "content_hash": content_hash,
            "portal_id": portal["id"],
            "portal_name": portal["name"],
            "url": url,
            "title": title,
            "body": body,
            "author": entry.get("author", ""),
            "published_at": _parse_date(entry).isoformat(),
            "language": portal["language"],
            "source_credibility": portal["credibility"],
        })

    return articles
