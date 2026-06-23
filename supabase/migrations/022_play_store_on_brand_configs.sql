-- Migration 022: add Google Play Store columns to brand_configs
--
-- Enables per-brand Play Store review monitoring via google-play-scraper.
-- play_store_app_id is the package name from the Play Store URL
-- (e.g. com.maruti.marutisuzuki, com.iob.mobilebanking).

ALTER TABLE brand_configs
  ADD COLUMN IF NOT EXISTS play_store_enabled  BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS play_store_app_id   TEXT;
