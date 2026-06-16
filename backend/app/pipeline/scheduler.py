import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client
from app.config import settings
from app.pipeline.worker import enqueue_brand

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _order_by_staleness(db, brands: list[dict]) -> list[dict]:
    """Sorts brands by their most recent article's collected_at, oldest/never-processed
    first — so a brand that got starved of NLP quota last cycle is first in line next
    time, instead of the same brands always losing the race for the shared daily quota."""
    rows = db.table("articles").select("brand_id, collected_at") \
             .order("collected_at", desc=True).limit(2000).execute().data
    last_seen: dict[str, str] = {}
    for row in rows:
        last_seen.setdefault(row["brand_id"], row["collected_at"])
    return sorted(brands, key=lambda b: last_seen.get(b["id"], ""))


def _enqueue_all_brands():
    db = create_client(settings.supabase_url, settings.supabase_service_role_key)
    brands = db.table("brands").select("id, name").execute().data
    brands = _order_by_staleness(db, brands)
    for brand in brands:
        config_row = db.table("brand_configs").select("*") \
                       .eq("brand_id", brand["id"]).execute().data
        if not config_row:
            continue
        config = config_row[0]
        enqueue_brand(brand, {
            "keywords": config.get("keywords", []),
            "languages": config.get("languages", ["en"]),
        })
    log.info("Enqueued %d brands for processing", len(brands))


def start_scheduler():
    from datetime import datetime, timezone
    scheduler.add_job(
        _enqueue_all_brands, "interval", hours=1,
        id="hourly_pipeline",
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    log.info("Scheduler started — hourly pipeline active, first run immediate")
