-- Migration 021: add keyword_variants JSONB column to brand_configs
-- Stores per-language transliterated keyword variants for Indian language
-- relevance filtering. Falls back to keyword_variants.py if column is empty.
ALTER TABLE brand_configs
    ADD COLUMN IF NOT EXISTS keyword_variants JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN brand_configs.keyword_variants IS
    'Per-language transliterated keyword variants: {lang: [variant1, variant2, ...]}. '
    'Used by rss_collector for non-English article relevance filtering. '
    'Falls back to ingestion/keyword_variants.py if empty.';
