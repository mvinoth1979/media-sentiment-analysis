from supabase import create_client, Client
from app.config import settings


def get_db() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


_REVIEW_TRIGGER_CATEGORIES = frozenset({"crisis_controversy", "regulatory_compliance"})


def save_article(article: dict, nlp: dict) -> str | None:
    db = get_db()
    row = {**article, **nlp}
    for field in ("body", "portal_name"):
        row.pop(field, None)
    row.setdefault("source_platform", "news")
    result = db.table("articles").upsert(row, on_conflict="brand_id,content_hash").execute()
    article_id = result.data[0]["id"] if result.data else None

    # Auto-enqueue for human review when NLP confidence is low AND issue is sensitive.
    # A missing confidence value is treated as high-confidence (no enqueue).
    if article_id is not None:
        confidence = nlp.get("confidence")
        issue_cat = nlp.get("issue_category") or ""
        if (
            confidence is not None
            and float(confidence) < 0.5
            and issue_cat in _REVIEW_TRIGGER_CATEGORIES
        ):
            try:
                db.table("human_review_queue").insert({
                    "brand_id": article.get("brand_id"),
                    "article_id": article_id,
                    "reason": f"low_confidence_{issue_cat}",
                    "status": "pending",
                }).execute()
            except Exception:
                pass  # queue insertion failure must never break article ingestion

    return article_id


_SOURCE_CATEGORY_MAP: dict[str, list[str]] = {
    "youtube":      ["youtube_video", "youtube_comment"],
    "reddit":       ["reddit_post", "reddit_comment"],
    "news":         ["news"],
    "google_review": ["google_review"],
    "review_site":  [
        "google_review", "trustpilot_review", "mouthshut_review",
        "justdial_review", "ambitionbox_review", "tripadvisor_review",
        "team_bhp_review", "amazon_review", "flipkart_review",
        "glassdoor_review", "indiamart_review",
    ],
}


def get_articles(brand_id: str, limit: int = 50, offset: int = 0,
                 sentiment: str | None = None, language: str | None = None,
                 portal_id: str | None = None, topic: str | None = None,
                 state: str | None = None, source_type: str | None = None,
                 date_from: str | None = None, date_to: str | None = None,
                 q: str | None = None,
                 editorial_tone: str | None = None,
                 issue_category: str | None = None,
                 source_category: str | None = None,
                 entity: str | None = None) -> list[dict]:
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
    if source_category and source_category in _SOURCE_CATEGORY_MAP:
        query = query.in_("source_type", _SOURCE_CATEGORY_MAP[source_category])
    elif source_type:
        query = query.eq("source_type", source_type)
    if issue_category:
        query = query.eq("issue_category", issue_category)
    if editorial_tone:
        query = query.eq("editorial_tone", editorial_tone)
    if date_from:
        query = query.gte("collected_at", date_from)
    if date_to:
        query = query.lte("collected_at", date_to)
    if q:
        query = query.ilike("title", f"%{q}%")
    if entity:
        query = query.contains("entities", [entity])
    query = query.order("collected_at", desc=True).range(offset, offset + limit - 1)
    try:
        return query.execute().data
    except Exception:
        if state:
            return get_articles(brand_id, limit=limit, offset=offset,
                                sentiment=sentiment, language=language,
                                portal_id=portal_id, topic=topic, state=None,
                                source_type=source_type,
                                date_from=date_from, date_to=date_to, q=q,
                                editorial_tone=editorial_tone,
                                issue_category=issue_category,
                                source_category=source_category,
                                entity=entity)
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
        # Phase A fix: write content_hash AND story_hash to dedupe_hashes so user-deleted
        # articles never re-enter on the next pipeline run, even if re-fetched from RSS.
        dedupe_rows = []
        for r in rows:
            if r.get("content_hash"):
                dedupe_rows.append({"content_hash": r["content_hash"], "brand_id": brand_id})
            if r.get("story_hash") and r["story_hash"] != r.get("content_hash"):
                dedupe_rows.append({"content_hash": r["story_hash"], "brand_id": brand_id})
        if dedupe_rows:
            db.table("dedupe_hashes").upsert(
                dedupe_rows, on_conflict="content_hash,brand_id"
            ).execute()
    return rows


def get_kpi_summary(brand_id: str) -> dict:
    db = get_db()
    # Exclude very low-confidence classifications (< 0.3) from KPI counts.
    # Articles with NULL confidence (ingested before migration 012) are always included.
    rows = (
        db.table("articles")
        .select("sentiment_label, source_type")
        .eq("brand_id", brand_id)
        .or_("confidence.is.null,confidence.gte.0.3")
        .execute()
        .data
    )
    total = len(rows)
    if total == 0:
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0,
                "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0,
                "youtube_mention_count": 0}
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    youtube_count = 0
    for r in rows:
        counts[r["sentiment_label"]] = counts.get(r["sentiment_label"], 0) + 1
        if r.get("source_type") in ("youtube_video", "youtube_comment"):
            youtube_count += 1
    return {
        "total": total,
        **counts,
        "positive_pct": round(counts["positive"] / total * 100, 1),
        "negative_pct": round(counts["negative"] / total * 100, 1),
        "neutral_pct":  round(counts["neutral"]  / total * 100, 1),
        "youtube_mention_count": youtube_count,
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


def decrement_bootstrap_runs(brand_id: str) -> None:
    try:
        db = get_db()
        row = db.table("brand_configs") \
                .select("bootstrap_runs_remaining") \
                .eq("brand_id", brand_id).execute().data
        if row and row[0].get("bootstrap_runs_remaining", 0) > 0:
            db.table("brand_configs") \
              .update({"bootstrap_runs_remaining": row[0]["bootstrap_runs_remaining"] - 1}) \
              .eq("brand_id", brand_id).execute()
    except Exception:
        pass  # column may not exist on older deployments


def get_pipeline_info(brand_id: str) -> dict:
    db = get_db()
    rows = db.table("brand_configs") \
             .select("pipeline_status, pipeline_last_run_at, pipeline_last_stats") \
             .eq("brand_id", brand_id).execute().data
    if not rows:
        return {"pipeline_status": "idle", "pipeline_last_run_at": None, "pipeline_last_stats": {}}
    return rows[0]
