"""
Item 3 — Rolling Baseline Virality Detection
============================================
Computes a 7-day rolling average of YouTube video engagement metrics
(view_count, comment_count, negative_count) and raises a flag when
today's value exceeds 3× that average.

Flag levels:
  1 = emerging_issue   (1 metric spiked)
  2 = reputation_risk  (2 metrics spiked)
  3 = crisis_alert     (all 3 metrics spiked)

Public API
----------
compute_virality_flags(brand_id) -> list[dict]
    Returns a list of flagged articles:
    {
        "article_id": str,
        "title": str,
        "flag_level": int,          # 1 / 2 / 3
        "triggered_metrics": list[str],
    }

save_snapshot(article_id, brand_id, view_count, comment_count, negative_count) -> None
    Upserts today's metrics snapshot into video_metrics_history.
"""

import logging
from collections import Counter
from datetime import date, timedelta

from app.storage.postgres import get_db

log = logging.getLogger(__name__)

_MULTIPLIER = 3          # trigger when today > MULTIPLIER × rolling avg
_HISTORY_DAYS = 7        # rolling window in days


def save_snapshot(
    article_id: str,
    brand_id: str,
    view_count: int,
    comment_count: int,
    negative_count: int,
) -> None:
    """Upsert today's metric snapshot for a YouTube video article."""
    try:
        db = get_db()
        row = {
            "article_id":    article_id,
            "brand_id":      brand_id,
            "snapshot_date": date.today().isoformat(),
            "view_count":    int(view_count),
            "comment_count": int(comment_count),
            "negative_count": int(negative_count),
        }
        db.table("video_metrics_history").upsert(
            row, on_conflict="article_id,snapshot_date"
        ).execute()
    except Exception as exc:
        log.warning("save_snapshot failed for article %s: %s", article_id, exc)


def _rolling_avg(snapshots: list[dict], metric: str) -> float | None:
    """
    Compute the arithmetic mean of *metric* across the provided snapshot rows.
    Returns None when snapshots is empty (no baseline available).
    """
    if not snapshots:
        return None
    total = sum(int(s.get(metric) or 0) for s in snapshots)
    return total / len(snapshots)


def compute_virality_flags(brand_id: str) -> list[dict]:
    """
    Scan all YouTube video articles for *brand_id* and return those whose
    today metrics exceed 3× the 7-day rolling average.

    Returns:
        list of dicts: {article_id, title, flag_level, triggered_metrics}
    """
    db = get_db()
    today_str = date.today().isoformat()
    cutoff_str = (date.today() - timedelta(days=1)).isoformat()  # yesterday (exclusive) so "today" is separate

    # Fetch today's YouTube video articles for this brand
    try:
        articles = (
            db.table("articles")
            .select("id, title, source_type, reach_metadata, negative_count")
            .eq("brand_id", brand_id)
            .eq("source_type", "youtube_video")
            .gte("collected_at", today_str)
            .execute()
            .data
        )
    except Exception as exc:
        log.warning("compute_virality_flags: failed to fetch articles for brand %s: %s", brand_id, exc)
        return []

    if not articles:
        return []

    history_cutoff = (date.today() - timedelta(days=_HISTORY_DAYS)).isoformat()
    flags: list[dict] = []

    for article in articles:
        article_id = article["id"]
        title      = article.get("title") or ""

        # Fetch historical snapshots (last 7 days, excluding today)
        try:
            history = (
                db.table("video_metrics_history")
                .select("view_count, comment_count, negative_count, snapshot_date")
                .eq("article_id", article_id)
                .eq("brand_id", brand_id)
                .gte("snapshot_date", history_cutoff)
                .order("snapshot_date", desc=True)
                .execute()
                .data
            )
        except Exception as exc:
            log.warning("compute_virality_flags: history query failed for %s: %s", article_id, exc)
            continue

        # Exclude today's own snapshot from baseline (if already saved)
        history = [s for s in history if s.get("snapshot_date") != today_str]

        if not history:
            # No baseline — cannot determine anomaly
            log.debug("No history for article %s, skipping virality check", article_id)
            continue

        # Extract today's metric values from reach_metadata + article fields
        meta = article.get("reach_metadata") or {}
        today_views    = int(meta.get("view_count")    or 0)
        today_comments = int(meta.get("comment_count") or 0)
        today_negative = int(article.get("negative_count") or 0)

        triggered: list[str] = []

        # Check each metric against rolling average
        for metric_name, today_val in [
            ("view_count",    today_views),
            ("comment_count", today_comments),
            ("negative_count", today_negative),
        ]:
            avg = _rolling_avg(history, metric_name)
            if avg is None:
                continue
            if avg > 0 and today_val > _MULTIPLIER * avg:
                triggered.append(metric_name)

        if triggered:
            flag_level = min(len(triggered), 3)  # 1=emerging, 2=reputation, 3=crisis
            flags.append({
                "article_id":       article_id,
                "title":            title,
                "flag_level":       flag_level,
                "triggered_metrics": triggered,
            })
            log.info(
                "Virality flag level=%d for article %s (%s): %s",
                flag_level, article_id, title[:50], triggered,
            )

    return flags
