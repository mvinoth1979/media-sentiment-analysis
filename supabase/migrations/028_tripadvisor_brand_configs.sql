-- Migration 028: Seed tripadvisor_listing_url for relevant brands
-- Only brands with confirmed TripAdvisor listing pages are enabled.
-- Lalitha Jewellery: no listing found — left disabled.

-- ── Southern Railway — Nilgiri Mountain Railway (UNESCO) ──────────────────────
-- Operated by Southern Railway; thousands of reviews on TripAdvisor.
-- Best proxy for Southern Railway's tourism/passenger sentiment.
UPDATE brand_configs bc
SET    tripadvisor_enabled     = TRUE,
       tripadvisor_listing_url = 'https://www.tripadvisor.in/Attraction_Review-g297679-d3440016-Reviews-Nilgiri_Mountain_Railway-Ooty_Udhagamandalam_The_Nilgiris_District_Tamil_Nadu.html'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%Southern Railway%';

-- ── Pothys — T Nagar Chennai ──────────────────────────────────────────────────
-- Major tourist shopping destination; confirmed listing with reviews.
UPDATE brand_configs bc
SET    tripadvisor_enabled     = TRUE,
       tripadvisor_listing_url = 'https://www.tripadvisor.in/Attraction_Review-g304556-d10380288-Reviews-Pothys_Hyper-Chennai_Madras_Chennai_District_Tamil_Nadu.html'
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%pothys%';

-- ── Lalitha Jewellery — no listing found ──────────────────────────────────────
-- tripadvisor_enabled remains FALSE; no action needed.
