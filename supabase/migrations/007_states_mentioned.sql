-- §5.1 — State/region sentiment filtering
-- Adds states_mentioned to articles for Indian state-level filtering.
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS states_mentioned TEXT[] NOT NULL DEFAULT '{}';

-- GIN index for fast array containment queries (e.g. @> ARRAY['Tamil Nadu'])
CREATE INDEX IF NOT EXISTS idx_articles_states ON articles USING GIN (states_mentioned);
