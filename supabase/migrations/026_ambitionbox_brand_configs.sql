-- Migration 026: Seed ambitionbox_slug for all 14 brands
-- Verified slugs via AmbitionBox search (2026-06-22).
-- URL pattern: https://www.ambitionbox.com/reviews/{slug}-reviews
-- Southern Railway → NULL (only Indian Railways parent exists; no zone-specific page)

-- Automotive
UPDATE brand_configs bc
SET    ambitionbox_slug = 'tata-motors'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%tata%motors%';

UPDATE brand_configs bc
SET    ambitionbox_slug = 'ashok-leyland'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%ashok leyland%';

UPDATE brand_configs bc
SET    ambitionbox_slug = 'maruti-suzuki'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%maruti%';

-- Telecom / Conglomerate
-- Reliance Jio is listed as "Jio" on AmbitionBox (slug: jio)
UPDATE brand_configs bc
SET    ambitionbox_slug = 'jio'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%reliance%';

-- Banking
UPDATE brand_configs bc
SET    ambitionbox_slug = 'bank-of-baroda'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%bank of baroda%';

UPDATE brand_configs bc
SET    ambitionbox_slug = 'canara-bank'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%canara bank%';

-- Indian Bank guard: exclude Indian Overseas Bank
UPDATE brand_configs bc
SET    ambitionbox_slug = 'indian-bank'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%indian bank%'
  AND  b.name NOT ILIKE '%overseas%';

UPDATE brand_configs bc
SET    ambitionbox_slug = 'indian-overseas-bank'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%indian overseas bank%';

-- FMCG / Consumer
UPDATE brand_configs bc
SET    ambitionbox_slug = 'cavinkare'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%cavinkare%';

-- Cement
UPDATE brand_configs bc
SET    ambitionbox_slug = 'the-ramco-cements'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%ramco%';

-- Jewellery / Retail
UPDATE brand_configs bc
SET    ambitionbox_slug = 'lalitha-jewellery'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%lalitha%jewel%';

UPDATE brand_configs bc
SET    ambitionbox_slug = 'pothys'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%pothys%';

-- Education / Training
-- Full slug: central-institute-of-plastics-engineering-and-tech
UPDATE brand_configs bc
SET    ambitionbox_slug = 'central-institute-of-plastics-engineering-and-tech'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%cipet%';

-- Southern Railway → no distinct AmbitionBox zone page; leave slug NULL
-- (reviews appear under parent "indian-railways" which conflates all zones)
