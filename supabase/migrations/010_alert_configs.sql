-- Migration 010: alert_configs — per-brand sentiment alert thresholds
-- Alerts fire via email (Resend) after each pipeline run when conditions are met.
-- Rate-limited by last_triggered_at to avoid flooding (4h cooldown per alert).

CREATE TABLE IF NOT EXISTS alert_configs (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id          UUID        NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    alert_type        TEXT        NOT NULL
                                  CHECK (alert_type IN (
                                      'perception_score_below',
                                      'negative_pct_above',
                                      'mention_spike'
                                  )),
    threshold         FLOAT       NOT NULL,
    notify_email      TEXT        NOT NULL,
    enabled           BOOLEAN     NOT NULL DEFAULT TRUE,
    last_triggered_at TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_configs_brand ON alert_configs(brand_id);
