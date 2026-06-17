-- Migration 008: Add Reliance, Bank of Baroda, and Canara Bank
-- All-India brands with multi-language coverage (hi, gu, bn, kn).
-- Uses INSERT...SELECT so no DO block is needed; safe to re-run.

-- Reliance
INSERT INTO brands (agency_id, name)
SELECT (SELECT agency_id FROM brands ORDER BY created_at LIMIT 1), 'Reliance'
WHERE NOT EXISTS (SELECT 1 FROM brands WHERE name = 'Reliance');

INSERT INTO brand_configs (brand_id, keywords, languages)
SELECT b.id,
       ARRAY['Reliance', 'Reliance Industries', 'RIL'],
       ARRAY['en', 'ta', 'hi', 'gu', 'bn']
FROM   brands b
WHERE  b.name = 'Reliance'
  AND  NOT EXISTS (SELECT 1 FROM brand_configs bc WHERE bc.brand_id = b.id);

-- Bank of Baroda
INSERT INTO brands (agency_id, name)
SELECT (SELECT agency_id FROM brands ORDER BY created_at LIMIT 1), 'Bank of Baroda'
WHERE NOT EXISTS (SELECT 1 FROM brands WHERE name = 'Bank of Baroda');

INSERT INTO brand_configs (brand_id, keywords, languages)
SELECT b.id,
       ARRAY['Bank of Baroda', 'BOB Bank'],
       ARRAY['en', 'ta', 'hi', 'bn', 'kn']
FROM   brands b
WHERE  b.name = 'Bank of Baroda'
  AND  NOT EXISTS (SELECT 1 FROM brand_configs bc WHERE bc.brand_id = b.id);

-- Canara Bank
INSERT INTO brands (agency_id, name)
SELECT (SELECT agency_id FROM brands ORDER BY created_at LIMIT 1), 'Canara Bank'
WHERE NOT EXISTS (SELECT 1 FROM brands WHERE name = 'Canara Bank');

INSERT INTO brand_configs (brand_id, keywords, languages)
SELECT b.id,
       ARRAY['Canara Bank', 'Canbank'],
       ARRAY['en', 'ta', 'hi', 'kn']
FROM   brands b
WHERE  b.name = 'Canara Bank'
  AND  NOT EXISTS (SELECT 1 FROM brand_configs bc WHERE bc.brand_id = b.id);
