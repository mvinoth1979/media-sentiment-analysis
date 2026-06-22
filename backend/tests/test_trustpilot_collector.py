from unittest.mock import MagicMock, patch

import pytest

FIND_RESPONSE = {"businessUnits": [{"id": "abc123", "displayName": "Test Brand"}]}
REVIEWS_RESPONSE = {
    "reviews": [
        {
            "id": "r1",
            "stars": 4,
            "text": {"review": "Great product, very happy!"},
            "consumer": {"displayName": "Alice"},
            "createdAt": "2025-05-01T10:00:00Z",
        }
    ]
}

BRAND = {"id": "b1b1b1b1-0000-0000-0000-000000000000"}
CONFIG_ENABLED = {
    "trustpilot_enabled": True,
    "trustpilot_domain": "example.com",
    "trustpilot_business_unit_id": "abc123",
}


def _mock_response(status_code=200, json_data=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    mock.raise_for_status = MagicMock()
    return mock


# ── disabled / missing config ──────────────────────────────────────────────

def test_disabled_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    result = collect_trustpilot_for_brand(BRAND, {**CONFIG_ENABLED, "trustpilot_enabled": False})
    assert result == []


def test_missing_domain_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    cfg = {**CONFIG_ENABLED, "trustpilot_domain": "", "trustpilot_business_unit_id": ""}
    with patch("app.ingestion.trustpilot_collector.settings") as s:
        s.trustpilot_api_key = "fake_key"
        result = collect_trustpilot_for_brand(BRAND, cfg)
    assert result == []


def test_no_api_key_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    with patch("app.ingestion.trustpilot_collector.settings") as s:
        s.trustpilot_api_key = ""
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


# ── successful parse ───────────────────────────────────────────────────────

def test_parses_reviews_correctly():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    with patch("app.ingestion.trustpilot_collector.settings") as s, \
         patch("httpx.get") as mock_get:
        s.trustpilot_api_key = "fake_key"
        mock_get.return_value = _mock_response(json_data=REVIEWS_RESPONSE)

        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)

    assert len(result) == 1
    art = result[0]
    assert art["source_type"] == "trustpilot_review"
    assert art["portal_id"] == "trustpilot"
    assert art["author"] == "Alice"
    assert "★★★★☆" in art["title"]
    assert art["reach_metadata"]["rating"] == 4
    assert art["source_credibility"] == 0.80


def test_skips_review_with_empty_body():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    response = {
        "reviews": [
            {"stars": 3, "text": {"review": ""}, "consumer": {"displayName": "Bob"}, "createdAt": "2025-05-02T10:00:00Z"}
        ]
    }
    with patch("app.ingestion.trustpilot_collector.settings") as s, \
         patch("httpx.get") as mock_get:
        s.trustpilot_api_key = "fake_key"
        mock_get.return_value = _mock_response(json_data=response)
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)

    assert result == []


# ── business unit ID resolution ────────────────────────────────────────────

def test_resolves_and_saves_business_unit_id():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    cfg_no_unit = {**CONFIG_ENABLED, "trustpilot_business_unit_id": ""}
    responses = [
        _mock_response(json_data=FIND_RESPONSE),
        _mock_response(json_data=REVIEWS_RESPONSE),
    ]
    with patch("app.ingestion.trustpilot_collector.settings") as s, \
         patch("httpx.get", side_effect=responses), \
         patch("app.ingestion.trustpilot_collector._save_business_unit_id") as mock_save:
        s.trustpilot_api_key = "fake_key"
        result = collect_trustpilot_for_brand(BRAND, cfg_no_unit)

    mock_save.assert_called_once_with(BRAND["id"], "abc123")
    assert len(result) == 1


def test_http_error_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    with patch("app.ingestion.trustpilot_collector.settings") as s, \
         patch("httpx.get", side_effect=Exception("Connection refused")):
        s.trustpilot_api_key = "fake_key"
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []
