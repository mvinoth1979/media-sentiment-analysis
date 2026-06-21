-- Migration 020: Add creator_type column to articles table
-- Item 9 — YouTube Creator Type Classification
-- Valid values: journalist | reviewer | influencer | customer |
--               industry_expert | activist | competitor_affiliate | unknown

ALTER TABLE articles
  ADD COLUMN IF NOT EXISTS creator_type TEXT NOT NULL DEFAULT 'unknown';
