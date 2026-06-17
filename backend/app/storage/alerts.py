import logging
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

        alert_type = cfg["alert_type"]
        threshold  = cfg["threshold"]
        current_value: float | None = None

        if alert_type == "perception_score_below" and perception_score < threshold:
            current_value = perception_score
        elif alert_type == "negative_pct_above" and negative_pct > threshold:
            current_value = negative_pct
        elif alert_type == "mention_spike" and mention_count > threshold:
            current_value = float(mention_count)

        if current_value is not None:
            _send_alert_email(cfg["notify_email"], brand_name, alert_type, threshold, current_value)
            try:
                db = get_db()
                db.table("alert_configs").update(
                    {"last_triggered_at": now.isoformat()}
                ).eq("id", cfg["id"]).execute()
            except Exception as e:
                log.warning("Could not update last_triggered_at for alert %s: %s", cfg["id"], e)


def _send_alert_email(email: str, brand_name: str, alert_type: str, threshold: float, value: float) -> None:
    _LABELS = {
        "perception_score_below": ("Perception Score Alert", "Perception score dropped to"),
        "negative_pct_above":     ("Negative Sentiment Alert", "Negative mentions reached"),
        "mention_spike":          ("Mention Spike Alert", "Mention count spiked to"),
    }
    subject_suffix, value_label = _LABELS.get(alert_type, ("Alert", "Value"))

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
                "subject": f"[MediaSense] {brand_name} — {subject_suffix}",
                "html": f"""
<div style="font-family:sans-serif;max-width:520px;margin:auto;padding:24px;background:#0f172a;color:#e2e8f0;border-radius:12px">
  <h2 style="color:#818cf8;margin:0 0 8px">MediaSense Alert</h2>
  <p style="margin:0 0 16px;color:#94a3b8;font-size:14px">Brand: <strong style="color:#e2e8f0">{brand_name}</strong></p>
  <div style="background:#1e293b;border-radius:8px;padding:16px;margin-bottom:16px">
    <p style="margin:0;font-size:16px">{value_label} <strong style="color:#f87171">{value:.1f}</strong>
    (threshold: {threshold:.1f})</p>
  </div>
  <p style="font-size:12px;color:#475569;margin:0">
    Log in to <a href="https://frontend-eight-neon-4hn7jgw46u.vercel.app" style="color:#818cf8">MediaSense</a>
    to review. Alerts are rate-limited to once per 4 hours.
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
