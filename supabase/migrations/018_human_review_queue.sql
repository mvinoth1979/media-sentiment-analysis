CREATE TABLE IF NOT EXISTS human_review_queue (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id      UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    article_id    UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    reason        TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewer_id   UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reviewed_at   TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_human_review_queue_brand_status ON human_review_queue (brand_id, status, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_human_review_queue_pending_article ON human_review_queue (article_id) WHERE status = 'pending';
