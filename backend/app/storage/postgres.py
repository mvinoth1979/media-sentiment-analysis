from supabase import create_client, Client
from app.config import settings


def get_db() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def save_article(article: dict, nlp: dict) -> str | None:
    db = get_db()
    row = {**article, **nlp}
    row.pop("body", None)
    row.pop("confidence", None)
    result = db.table("articles").upsert(row, on_conflict="brand_id,content_hash").execute()
    return result.data[0]["id"] if result.data else None


def get_articles(brand_id: str, limit: int = 50, offset: int = 0,
                 sentiment: str | None = None, language: str | None = None) -> list[dict]:
    db = get_db()
    q = db.table("articles").select("*").eq("brand_id", brand_id) \
           .order("collected_at", desc=True).range(offset, offset + limit - 1)
    if sentiment:
        q = q.eq("sentiment_label", sentiment)
    if language:
        q = q.eq("language", language)
    return q.execute().data


def get_kpi_summary(brand_id: str) -> dict:
    db = get_db()
    rows = db.table("articles").select("sentiment_label").eq("brand_id", brand_id).execute().data
    total = len(rows)
    if total == 0:
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0,
                "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0}
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for r in rows:
        counts[r["sentiment_label"]] = counts.get(r["sentiment_label"], 0) + 1
    return {
        "total": total,
        **counts,
        "positive_pct": round(counts["positive"] / total * 100, 1),
        "negative_pct": round(counts["negative"] / total * 100, 1),
        "neutral_pct":  round(counts["neutral"]  / total * 100, 1),
    }
