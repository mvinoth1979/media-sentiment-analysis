-- Migration 026: Seed ambitionbox_slug + ambitionbox_enabled for all 14 brands
-- Verified slugs via AmbitionBox (2026-06-22).
-- URL pattern: https://www.ambitionbox.com/reviews/{slug}-reviews
-- Southern Railway → NULL (only parent Indian Railways page exists; no zone-specific page)

-- ── Tata ──────────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'tata-motors'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%tata%'
  AND  b.name NOT ILIKE '%tata steel%'
  AND  b.name NOT ILIKE '%tata consultancy%';

-- ── Ashok Leyland ─────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'ashok-leyland'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%ashok leyland%';

-- ── Maruti Suzuki ─────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'maruti-suzuki'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%maruti%';

-- ── Reliance / Jio ────────────────────────────────────────────────────────────
-- Listed as "Jio" on AmbitionBox (33,000+ reviews) rather than Reliance Industries
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'jio'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%reliance%';

-- ── Bank of Baroda ────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'bank-of-baroda'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%bank of baroda%';

-- ── Canara Bank ───────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'canara-bank'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%canara bank%';

-- ── Indian Bank (guard: exclude Indian Overseas Bank) ─────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'indian-bank'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%indian bank%'
  AND  b.name NOT ILIKE '%overseas%';

-- ── Indian Overseas Bank ──────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'indian-overseas-bank'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%indian overseas bank%';

-- ── CavinKare ─────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'cavinkare'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%cavinkare%';

-- ── Ramco Cements ─────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'the-ramco-cements'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%ramco%';

-- ── Lalitha Jewellery ─────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'lalitha-jewellery'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%lalitha%';

-- ── Pothys ────────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'pothys'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%pothys%';

-- ── CIPET ─────────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    ambitionbox_enabled = TRUE,
       ambitionbox_slug    = 'central-institute-of-plastics-engineering-and-tech'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%cipet%';

-- ── Southern Railway ──────────────────────────────────────────────────────────
-- No AmbitionBox page for this zone specifically; parent is 'indian-railways'
-- which conflates all zones. Leave slug NULL, disabled by default.
