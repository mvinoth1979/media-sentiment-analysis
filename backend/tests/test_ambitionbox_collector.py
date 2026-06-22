"""Tests for the AmbitionBox employee review collector."""
import json
from unittest.mock import MagicMock, patch

BRAND = {"id": "b2b2b2b2-0000-0000-0000-000000000000"}
CONFIG = {"ambitionbox_enabled": True, "ambitionbox_slug": "tata-motors"}

_REVIEW_1 = {
    "id": 101,
    "rating": 4,
    "title": "Good employer overall",
    "pros": "Good work-life balance",
    "cons": "Slow promotions",
    "designation": "Software Engineer",
    "createdDate": "2025-03-15T08:00:00Z",
}
_REVIEW_NO_CONTENT = {
    "id": 102,
    "rating": 3,
    "title": "",
    "pros": "",
    "cons": "",
    "description": "",
    "designation": "Analyst",
    "createdDate": "2025-03-16T08:00:00Z",
}


def _make_next_data_html(reviews: list[dict]) -> str:
    nd = {"props": {"pageProps": {"reviews": reviews}}}
    return (
        "<html><head>"
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(nd)}</script>'
        "</head><body></body></html>"
    )


def _mock_http(status: int = 200, html: str = "") -> MagicMock:
    m = MagicMock()
    m.status_code = status
    m.text = html
    return m


# ── disabled / missing config ──────────────────────────────────────────────

def test_disabled_returns_empty():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    result = collect_ambitionbox_for_brand(BRAND, {**CONFIG, "ambitionbox_enabled": False})
    assert result == []


def test_missing_slug_returns_empty():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    result = collect_ambitionbox_for_brand(BRAND, {**CONFIG, "ambitionbox_slug": ""})
    assert result == []


# ── __NEXT_DATA__ parsing ──────────────────────────────────────────────────

def test_parses_next_data_review():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    html = _make_next_data_html([_REVIEW_1])
    with patch("httpx.get", return_value=_mock_http(html=html)):
        result = collect_ambitionbox_for_brand(BRAND, CONFIG)

    assert len(result) == 1
    art = result[0]
    assert art["source_type"] == "ambitionbox_review"
    assert art["portal_id"] == "ambitionbox"
    assert art["source_credibility"] == 0.70
    assert "★★★★☆" in art["title"]
    assert "Software Engineer" in art["title"]
    assert "Good work-life balance" in art["body"]
    assert "Slow promotions" in art["body"]
    assert art["reach_metadata"]["rating"] == 4


def test_skips_review_with_no_content():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    html = _make_next_data_html([_REVIEW_NO_CONTENT])
    with patch("httpx.get", return_value=_mock_http(html=html)):
        result = collect_ambitionbox_for_brand(BRAND, CONFIG)
    assert result == []


def test_limits_to_10_reviews():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    reviews = [{**_REVIEW_1, "id": i, "pros": f"Pro {i}"} for i in range(15)]
    html = _make_next_data_html(reviews)
    with patch("httpx.get", return_value=_mock_http(html=html)):
        result = collect_ambitionbox_for_brand(BRAND, CONFIG)
    assert len(result) == 10


def test_content_hash_deterministic():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    html = _make_next_data_html([_REVIEW_1])
    with patch("httpx.get", return_value=_mock_http(html=html)):
        r1 = collect_ambitionbox_for_brand(BRAND, CONFIG)
    with patch("httpx.get", return_value=_mock_http(html=html)):
        r2 = collect_ambitionbox_for_brand(BRAND, CONFIG)
    assert r1[0]["content_hash"] == r2[0]["content_hash"]


# ── error handling ─────────────────────────────────────────────────────────

def test_http_error_returns_empty():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    with patch("httpx.get", side_effect=Exception("timeout")):
        result = collect_ambitionbox_for_brand(BRAND, CONFIG)
    assert result == []


def test_non_200_returns_empty():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    with patch("httpx.get", return_value=_mock_http(status=403)):
        result = collect_ambitionbox_for_brand(BRAND, CONFIG)
    assert result == []


def test_missing_next_data_returns_empty():
    from app.ingestion.ambitionbox_collector import collect_ambitionbox_for_brand
    bare = "<html><body><p>No reviews here</p></body></html>"
    with patch("httpx.get", return_value=_mock_http(html=bare)):
        result = collect_ambitionbox_for_brand(BRAND, CONFIG)
    assert result == []
