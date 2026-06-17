import re
from app.storage.postgres import get_db

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "its", "it", "this", "that", "as",
    "up", "out", "about", "into", "than", "so", "if", "not", "no",
}

# Fraction of candidate article's content words that must overlap with a
# stored rejection before the article is considered "similar enough to block".
SIMILARITY_THRESHOLD = 0.6


def _extract_words(title: str) -> list[str]:
    words = re.findall(r'\b[a-z]{3,}\b', title.lower())
    return [w for w in words if w not in STOPWORDS]


def save_rejections(brand_id: str, articles: list[dict], rejected_by: str | None = None) -> None:
    db = get_db()
    rows = [
        {
            "brand_id": brand_id,
            "original_article_id": a.get("id"),
            "article_url": a.get("url", ""),
            "title": a.get("title", ""),
            "title_words": _extract_words(a.get("title", "")),
            "portal_id": a.get("portal_id"),
            "language": a.get("language"),
            "rejected_by": rejected_by,
        }
        for a in articles
    ]
    if rows:
        db.table("article_rejections").insert(rows).execute()


def is_rejected(brand_id: str, url: str, title: str) -> bool:
    db = get_db()

    # 1. Exact URL already rejected
    exact = (
        db.table("article_rejections")
        .select("id")
        .eq("brand_id", brand_id)
        .eq("article_url", url)
        .limit(1)
        .execute()
    )
    if exact.data:
        return True

    # 2. Title word overlap — catches same story retitled across outlets
    candidate = set(_extract_words(title))
    if not candidate:
        return False

    stored_rows = (
        db.table("article_rejections")
        .select("title_words")
        .eq("brand_id", brand_id)
        .execute()
    )
    for row in stored_rows.data:
        stored = set(row.get("title_words") or [])
        if not stored:
            continue
        if len(candidate & stored) / len(candidate) >= SIMILARITY_THRESHOLD:
            return True

    return False
