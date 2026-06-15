"""Backfill InfluxDB with sentiment trend data from existing Supabase articles."""
import logging
from collections import defaultdict
from datetime import datetime, timezone
from app.storage.postgres import get_db
from app.storage.influxdb import write_sentiment_point
from app.pipeline.perception import calculate_perception_score

log = logging.getLogger(__name__)


def backfill_influxdb(brand_id: str) -> int:
    """Read all articles for a brand, group by day, write one InfluxDB point per day.

    Returns the number of points written.
    """
    db = get_db()
    rows = db.table("articles").select(
        "sentiment_score,sentiment_label,source_credibility,reach_score,published_at,collected_at"
    ).eq("brand_id", brand_id).execute().data

    if not rows:
        log.info("No articles found for brand %s — nothing to backfill", brand_id)
        return 0

    by_day: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        raw = row.get("published_at") or row.get("collected_at", "")
        try:
            day = datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except Exception:
            continue
        by_day[day].append(row)

    written = 0
    for day_str, articles in sorted(by_day.items()):
        ts = datetime.fromisoformat(f"{day_str}T12:00:00+00:00")
        score = calculate_perception_score(articles)
        counts = {
            "positive": sum(1 for a in articles if a.get("sentiment_label") == "positive"),
            "negative": sum(1 for a in articles if a.get("sentiment_label") == "negative"),
            "neutral":  sum(1 for a in articles if a.get("sentiment_label") == "neutral"),
            "total": len(articles),
        }
        try:
            write_sentiment_point(brand_id, score, counts, timestamp=ts)
            log.info("Backfilled %s: score=%.1f total=%d", day_str, score, len(articles))
            written += 1
        except Exception as e:
            log.error("InfluxDB write failed for %s: %s", day_str, e)

    return written
