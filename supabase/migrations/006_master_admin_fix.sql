-- Allow master_admin rows to have both agency_id and brand_id as NULL
-- (master_admin is a platform-wide role, not scoped to any brand or agency)
ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS user_roles_check;
ALTER TABLE user_roles ADD CONSTRAINT user_roles_check
    CHECK (
        role = 'master_admin'
        OR (agency_id IS NOT NULL OR brand_id IS NOT NULL)
    );
