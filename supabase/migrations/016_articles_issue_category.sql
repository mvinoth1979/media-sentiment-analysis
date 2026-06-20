-- Migration 016: add structured issue_category to articles
-- 12-category taxonomy: financial_performance, regulatory_compliance,
-- product_quality, leadership_governance, crisis_controversy,
-- awards_recognition, csr_sustainability, policy_government,
-- competitive_landscape, customer_experience, brand_advocacy,
-- market_opportunity, other

ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS issue_category TEXT DEFAULT 'other';

CREATE INDEX IF NOT EXISTS idx_articles_issue_category
    ON articles(brand_id, issue_category);
