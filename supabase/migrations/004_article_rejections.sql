CREATE TABLE article_rejections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    original_article_id UUID,
    article_url TEXT NOT NULL,
    title TEXT NOT NULL,
    title_words TEXT[] NOT NULL DEFAULT '{}',
    portal_id TEXT,
    language TEXT,
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rejected_by UUID REFERENCES auth.users(id)
);

CREATE INDEX idx_article_rejections_brand_url ON article_rejections(brand_id, article_url);
CREATE INDEX idx_article_rejections_brand ON article_rejections(brand_id);

ALTER TABLE article_rejections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users can view rejections for their brands"
ON article_rejections FOR SELECT
USING (
    brand_id IN (SELECT brand_id FROM user_roles WHERE user_id = auth.uid())
    OR brand_id IN (
        SELECT b.id FROM brands b
        JOIN user_roles ur ON ur.agency_id = b.agency_id
        WHERE ur.user_id = auth.uid()
    )
);
