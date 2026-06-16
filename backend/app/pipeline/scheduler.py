import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client
from app.config import settings
from app.pipeline.worker import enqueue_brand

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _enqueue_all_brands():
    db = create_client(settings.supabase_url, settings.supabase_service_role_key)
    brands = db.table("brands").select("id, name").execute().data
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
