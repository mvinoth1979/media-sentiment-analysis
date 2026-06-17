-- Migration 008: Add Reliance, Bank of Baroda, and Canara Bank
-- All-India brands with multi-language coverage (hi, gu, bn, kn added).
-- Uses the agency_id from existing brands so they sit under the same tenant.

DO $$
DECLARE
    v_agency_id    UUID;
    v_reliance_id  UUID;
    v_bob_id       UUID;
    v_canara_id    UUID;
BEGIN
    -- Inherit the agency from existing brands (all brands share one agency in this deployment)
    SELECT agency_id INTO v_agency_id FROM brands ORDER BY created_at LIMIT 1;

    IF v_agency_id IS NULL THEN
        RAISE EXCEPTION 'No existing agency found. Create an agency first.';
    END IF;

    -- ── Reliance ──────────────────────────────────────────────────────────────
    INSERT INTO brands (agency_id, name)
    VALUES (v_agency_id, 'Reliance')
    RETURNING id INTO v_reliance_id;

    INSERT INTO brand_configs (brand_id, keywords, languages)
    VALUES (
        v_reliance_id,
        ARRAY['Reliance', 'Reliance Industries', 'RIL'],
        ARRAY['en', 'ta', 'hi', 'gu', 'bn']
    );

    -- ── Bank of Baroda ────────────────────────────────────────────────────────
    INSERT INTO brands (agency_id, name)
    VALUES (v_agency_id, 'Bank of Baroda')
    RETURNING id INTO v_bob_id;

    INSERT INTO brand_configs (brand_id, keywords, languages)
    VALUES (
        v_bob_id,
        ARRAY['Bank of Baroda', 'BOB Bank'],
        ARRAY['en', 'ta', 'hi', 'bn', 'kn']
    );

    -- ── Canara Bank ───────────────────────────────────────────────────────────
    INSERT INTO brands (agency_id, name)
    VALUES (v_agency_id, 'Canara Bank')
    RETURNING id INTO v_canara_id;

    INSERT INTO brand_configs (brand_id, keywords, languages)
    VALUES (
        v_canara_id,
        ARRAY['Canara Bank', 'Canbank'],
        ARRAY['en', 'ta', 'hi', 'kn']
    );

    RAISE NOTICE 'Created brands: Reliance=%, Bank of Baroda=%, Canara Bank=%',
        v_reliance_id, v_bob_id, v_canara_id;
END $$;
