from supabase import create_client, Client
from app.config import settings


def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def filter_new_articles(articles: list[dict], brand_id: str) -> list[dict]:
    if not articles:
        return []

    db = get_supabase()
    hashes = [a["content_hash"] for a in articles]

    seen = db.table("dedupe_hashes") \
             .select("content_hash") \
             .eq("brand_id", brand_id) \
             .in_("content_hash", hashes) \
             .execute().data

    seen_set = {r["content_hash"] for r in seen}
    return [a for a in articles if a["content_hash"] not in seen_set]


def mark_article_seen(content_hash: str, brand_id: str) -> None:
    db = get_supabase()
    db.table("dedupe_hashes").upsert(
        {"content_hash": content_hash, "brand_id": brand_id},
        on_conflict="content_hash,brand_id",
    ).execute()
