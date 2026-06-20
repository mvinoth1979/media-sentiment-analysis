from datetime import datetime, timezone, timedelta
from supabase import create_client, Client
from app.config import settings


def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# ── URL-level deduplication (unchanged) ──────────────────────────────────────

def filter_new_articles(articles: list[dict], brand_id: str) -> list[dict]:
    if not articles:
        return []

    db = get_supabase()
    hashes = [a["content_hash"] for a in articles]

    seen = db.table("dedupe_hashes") \
             .select("content_hash") \
             .eq("brand_id", brand_id) \
             .execute().data

    seen_set = {r["content_hash"] for r in seen}
    return [a for a in articles if a["content_hash"] not in seen_set]


def mark_article_seen(content_hash: str, brand_id: str) -> None:
    db = get_supabase()
    db.table("dedupe_hashes").upsert(
        {"content_hash": content_hash, "brand_id": brand_id},
        on_conflict="content_hash,brand_id",
    ).execute()


# ── Story-level syndication deduplication (A1) ────────────────────────────────

def filter_syndicated(articles: list[dict], brand_id: str) -> tuple[list[dict], int]:
    """Separate genuinely new stories from wire-service republications.

    Returns (new_articles, syndicated_count).

    For each article whose story_hash already exists in the DB within the last
    48 hours, the DB syndication_count is incremented and the article is dropped
    from the processing queue — it would otherwise consume NLP quota without adding
    any new sentiment signal.

    Within-batch duplicates (same story from two portals in one run) are also
    collapsed: only the first occurrence is kept.
    """
    if not articles:
        return [], 0

    story_hashes = [a["story_hash"] for a in articles if a.get("story_hash")]
    if not story_hashes:
        return articles, 0

    db = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()

    existing = (
        db.table("articles")
        .select("id, story_hash, syndication_count")
        .eq("brand_id", brand_id)
        .in_("story_hash", list(set(story_hashes)))
        .gte("collected_at", cutoff)
        .execute()
        .data
    )

    # story_hash → existing DB row; None id means seen within this batch only
    known: dict[str, dict] = {r["story_hash"]: r for r in existing}

    new_articles: list[dict] = []
    syndicated_count = 0

    for article in articles:
        sh = article.get("story_hash", "")
        if sh and sh in known:
            row = known[sh]
            if row["id"] is not None:
                # Increment syndication_count on the existing DB record
                db.table("articles").update(
                    {"syndication_count": (row.get("syndication_count") or 1) + 1}
                ).eq("id", row["id"]).execute()
                # Prevent double-increment if the same story appears twice more in this batch
                known[sh] = {**row, "id": None}
            syndicated_count += 1
        else:
            new_articles.append(article)
            # Mark as seen for within-batch dedup
            if sh:
                known[sh] = {"id": None, "story_hash": sh, "syndication_count": 1}

    return new_articles, syndicated_count
