-- Migration 014: extend alert_configs.alert_type CHECK to include C1 + C2 alert types
-- PostgreSQL does not support ALTER CONSTRAINT — must drop then re-add.
-- Adds: syndication_spike (fire when a story spreads to N+ portals in 24h)
--       journalist_beat   (fire when same journalist publishes N+ negative articles in 30d)

ALTER TABLE alert_configs
    DROP CONSTRAINT IF EXISTS alert_configs_alert_type_check;

ALTER TABLE alert_configs
    ADD CONSTRAINT alert_configs_alert_type_check
    CHECK (alert_type IN (
        'perception_score_below',
        'negative_pct_above',
        'mention_spike',
        'syndication_spike',
        'journalist_beat'
    ));
