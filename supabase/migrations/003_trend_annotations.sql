CREATE TABLE trend_annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    label TEXT NOT NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trend_annotations_brand_date ON trend_annotations(brand_id, date);

ALTER TABLE trend_annotations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users can view annotations for their brands"
ON trend_annotations FOR SELECT
USING (
    brand_id IN (SELECT brand_id FROM user_roles WHERE user_id = auth.uid())
    OR brand_id IN (
        SELECT b.id FROM brands b
        JOIN user_roles ur ON ur.agency_id = b.agency_id
        WHERE ur.user_id = auth.uid()
    )
);

-- Service role bypass (backend uses service_role_key, bypasses RLS automatically)
-- No additional policies needed for INSERT/UPDATE/DELETE from backend
