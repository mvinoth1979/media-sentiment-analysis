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
             .in_("content_hash", hashes) \
             .execute().data

    seen_set = {r["content_hash"] for r in seen}
    new_articles = [a for a in articles if a["content_hash"] not in seen_set]

    if new_articles:
        db.table("dedupe_hashes").insert([
            {"content_hash": a["content_hash"], "brand_id": brand_id}
            for a in new_articles
        ]).execute()

    return new_articles
