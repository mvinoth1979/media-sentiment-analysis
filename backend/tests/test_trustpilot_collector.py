"""Tests for the scraping-based Trustpilot collector (no API key required)."""
import json
from unittest.mock import MagicMock, patch

BRAND = {"id": "b1b1b1b1-0000-0000-0000-000000000000"}
CONFIG_ENABLED = {
    "trustpilot_enabled": True,
    "trustpilot_domain": "example.com",
}

_REVIEW_1 = {
    "id": "r1",
    "text": "Great product, very happy!",
    "title": "Excellent experience",
    "rating": {"value": 4},
    "consumer": {"displayName": "Alice"},
    "dates": {"publishedDate": "2025-05-01T10:00:00Z"},
}
_REVIEW_NO_BODY = {
    "id": "r2",
    "text": "",
    "title": "",
    "rating": {"value": 3},
    "consumer": {"displayName": "Bob"},
    "dates": {"publishedDate": "2025-05-02T10:00:00Z"},
}


def _make_html(reviews: list[dict]) -> str:
    next_data = {
        "props": {
            "pageProps": {"reviews": reviews}
        }
    }
    return (
        "<html><head>"
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>'
        "</head><body></body></html>"
    )


def _mock_http(status_code: int = 200, html: str = "") -> MagicMock:
    m = MagicMock()
    m.status_code = status_code
    m.text = html
    return m


# ── disabled / missing config ──────────────────────────────────────────────

def test_disabled_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    result = collect_trustpilot_for_brand(BRAND, {**CONFIG_ENABLED, "trustpilot_enabled": False})
    assert result == []


def test_missing_domain_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    result = collect_trustpilot_for_brand(BRAND, {**CONFIG_ENABLED, "trustpilot_domain": ""})
    assert result == []


# ── successful scraping ────────────────────────────────────────────────────

def test_parses_review_correctly():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    with patch("httpx.get", return_value=_mock_http(html=_make_html([_REVIEW_1]))):
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)

    assert len(result) == 1
    art = result[0]
    assert art["source_type"] == "trustpilot_review"
    assert art["portal_id"] == "trustpilot"
    assert art["author"] == "Alice"
    assert "★★★★☆" in art["title"]
    assert art["reach_metadata"]["rating"] == 4
    assert art["source_credibility"] == 0.80
    assert "Great product" in art["body"]
    assert "Excellent experience" in art["body"]


def test_skips_review_with_empty_body_and_title():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    with patch("httpx.get", return_value=_mock_http(html=_make_html([_REVIEW_NO_BODY]))):
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


def test_limits_to_20_reviews():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    reviews = [
        {**_REVIEW_1, "id": f"r{i}", "text": f"Review {i}"}
        for i in range(30)
    ]
    with patch("httpx.get", return_value=_mock_http(html=_make_html(reviews))):
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    assert len(result) == 20


def test_content_hash_deterministic():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    html = _make_html([_REVIEW_1])
    with patch("httpx.get", return_value=_mock_http(html=html)):
        r1 = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    with patch("httpx.get", return_value=_mock_http(html=html)):
        r2 = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    assert r1[0]["content_hash"] == r2[0]["content_hash"]


# ── error handling ─────────────────────────────────────────────────────────

def test_http_error_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    with patch("httpx.get", side_effect=Exception("Connection refused")):
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


def test_non_200_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    with patch("httpx.get", return_value=_mock_http(status_code=404)):
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []


def test_missing_next_data_returns_empty():
    from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
    bare_html = "<html><body><p>No JSON here</p></body></html>"
    with patch("httpx.get", return_value=_mock_http(html=bare_html)):
        result = collect_trustpilot_for_brand(BRAND, CONFIG_ENABLED)
    assert result == []
