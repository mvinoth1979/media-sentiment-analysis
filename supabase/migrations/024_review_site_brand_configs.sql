-- Migration 024: populate review-site config (Trustpilot / MouthShut / JustDial) for all 14 brands
--
-- Prerequisites: migrations 021-023 must be applied (columns exist in brand_configs).
-- All UPDATE statements are safe to re-run; setting the same values a second time
-- is idempotent.
--
-- Notes:
--   • Reliance MouthShut listing is under /mobile-operators/ not /product-reviews/,
--     so mouthshut_slug is left NULL — collector would 404 otherwise.
--   • Southern Railway has no brand-specific MouthShut page (only generic Indian
--     Railways); mouthshut_slug left NULL.
--   • Only Tata (tatamotors.com) and Reliance/Jio (jio.com) are confirmed on
--     Trustpilot with meaningful review counts.  All other brands get NULL.
--   • JustDial URLs point to the brand's registered office or primary listed
--     location — these are real listing pages, not search result pages.

-- ── CIPET ─────────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'central-institute-of-plastics-engineering-and-technology-cipet-chennai-reviews-925716789',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Central-Institute-Of-Plastics-Engineering-Technology-Head-Office-Opposite-Olympia-Tech-Park-TVK-Industrial-Estate-Guindy/044P3006406_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE 'CIPET';

-- ── Southern Railway ──────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Southern-Railway-Gm-Office-George-Town/044PXX44-XX44-180530023358-Y8M9_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Southern Railway%';

-- ── Indian Bank ───────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'indian-bank-reviews-925053632',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Indian-Bank-Corporate-Office-Near-Admk-Office-Royapettah/044P3015157_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Indian Bank%'
  AND  b.name NOT ILIKE '%Overseas%';

-- ── Indian Overseas Bank ──────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'indian-overseas-bank-reviews-925004510',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Indian-Overseas-Bank-Central-Office-Opposite-TVS-Near-Spencer-Plaza-Mount-Road/044P6200031_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Indian Overseas Bank%';

-- ── Bank of Baroda ────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'bank-of-baroda-reviews-925004470',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Mumbai/Bank-of-Baroda-Corporate-Head-Office-Bandra-Kurla-Complex-Bandra-East/022P8005770_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name = 'Bank of Baroda';

-- ── Canara Bank ───────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'canara-bank-reviews-925004505',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Bangalore/Canara-Bank-Head-Office-Near-Dwarakanath-Bhavan-Basavanagudi/080PXX80-XX80-130520143441-N7F6_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name = 'Canara Bank';

-- ── Tata ──────────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    trustpilot_enabled   = TRUE,
       trustpilot_domain    = 'tatamotors.com',
       mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'tata-motors-ltd-reviews-925099295',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/TATA-Motors-Ltd-Regional-Office-Opposite-Dindigul-Thalappakatti-T-Nagar/044P4207943_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE 'Tata';

-- ── Reliance ──────────────────────────────────────────────────────────────────
-- MouthShut slug omitted: listing lives under /mobile-operators/ not /product-reviews/
UPDATE brand_configs bc
SET    trustpilot_enabled   = TRUE,
       trustpilot_domain    = 'jio.com',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Reliance-Jio-Infocom-Opposite-to-Natesan-Park-T-Nagar/044PXX44-XX44-211109164029-C1P6_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name = 'Reliance';

-- ── CavinKare ─────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'Cavinkare-Pvt-Ltd-reviews-925875043',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Cavinkare-Pvt-Ltd-Corporate-Office-Opposite-TPL-House-Teynampet/044PPE03951_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%CavinKare%';

-- ── Ramco Cements ─────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'The-Ramco-Cements-Ltd-reviews-925857767',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/The-Ramco-Cements-Ltd-Corporate-Office-Opposite-DrRadhakrishnan-Salai-Mylapore/044PXX44-XX44-131121231735-S3J4_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Ramco%';

-- ── Lalitha Jewellery ─────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'lalitha-jewellery-mart-t-nagar-chennai-reviews-925704438',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Lalithaa-Jewellery-Mart-Ltd-Near-Panagal-Park-T-Nagar/044PJD00905_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Lalitha%';

-- ── Pothys ────────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'pothys-reviews-926132960',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Pothys-Opposite-Doraiswami-Subway-T-Nagar/044PXX44-XX44-180908181756-P4F3_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Pothys%';

-- ── Ashok Leyland ─────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'ashok-leyland-ltd-reviews-925099286',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Chennai/Ashok-Leyland-Ltd-Corporate-Office/044P4207938_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Ashok Leyland%';

-- ── Maruti ────────────────────────────────────────────────────────────────────
UPDATE brand_configs bc
SET    mouthshut_enabled    = TRUE,
       mouthshut_slug       = 'maruti-suzuki-india-ltd-reviews-925099294',
       justdial_enabled     = TRUE,
       justdial_listing_url = 'https://www.justdial.com/Delhi/Maruti-Suzuki-India-Pvt-Ltd-Head-Office-Vasant-Kunj/011PXX11-XX11-000075149597-O5A4_BZDET'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Maruti%';
