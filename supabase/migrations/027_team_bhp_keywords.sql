-- Migration 027: Seed team_bhp_keywords for automotive brands
-- Team-BHP collector searches https://www.team-bhp.com for each keyword
-- and scrapes ownership reviews + forum threads.
-- Only automotive brands are relevant; all others left at default FALSE / empty.

-- ── Maruti Suzuki ─────────────────────────────────────────────────────────────
-- Current model lineup (2024-25): hatchbacks, sedans, SUVs, MPVs
UPDATE brand_configs bc
SET    team_bhp_enabled  = TRUE,
       team_bhp_keywords = ARRAY[
           'Maruti Swift',
           'Maruti Baleno',
           'Maruti Grand Vitara',
           'Maruti Brezza',
           'Maruti WagonR',
           'Maruti Ertiga',
           'Maruti XL6',
           'Maruti Fronx',
           'Maruti Jimny',
           'Maruti Dzire',
           'Maruti Celerio',
           'Maruti Alto'
       ]
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%maruti%';

-- ── Tata Motors ───────────────────────────────────────────────────────────────
-- Current model lineup: SUVs, EVs, hatchbacks, sedans
UPDATE brand_configs bc
SET    team_bhp_enabled  = TRUE,
       team_bhp_keywords = ARRAY[
           'Tata Nexon',
           'Tata Harrier',
           'Tata Safari',
           'Tata Punch',
           'Tata Tiago',
           'Tata Curvv',
           'Tata Altroz',
           'Tata Tigor',
           'Tata Nexon EV',
           'Tata Punch EV',
           'Tata Curvv EV',
           'Tata Tiago EV'
       ]
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%tata%'
  AND  b.name NOT ILIKE '%tata steel%'
  AND  b.name NOT ILIKE '%tata consultancy%';

-- ── Ashok Leyland ─────────────────────────────────────────────────────────────
-- Commercial vehicles: LCVs, trucks, buses, EVs
UPDATE brand_configs bc
SET    team_bhp_enabled  = TRUE,
       team_bhp_keywords = ARRAY[
           'Ashok Leyland DOST',
           'Ashok Leyland Partner',
           'Ashok Leyland Boss',
           'Ashok Leyland Sunshine',
           'Ashok Leyland Viking',
           'Ashok Leyland AVTR',
           'Ashok Leyland Circuit',
           'Ashok Leyland Stile',
           'Ashok Leyland truck',
           'Ashok Leyland bus'
       ]
FROM   brands b
WHERE  bc.brand_id = b.id
  AND  b.name ILIKE '%ashok leyland%';
