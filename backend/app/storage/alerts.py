import logging
from collections import Counter
from datetime import datetime, timezone, timedelta
from app.storage.postgres import get_db
from app.config import settings

log = logging.getLogger(__name__)

_COOLDOWN_HOURS = 4


def get_alert_configs(brand_id: str) -> list[dict]:
    db = get_db()
    return db.table("alert_configs").select("*").eq("brand_id", brand_id).execute().data


def create_alert_config(brand_id: str, alert_type: str, threshold: float, notify_email: str) -> dict:
    db = get_db()
    row = {
        "brand_id":    brand_id,
        "alert_type":  alert_type,
        "threshold":   threshold,
        "notify_email": notify_email,
    }
    return db.table("alert_configs").insert(row).execute().data[0]


def delete_alert_config(alert_id: str) -> None:
    db = get_db()
    db.table("alert_configs").delete().eq("id", alert_id).execute()


# ── C1: Syndication spike check ───────────────────────────────────────────────

def _check_syndication_spike(brand_id: str, threshold: int) -> tuple[float, str] | None:
    """Return (count, article_title) if any single story hit threshold portals in last 24h."""
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    rows = (
        db.table("articles")
        .select("title, syndication_count")
        .eq("brand_id", brand_id)
        .gte("syndication_count", threshold)
        .gte("collected_at", cutoff)
        .order("syndication_count", desc=True)
        .limit(1)
        .execute()
        .data
    )
    if rows:
        return float(rows[0]["syndication_count"]), (rows[0]["title"] or "")[:80]
    return None


# ── C2: Journalist beat check ─────────────────────────────────────────────────

def _check_journalist_beat(brand_id: str, threshold: int) -> tuple[float, str] | None:
    """Return (count, author_name) if any author hit threshold negative articles in last 30 days."""
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    rows = (
        db.table("articles")
        .select("author")
        .eq("brand_id", brand_id)
        .eq("sentiment_label", "negative")
        .gte("collected_at", cutoff)
        .neq("author", "")
        .not_.is_("author", "null")
        .execute()
        .data
    )
    if not rows:
        return None
    counts = Counter(r["author"] for r in rows if r.get("author"))
    if not counts:
        return None
    top_author, top_count = counts.most_common(1)[0]
    if top_count >= threshold:
        return float(top_count), top_author
    return None


# ── Main alert runner ─────────────────────────────────────────────────────────

def check_and_fire_alerts(
    brand_id: str,
    brand_name: str,
    perception_score: float,
    negative_pct: float,
    mention_count: int,
) -> None:
    if not settings.resend_api_key:
        return
    try:
        configs = [c for c in get_alert_configs(brand_id) if c.get("enabled")]
    except Exception as e:
        log.warning("Could not load alert configs for %s: %s", brand_id[:8], e)
        return

    now = datetime.now(timezone.utc)
    cooldown = timedelta(hours=_COOLDOWN_HOURS)

    for cfg in configs:
        last = cfg.get("last_triggered_at")
        if last:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            if now - last_dt < cooldown:
                continue

        alert_type    = cfg["alert_type"]
        threshold     = cfg["threshold"]
        current_value: float | None = None
        extra_context: str = ""

        if alert_type == "perception_score_below" and perception_score < threshold:
            current_value = perception_score

        elif alert_type == "negative_pct_above" and negative_pct > threshold:
            current_value = negative_pct

        elif alert_type == "mention_spike" and mention_count > threshold:
            current_value = float(mention_count)

        elif alert_type == "syndication_spike":
            result = _check_syndication_spike(brand_id, int(threshold))
            if result:
                current_value, extra_context = result

        elif alert_type == "journalist_beat":
            result = _check_journalist_beat(brand_id, int(threshold))
            if result:
                current_value, extra_context = result

        if current_value is not None:
            _send_alert_email(
                cfg["notify_email"], brand_name, alert_type,
                threshold, current_value, extra_context,
            )
            try:
                db = get_db()
                db.table("alert_configs").update(
                    {"last_triggered_at": now.isoformat()}
                ).eq("id", cfg["id"]).execute()
            except Exception as e:
                log.warning("Could not update last_triggered_at for alert %s: %s", cfg["id"], e)


# ── Email sender ──────────────────────────────────────────────────────────────

_ALERT_META: dict[str, dict] = {
    "perception_score_below": {
        "subject": "Perception Score Alert",
        "value_label": "Perception score dropped to",
        "detail_fn": lambda v, ctx, thr: f"Score is <strong style='color:#f87171'>{v:.1f}</strong> (threshold: {thr:.0f})",
    },
    "negative_pct_above": {
        "subject": "Negative Sentiment Alert",
        "value_label": "Negative mentions reached",
        "detail_fn": lambda v, ctx, thr: f"Negative % is <strong style='color:#f87171'>{v:.1f}%</strong> (threshold: {thr:.0f}%)",
    },
    "mention_spike": {
        "subject": "Mention Spike Alert",
        "value_label": "Mention count spiked to",
        "detail_fn": lambda v, ctx, thr: f"Mention count hit <strong style='color:#f87171'>{v:.0f}</strong> (threshold: {thr:.0f})",
    },
    "syndication_spike": {
        "subject": "Syndication Spike Alert",
        "value_label": "Story republished across portals",
        "detail_fn": lambda v, ctx, thr: (
            f"The article <em>\"{ctx}\"</em> was republished in "
            f"<strong style='color:#f87171'>{v:.0f} portals</strong> within 24 hours "
            f"(threshold: {thr:.0f})"
        ),
    },
    "journalist_beat": {
        "subject": "Journalist Beat Alert",
        "value_label": "Repeated negative coverage detected",
        "detail_fn": lambda v, ctx, thr: (
            f"Journalist <strong>{ctx}</strong> has published "
            f"<strong style='color:#f87171'>{v:.0f} negative articles</strong> "
            f"about this brand in the last 30 days (threshold: {thr:.0f})"
        ),
    },
}


def _send_alert_email(
    email: str,
    brand_name: str,
    alert_type: str,
    threshold: float,
    value: float,
    extra_context: str = "",
) -> None:
    meta = _ALERT_META.get(alert_type, {
        "subject": "Alert",
        "detail_fn": lambda v, ctx, thr: f"Value: {v:.1f} (threshold: {thr:.1f})",
    })
    subject   = meta["subject"]
    detail_fn = meta["detail_fn"]
    detail    = detail_fn(value, extra_context, threshold)

    try:
        import httpx
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from":    "MediaSense Alerts <alerts@mediasense.in>",
                "to":      [email],
                "subject": f"[MediaSense] {brand_name} — {subject}",
                "html": f"""
<div style="font-family:sans-serif;max-width:520px;margin:auto;padding:24px;background:#0f172a;color:#e2e8f0;border-radius:12px">
  <h2 style="color:#818cf8;margin:0 0 8px">MediaSense Alert</h2>
  <p style="margin:0 0 16px;color:#94a3b8;font-size:14px">Brand: <strong style="color:#e2e8f0">{brand_name}</strong></p>
  <div style="background:#1e293b;border-radius:8px;padding:16px;margin-bottom:16px">
    <p style="margin:0;font-size:15px">{detail}</p>
  </div>
  <p style="font-size:12px;color:#475569;margin:0">
    Log in to <a href="https://mediasensetool.vercel.app" style="color:#818cf8">MediaSense</a>
    to review. Alerts are rate-limited to once per {_COOLDOWN_HOURS} hours.
  </p>
</div>""",
            },
        )
        if resp.status_code >= 400:
            log.warning("Resend API error %d for alert to %s: %s", resp.status_code, email, resp.text[:200])
        else:
            log.info("Alert email sent to %s for brand %s (%s=%.1f)", email, brand_name, alert_type, value)
    except Exception as e:
        log.error("Failed to send alert email to %s: %s", email, e)
