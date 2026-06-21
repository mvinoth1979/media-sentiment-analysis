-- Migration 019: Add Google Business Reviews configuration columns to brand_configs
-- Adds google_places_id (resolved Google Places ID) and google_reviews_enabled toggle.

ALTER TABLE brand_configs
  ADD COLUMN IF NOT EXISTS google_places_id TEXT,
  ADD COLUMN IF NOT EXISTS google_reviews_enabled BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN brand_configs.google_places_id IS
  'Google Places ID for the brand location (e.g. ChIJ...). Resolved automatically on first run if empty.';

COMMENT ON COLUMN brand_configs.google_reviews_enabled IS
  'When TRUE, the pipeline collects Google Business reviews for this brand each run.';
