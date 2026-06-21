-- Migration 017: video_metrics_history table
-- Stores daily snapshots of YouTube video engagement metrics per article.
-- Used by the rolling-baseline virality detector to fire when today's metrics
-- exceed 3× the 7-day average.

CREATE TABLE IF NOT EXISTS video_metrics_history (
    id               BIGSERIAL PRIMARY KEY,
    article_id       UUID        NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    brand_id         UUID        NOT NULL,
    snapshot_date    DATE        NOT NULL DEFAULT CURRENT_DATE,
    view_count       BIGINT      NOT NULL DEFAULT 0,
    comment_count    BIGINT      NOT NULL DEFAULT 0,
    negative_count   INTEGER     NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_video_metrics_daily
        UNIQUE (article_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_vmh_article_date
    ON video_metrics_history (article_id, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_vmh_brand_date
    ON video_metrics_history (brand_id, snapshot_date DESC);

COMMENT ON TABLE video_metrics_history IS
    'Daily snapshots of YouTube video engagement metrics per article, used for virality detection.';
