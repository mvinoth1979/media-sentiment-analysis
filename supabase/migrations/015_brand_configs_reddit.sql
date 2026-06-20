-- Migration 015: add Reddit monitoring config to brand_configs
ALTER TABLE brand_configs
    ADD COLUMN IF NOT EXISTS reddit_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS reddit_subreddits TEXT[] DEFAULT ARRAY[]::TEXT[];
