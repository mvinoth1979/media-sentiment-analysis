ALTER TABLE agencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Agencies: visible to agency members
CREATE POLICY "agency members can view their agency"
ON agencies FOR SELECT
USING (id IN (
    SELECT agency_id FROM user_roles WHERE user_id = auth.uid()
));

-- Brands: visible if user has a role for that brand or parent agency
CREATE POLICY "users can view brands they have access to"
ON brands FOR SELECT
USING (
    id IN (SELECT brand_id FROM user_roles WHERE user_id = auth.uid())
    OR agency_id IN (SELECT agency_id FROM user_roles WHERE user_id = auth.uid())
);

-- Articles: scoped to brand
CREATE POLICY "users can view articles for their brands"
ON articles FOR SELECT
USING (
    brand_id IN (SELECT brand_id FROM user_roles WHERE user_id = auth.uid())
    OR brand_id IN (
        SELECT b.id FROM brands b
        JOIN user_roles ur ON ur.agency_id = b.agency_id
        WHERE ur.user_id = auth.uid()
    )
);

-- Brand configs: visible to brand/agency members
CREATE POLICY "users can view brand configs they have access to"
ON brand_configs FOR SELECT
USING (
    brand_id IN (SELECT brand_id FROM user_roles WHERE user_id = auth.uid())
    OR brand_id IN (
        SELECT b.id FROM brands b
        JOIN user_roles ur ON ur.agency_id = b.agency_id
        WHERE ur.user_id = auth.uid()
    )
);

-- User roles: users see their own role assignments
CREATE POLICY "users can view their own role assignments"
ON user_roles FOR SELECT
USING (
    user_id = auth.uid()
    OR agency_id IN (SELECT agency_id FROM user_roles WHERE user_id = auth.uid() AND role IN ('agency_admin', 'agency_analyst'))
);

-- Service role bypass (backend uses service_role_key, bypasses RLS automatically)
-- No additional policies needed for INSERT/UPDATE/DELETE from backend
