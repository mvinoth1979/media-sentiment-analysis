import re
import hashlib
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
import feedparser


# ── Story-level hash (wire-service dedup) ────────────────────────────────────

def _story_hash(title: str) -> str:
    """Normalised title hash used to detect syndicated wire-service articles.
    Different portals publishing the same PTI/ANI story have different URLs but
    near-identical headlines — first 12 significant tokens capture the story identity.
    """
    normalized = unicodedata.normalize("NFKC", title).lower()
    clean = re.sub(r"[^\w\s]", " ", normalized)
    tokens = [t for t in clean.split() if len(t) > 2]
    # Take exactly 8 tokens — trailing wire-service credits ("PTI", "ANI") are
    # beyond position 8 in any normal headline and therefore don't affect the hash.
    key = " ".join(tokens[:8])
    return hashlib.sha256(key.encode()).hexdigest()[:32]


# ── Author extraction ─────────────────────────────────────────────────────────

def _extract_author(entry) -> str:
    """Try all common RSS/Atom author fields in priority order."""
    candidates = [
        entry.get("author"),
        (entry.get("author_detail") or {}).get("name"),
        entry.get("dc_creator"),
        entry.get("creator"),
    ]
    for c in candidates:
        if c and isinstance(c, str) and c.strip():
            return c.strip()[:200]
    return ""


# ── Regulatory source detection ───────────────────────────────────────────────

_REGULATORY_DOMAINS = frozenset({
    "sebi.gov.in", "rbi.org.in", "rbi.gov.in", "irdai.gov.in",
    "pfrda.org.in", "trai.gov.in", "mca.gov.in", "fssai.gov.in",
    "dpiit.gov.in", "pib.gov.in", "pib.nic.in", "mospi.gov.in",
    "indiacode.nic.in", "mofpi.gov.in", "cbi.gov.in", "sfio.gov.in",
})

_REGULATORY_TITLE_PHRASES = frozenset({
    "sebi", "securities and exchange board",
    "rbi", "reserve bank of india",
    "irdai", "irda",
    "pfrda", "pension fund",
    "trai", "telecom regulatory",
    "fssai", "food safety",
    "ministry of", "ministry of finance", "ministry of petroleum",
    "lok sabha", "rajya sabha", "parliament of india",
    "supreme court", "high court", "nclt", "nclat", "drat",
    "enforcement directorate", "ed raids",
    "gazette notification", "statutory notice",
    "press information bureau", "pib release",
    "central government notification",
    "income tax department", "customs department",
})


def _is_regulatory_source(article_url: str, portal_rss_url: str, title: str) -> bool:
    """Return True if the article originates from a regulatory/government body.
    Check is url-domain first (low false-positive rate), then title phrases.
    """
    for raw_url in (article_url, portal_rss_url):
        try:
            domain = urlparse(raw_url).netloc.lower().lstrip("www.")
            if any(domain == d or domain.endswith("." + d) for d in _REGULATORY_DOMAINS):
                return True
        except Exception:
            pass
    title_lower = title.lower()
    return any(phrase in title_lower for phrase in _REGULATORY_TITLE_PHRASES)


# ── Keyword filter ────────────────────────────────────────────────────────────

def keyword_matches(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        pattern = kw if kw.startswith("\\b") else r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text_lower):
            return True
    return False


# ── Date parser ───────────────────────────────────────────────────────────────

def _parse_date(entry) -> datetime:
    raw = entry.get("published") or entry.get("updated", "")
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


# ── Main collector ────────────────────────────────────────────────────────────

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

        if not portal.get("skip_keyword_filter") and not keyword_matches(combined, keywords):
            continue

        url = entry.get("link", "")
        if not url:
            continue

        content_hash = hashlib.sha256(f"{portal['id']}::{url}".encode()).hexdigest()

        articles.append({
            "brand_id": brand_id,
            "content_hash": content_hash,
            "story_hash": _story_hash(title),
            "portal_id": portal["id"],
            "portal_name": portal["name"],
            "url": url,
            "title": title,
            "body": body,
            "author": _extract_author(entry),
            "published_at": _parse_date(entry).isoformat(),
            "language": portal["language"],
            "source_credibility": portal["credibility"],
            "is_regulatory_source": _is_regulatory_source(url, portal["rss_url"], title),
        })

    return articles
