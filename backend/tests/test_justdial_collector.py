from unittest.mock import MagicMock, patch

BRAND = {"id": "b3b3b3b3-0000-0000-0000-000000000000"}
CONFIG_ENABLED = {
    "justdial_enabled": True,
    "justdial_listing_url": "https://www.justdial.com/Mumbai/Amul-Dairy/011PXX11-XX11-XXXXXX",
}

FIXTURE_HTML_JSON_LD = """<html><head>
<script type="application/ld+json">
{"@type":"LocalBusiness","name":"Amul","review":[
  {"reviewRating":{"ratingValue":5},"reviewBody":"Excellent service!","author":{"name":"Mohan"},"datePublished":"2025-06-01"},
  {"reviewRating":{"ratingValue":3},"reviewBody":"Average experience.","author":{"name":"Sunita"},"datePublished":"2025-06-02"}
]}
</script></head><body></body></html>"""


def _mock_response(status_code=200, text=""):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = text
    return mock


# ── disabled / missing config ──────────────────────────────────────────────

def test_disabled_returns_empty():
    from app.ingestion.justdial_collector import collect_justdial_for_brand
    result = collect_justdial_for_brand(BRAND, {**CONFIG_ENABLED, "justdial_enabled": False})
    assert result == []


def test_missing_listing_url_returns_empty():
    from app.ingestion.justdial_collector import collect_justdial_for_brand
    result = collect_justdial_for_brand(BRAND, {"justdial_enabled": True, "justdial_listing_url": ""})
    assert result == []


# ── WAP URL conversion ─────────────────────────────────────────────────────

def test_converts_to_wap():
    from app.ingestion.justdial_collector import _to_wap
    assert _to_wap("https://www.justdial.com/foo") == "https://wap.justdial.com/foo"


def test_wap_url_unchanged_if_already_wap():
    from app.ingestion.justdial_collector import _to_wap
    assert _to_wap("https://wap.justdial.com/foo") == "https://wap.justdial.com/foo"


# ── successful JSON-LD parse ───────────────────────────────────────────────

def test_parses_json_ld_reviews():
    from app.ingestion.justdial_collector import collect_justdial_for_brand
    with patch("httpx.get", return_value=_mock_response(text=FIXTURE_HTML_JSON_LD)):
        result = collect_justdial_for_brand(BRAND, CONFIG_ENABLED)

    assert len(result) == 2
    assert result[0]["source_type"] == "justdial_review"
    assert result[0]["portal_id"] == "justdial"
    assert result[0]["author"] == "Mohan"
    assert result[0]["reach_metadata"]["rating"] == 5
    assert result[0]["source_credibility"] == 0.60
    assert "★★★★★" in result[0]["title"]


def test_skips_empty_body_reviews():
    from app.ingestion.justdial_collector import collect_justdial_for_brand
    html = """<html><head><script type="application/ld+json">
    {"@type":"LocalBusiness","review":[{"reviewRating":{"ratingValue":3},"reviewBody":"","author":{"name":"X"},"datePublished":"2025-06-01"}]}
    </script></head></html>"""
    with patch("httpx.get", return_value=_mock_response(text=html)):
        result = collect_justdial_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


# ── error handling ─────────────────────────────────────────────────────────

def test_non_200_returns_empty():
    from app.ingestion.justdial_collector import collect_justdial_for_brand
    with patch("httpx.get", return_value=_mock_response(status_code=403)):
        result = collect_justdial_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


def test_http_exception_returns_empty():
    from app.ingestion.justdial_collector import collect_justdial_for_brand
    with patch("httpx.get", side_effect=Exception("Bot block")):
        result = collect_justdial_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []
