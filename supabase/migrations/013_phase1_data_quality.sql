-- Phase 1 data quality: wire dedup, headline/body sentiment, regulatory flag.

-- A1: Wire-service syndication deduplication
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS story_hash TEXT,
    ADD COLUMN IF NOT EXISTS syndication_count INTEGER NOT NULL DEFAULT 1;

-- Lookup index for 48-hour story dedup window
CREATE INDEX IF NOT EXISTS idx_articles_story_hash
    ON articles(brand_id, story_hash, collected_at);

-- A2: Separate headline and body sentiment scores
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS headline_sentiment_score FLOAT,
    ADD COLUMN IF NOT EXISTS body_sentiment_score FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_divergence BOOLEAN NOT NULL DEFAULT FALSE;

-- B1 (added here — zero-cost alongside A2): editorial tone classification
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS editorial_tone TEXT;

-- B2: Regulatory / government source flag
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS is_regulatory_source BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_articles_regulatory
    ON articles(brand_id, is_regulatory_source)
    WHERE is_regulatory_source = TRUE;

CREATE INDEX IF NOT EXISTS idx_articles_divergence
    ON articles(brand_id, sentiment_divergence)
    WHERE sentiment_divergence = TRUE;
