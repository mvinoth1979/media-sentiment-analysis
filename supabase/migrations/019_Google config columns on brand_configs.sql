ALTER TABLE brand_configs
  ADD COLUMN IF NOT EXISTS google_places_id TEXT,
  ADD COLUMN IF NOT EXISTS google_reviews_enabled BOOLEAN DEFAULT FALSE;