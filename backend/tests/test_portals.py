from app.ingestion.portals import PORTALS, get_portal, get_portals_for_languages

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
    assert len(portals) == 8

def test_get_portals_for_languages_tamil():
    portals = get_portals_for_languages(["ta"])
    assert all(p["language"] == "ta" for p in portals)
    assert len(portals) == 7

def test_get_portals_for_both_languages():
    portals = get_portals_for_languages(["en", "ta"])
    langs = {p["language"] for p in portals}
    assert "en" in langs and "ta" in langs

def test_get_portal_unknown_id_returns_none():
    assert get_portal("nonexistent_id") is None
