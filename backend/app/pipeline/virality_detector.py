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

# Absolute thresholds used when there is no prior history (day 0).
# A newly-uploaded video that already hits these numbers is viral by definition.
_ABS_VIEW_THRESHOLD    = 50_000
_ABS_COMMENT_THRESHOLD = 500


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


def compute_virality_flags(brand_id: str, article_days: int = 1) -> list[dict]:
    """
    Scan YouTube video articles for *brand_id* and return those whose current
    metrics spike relative to their rolling baseline.

    article_days:
        How many days back to look for articles to evaluate.
        Default 1 (today only) for the orchestrator post-pipeline call.
        Pass 7 for the dashboard endpoint so all recent videos are checked.

    Handles partial history gracefully:
      - 0 prior days  → absolute threshold (50K views / 500 comments)
      - 1-6 prior days → rolling avg of available days × 3
      - 7+ prior days → full 7-day rolling avg × 3

    Returns:
        list of dicts: {article_id, title, url, flag_level, triggered_metrics}
    """
    db = get_db()
    today_str    = date.today().isoformat()
    article_from = (date.today() - timedelta(days=article_days - 1)).isoformat()

    try:
        articles = (
            db.table("articles")
            .select("id, title, url, source_type, reach_metadata, negative_count")
            .eq("brand_id", brand_id)
            .eq("source_type", "youtube_video")
            .gte("collected_at", article_from)
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
        url        = article.get("url") or ""
        meta       = article.get("reach_metadata") or {}
        today_views    = int(meta.get("view_count")    or 0)
        today_comments = int(meta.get("comment_count") or 0)
        today_negative = int(article.get("negative_count") or 0)

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

        # Exclude today's own snapshot from baseline so we don't compare today with today
        history = [s for s in history if s.get("snapshot_date") != today_str]

        triggered: list[str] = []

        if not history:
            # Day 0 — no prior snapshots. Use absolute thresholds so genuinely viral
            # day-1 content is still surfaced rather than silently dropped.
            if today_views > _ABS_VIEW_THRESHOLD:
                triggered.append("view_count")
            if today_comments > _ABS_COMMENT_THRESHOLD:
                triggered.append("comment_count")
        else:
            # 1–7 days of history available: compare against rolling average.
            # _rolling_avg handles partial windows naturally (mean of N rows).
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
            flag_level = min(len(triggered), 3)
            flags.append({
                "article_id":        article_id,
                "title":             title,
                "url":               url,
                "flag_level":        flag_level,
                "triggered_metrics": triggered,
                "history_days":      len(history),
            })
            log.info(
                "Virality flag level=%d for article %s (%s) [%d history days]: %s",
                flag_level, article_id, title[:50], len(history), triggered,
            )

    return flags
