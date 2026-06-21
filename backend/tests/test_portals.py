from app.ingestion.portals import PORTALS, get_portal, get_portals_for_languages, get_portal_tier, TIER_LABELS
from app.ingestion.gnews import get_gnews_portals

def test_portals_have_required_fields():
    for p in PORTALS:
        assert "id" in p
        assert "name" in p
        assert "rss_url" in p
        assert "language" in p
        assert "credibility" in p
        assert 0.0 <= p["credibility"] <= 1.0

def test_get_portal_by_id():
    portal = get_portal("the_hindu")
    assert portal is not None
    assert portal["language"] == "en"

def test_get_portals_for_languages_english():
    portals = get_portals_for_languages(["en"])
    assert all(p["language"] == "en" for p in portals)
    assert len(portals) == 12

def test_get_portals_for_languages_tamil():
    portals = get_portals_for_languages(["ta"])
    assert all(p["language"] == "ta" for p in portals)
    assert len(portals) == 11

def test_get_portals_for_both_languages():
    # Tamil portals come from get_gnews_portals; static list is English-only
    portals = get_portals_for_languages(["en", "ta"])
    langs = {p["language"] for p in portals}
    assert "en" in langs

def test_gnews_portals_include_tamil():
    portals = get_gnews_portals(["Amul"], ["en", "ta"])
    langs = {p["language"] for p in portals}
    assert "en" in langs and "ta" in langs
    assert all(p.get("skip_keyword_filter") is True for p in portals)

def test_get_portal_unknown_id_returns_none():
    assert get_portal("nonexistent_id") is None


# --- Item 4: gnews portal tier tests ---

def test_gnews_portal_returns_tier_5():
    """gnews_ prefixed portal_ids must return tier 5 (Wire tier), not 4."""
    assert get_portal_tier("gnews_the_hindu") == 5
    assert get_portal_tier("gnews_ndtv") == 5
    assert get_portal_tier("gnews_random_source") == 5

def test_tier_5_label_is_wire():
    """TIER_LABELS must include 5 -> 'Wire'."""
    assert TIER_LABELS[5] == "Wire"

def test_youtube_portal_returns_tier_0():
    assert get_portal_tier("youtube_abc123") == 0

def test_known_portal_tier_mapping():
    # the_hindu credibility=0.92 -> Tier 1
    assert get_portal_tier("the_hindu") == 1
    # deccan_chronicle credibility=0.78 -> Tier 2 (>= 0.78)
    assert get_portal_tier("deccan_chronicle") == 2
    # news18 credibility=0.76 -> Tier 3 (>= 0.68)
    assert get_portal_tier("news18") == 3

def test_unknown_non_gnews_portal_still_returns_tier_4():
    """Non-gnews unknown portals remain tier 4."""
    assert get_portal_tier("unknown_portal_xyz") == 4
