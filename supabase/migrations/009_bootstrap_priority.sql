-- Migration 009: bootstrap_runs_remaining for new-brand pipeline priority
-- Newly onboarded brands run at the front of the queue until this counter hits 0.

ALTER TABLE brand_configs
    ADD COLUMN IF NOT EXISTS bootstrap_runs_remaining INTEGER NOT NULL DEFAULT 0;

-- Give the 3 new brands 6 priority pipeline runs
UPDATE brand_configs
SET bootstrap_runs_remaining = 6
WHERE brand_id IN (
    SELECT id FROM brands WHERE name IN ('Reliance', 'Bank of Baroda', 'Canara Bank')
);
