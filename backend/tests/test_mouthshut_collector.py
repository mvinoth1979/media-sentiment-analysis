from unittest.mock import MagicMock, patch

BRAND = {"id": "b2b2b2b2-0000-0000-0000-000000000000"}
CONFIG_ENABLED = {"mouthshut_enabled": True, "mouthshut_slug": "amul-dairy-reviews-925925714"}

FIXTURE_HTML_JSON_LD = """<html><head>
<script type="application/ld+json">
{"@type":"Product","name":"Amul","review":[
  {"reviewRating":{"ratingValue":4},"reviewBody":"Good quality product.","author":{"name":"Raj"},"datePublished":"2025-05-01"},
  {"reviewRating":{"ratingValue":2},"reviewBody":"Packaging was damaged.","author":{"name":"Priya"},"datePublished":"2025-05-02"}
]}
</script></head><body></body></html>"""

FIXTURE_HTML_EMPTY = "<html><body><p>No reviews found.</p></body></html>"


def _mock_response(status_code=200, text=""):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = text
    return mock


# ── disabled / missing config ──────────────────────────────────────────────

def test_disabled_returns_empty():
    from app.ingestion.mouthshut_collector import collect_mouthshut_for_brand
    result = collect_mouthshut_for_brand(BRAND, {**CONFIG_ENABLED, "mouthshut_enabled": False})
    assert result == []


def test_missing_slug_returns_empty():
    from app.ingestion.mouthshut_collector import collect_mouthshut_for_brand
    result = collect_mouthshut_for_brand(BRAND, {"mouthshut_enabled": True, "mouthshut_slug": ""})
    assert result == []


# ── successful JSON-LD parse ───────────────────────────────────────────────

def test_parses_json_ld_reviews():
    from app.ingestion.mouthshut_collector import collect_mouthshut_for_brand
    with patch("httpx.get", return_value=_mock_response(text=FIXTURE_HTML_JSON_LD)):
        result = collect_mouthshut_for_brand(BRAND, CONFIG_ENABLED)

    assert len(result) == 2
    assert result[0]["source_type"] == "mouthshut_review"
    assert result[0]["portal_id"] == "mouthshut"
    assert result[0]["author"] == "Raj"
    assert result[0]["reach_metadata"]["rating"] == 4
    assert result[0]["source_credibility"] == 0.65
    assert "★★★★☆" in result[0]["title"]


def test_skips_empty_body_reviews():
    from app.ingestion.mouthshut_collector import collect_mouthshut_for_brand
    html = """<html><head><script type="application/ld+json">
    {"@type":"Product","review":[{"reviewRating":{"ratingValue":3},"reviewBody":"","author":{"name":"X"},"datePublished":"2025-05-01"}]}
    </script></head></html>"""
    with patch("httpx.get", return_value=_mock_response(text=html)):
        result = collect_mouthshut_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


# ── error handling ─────────────────────────────────────────────────────────

def test_non_200_returns_empty():
    from app.ingestion.mouthshut_collector import collect_mouthshut_for_brand
    with patch("httpx.get", return_value=_mock_response(status_code=403, text="")):
        result = collect_mouthshut_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


def test_http_exception_returns_empty():
    from app.ingestion.mouthshut_collector import collect_mouthshut_for_brand
    with patch("httpx.get", side_effect=Exception("Timeout")):
        result = collect_mouthshut_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


def test_no_reviews_returns_empty():
    from app.ingestion.mouthshut_collector import collect_mouthshut_for_brand
    with patch("httpx.get", return_value=_mock_response(text=FIXTURE_HTML_EMPTY)):
        result = collect_mouthshut_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []
