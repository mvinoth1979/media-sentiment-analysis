-- Wave 1 hardening: master_admin role + source_platform + pipeline visibility
-- Run this migration ONCE against the production Supabase project.

-- §5.2 — Add master_admin to allowed roles
ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS user_roles_role_check;
ALTER TABLE user_roles ADD CONSTRAINT user_roles_role_check
    CHECK (role IN ('master_admin','agency_admin','agency_analyst','brand_admin','brand_viewer'));

-- §5.3 — Platform-agnostic source discriminator on articles
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS source_platform TEXT NOT NULL DEFAULT 'news';

-- Backfill existing rows (all pre-existing articles are from news portals)
UPDATE articles SET source_platform = 'news' WHERE source_platform IS NULL OR source_platform = '';

CREATE INDEX IF NOT EXISTS idx_articles_source_platform ON articles(brand_id, source_platform);

-- §5.6 — Pipeline progress visibility on brand_configs
ALTER TABLE brand_configs
    ADD COLUMN IF NOT EXISTS pipeline_status TEXT NOT NULL DEFAULT 'idle',
    ADD COLUMN IF NOT EXISTS pipeline_last_run_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS pipeline_last_stats JSONB NOT NULL DEFAULT '{}'::jsonb;
