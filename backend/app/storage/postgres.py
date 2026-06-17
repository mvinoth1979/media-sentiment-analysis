from supabase import create_client, Client
from app.config import settings


def get_db() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def save_article(article: dict, nlp: dict) -> str | None:
    db = get_db()
    row = {**article, **nlp}
    for field in ("body", "confidence", "portal_name"):
        row.pop(field, None)
    row.setdefault("source_platform", "news")
    result = db.table("articles").upsert(row, on_conflict="brand_id,content_hash").execute()
    return result.data[0]["id"] if result.data else None


def get_articles(brand_id: str, limit: int = 50, offset: int = 0,
                 sentiment: str | None = None, language: str | None = None,
                 portal_id: str | None = None, topic: str | None = None,
                 state: str | None = None,
                 date_from: str | None = None, date_to: str | None = None,
                 q: str | None = None) -> list[dict]:
    db = get_db()
    query = db.table("articles").select("*").eq("brand_id", brand_id)
    if sentiment:
        query = query.eq("sentiment_label", sentiment)
    if language:
        query = query.eq("language", language)
    if portal_id:
        query = query.eq("portal_id", portal_id)
    if topic:
        query = query.contains("topics", [topic])
    if state:
        query = query.contains("states_mentioned", [state])
    if date_from:
        query = query.gte("collected_at", date_from)
    if date_to:
        query = query.lte("collected_at", date_to)
    if q:
        query = query.ilike("title", f"%{q}%")
    query = query.order("collected_at", desc=True).range(offset, offset + limit - 1)
    try:
        return query.execute().data
    except Exception:
        if state:
            return get_articles(brand_id, limit=limit, offset=offset,
                                sentiment=sentiment, language=language,
                                portal_id=portal_id, topic=topic, state=None,
                                date_from=date_from, date_to=date_to, q=q)
        return []


def delete_articles(article_ids: list[str], brand_id: str) -> list[dict]:
    db = get_db()
    rows = (
        db.table("articles")
        .select("*")
        .eq("brand_id", brand_id)
        .in_("id", article_ids)
        .execute()
        .data
    )
    if rows:
        db.table("articles").delete().eq("brand_id", brand_id).in_("id", article_ids).execute()
    return rows


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


def get_state_breakdown(brand_id: str) -> list[dict]:
    try:
        db = get_db()
        rows = db.table("articles") \
                 .select("states_mentioned, sentiment_label") \
                 .eq("brand_id", brand_id).execute().data
    except Exception:
        return []
    state_map: dict[str, dict] = {}
    for row in rows:
        label = row.get("sentiment_label", "neutral")
        for state in row.get("states_mentioned") or []:
            if state not in state_map:
                state_map[state] = {"state": state, "count": 0,
                                    "positive": 0, "negative": 0, "neutral": 0}
            state_map[state]["count"] += 1
            state_map[state][label] = state_map[state].get(label, 0) + 1
    return sorted(state_map.values(), key=lambda x: x["count"], reverse=True)


def update_pipeline_status(brand_id: str, status: str, stats: dict | None = None) -> None:
    from datetime import datetime, timezone
    db = get_db()
    payload: dict = {"pipeline_status": status}
    if status == "running":
        payload["pipeline_last_run_at"] = datetime.now(timezone.utc).isoformat()
    if stats is not None:
        payload["pipeline_last_stats"] = stats
    db.table("brand_configs").update(payload).eq("brand_id", brand_id).execute()


def get_pipeline_info(brand_id: str) -> dict:
    db = get_db()
    rows = db.table("brand_configs") \
             .select("pipeline_status, pipeline_last_run_at, pipeline_last_stats") \
             .eq("brand_id", brand_id).execute().data
    if not rows:
        return {"pipeline_status": "idle", "pipeline_last_run_at": None, "pipeline_last_stats": {}}
    return rows[0]
