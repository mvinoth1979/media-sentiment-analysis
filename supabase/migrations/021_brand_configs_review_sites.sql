-- Migration 021: add review-site channel columns to brand_configs
--
-- Adds toggle + identifier columns for all 6 review-site channels that were
-- built in Phase 3.B (Trustpilot, MouthShut, JustDial, AmbitionBox, Team-BHP,
-- TripAdvisor).  Google Reviews columns were added in migration 019.
--
-- All statements are idempotent (ADD COLUMN IF NOT EXISTS).

ALTER TABLE brand_configs
  ADD COLUMN IF NOT EXISTS trustpilot_enabled      BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS trustpilot_domain        TEXT,
  ADD COLUMN IF NOT EXISTS mouthshut_enabled        BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS mouthshut_slug           TEXT,
  ADD COLUMN IF NOT EXISTS justdial_enabled         BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS justdial_listing_url     TEXT,
  ADD COLUMN IF NOT EXISTS ambitionbox_enabled      BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS ambitionbox_slug         TEXT,
  ADD COLUMN IF NOT EXISTS team_bhp_enabled         BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS team_bhp_keywords        TEXT[]  DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN IF NOT EXISTS tripadvisor_enabled      BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS tripadvisor_listing_url  TEXT;
