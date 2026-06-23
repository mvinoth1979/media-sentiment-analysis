import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client
from app.config import settings
from app.pipeline.worker import enqueue_brand

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _order_by_staleness(db, brands: list[dict], configs: dict[str, dict]) -> list[dict]:
    """Brands with bootstrap_runs_remaining > 0 always sort first (new-brand fast-fill).
    Within each tier, oldest last-collected article goes first so quota-starved brands
    are not repeatedly skipped."""
    rows = db.table("articles").select("brand_id, collected_at") \
             .order("collected_at", desc=True).limit(2000).execute().data
    last_seen: dict[str, str] = {}
    for row in rows:
        last_seen.setdefault(row["brand_id"], row["collected_at"])

    def sort_key(b: dict) -> tuple:
        cfg = configs.get(b["id"], {})
        bootstrap = cfg.get("bootstrap_runs_remaining", 0)
        # tier 0 = bootstrap priority, tier 1 = normal staleness order
        return (0 if bootstrap > 0 else 1, last_seen.get(b["id"], ""))

    return sorted(brands, key=sort_key)


def _enqueue_all_brands():
    db = create_client(settings.supabase_url, settings.supabase_service_role_key)
    brands = db.table("brands").select("id, name").execute().data
    config_rows = db.table("brand_configs").select("*").execute().data
    configs = {r["brand_id"]: r for r in config_rows}
    brands = _order_by_staleness(db, brands, configs)
    for brand in brands:
        config = configs.get(brand["id"])
        if not config:
            continue
        enqueue_brand(brand, {
            "keywords":                  config.get("keywords", []),
            "languages":                 config.get("languages", ["en"]),
            "bootstrap_runs_remaining":  config.get("bootstrap_runs_remaining", 0),
            "youtube_enabled":           config.get("youtube_enabled", False),
            "youtube_channel_ids":       config.get("youtube_channel_ids") or [],
            "reddit_enabled":            config.get("reddit_enabled", False),
            "reddit_subreddits":         config.get("reddit_subreddits") or [],
            "google_reviews_enabled":    config.get("google_reviews_enabled", False),
            "google_places_id":          config.get("google_places_id") or "",
            "play_store_enabled":        config.get("play_store_enabled", False),
            "play_store_app_id":         config.get("play_store_app_id") or "",
        })
    bootstrap_count = sum(1 for c in configs.values() if c.get("bootstrap_runs_remaining", 0) > 0)
    log.info("Enqueued %d brands (%d in bootstrap priority)", len(brands), bootstrap_count)


def start_scheduler():
    from datetime import datetime, timezone
    scheduler.add_job(
        _enqueue_all_brands, "interval", hours=1,
        id="hourly_pipeline",
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    log.info("Scheduler started — hourly pipeline active, first run immediate")
