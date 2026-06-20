-- Add NLP confidence score column to articles.
-- confidence is returned by Gemini/Groq (0.0–1.0) but was previously dropped
-- before DB insert because this column did not exist.
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS confidence FLOAT;

CREATE INDEX IF NOT EXISTS idx_articles_confidence ON articles(brand_id, confidence);
