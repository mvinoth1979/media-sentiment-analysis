"""Tests for TripAdvisor collector."""

import json
import pytest
from unittest.mock import MagicMock, patch

from app.ingestion.tripadvisor_collector import (
    _content_hash,
    _extract_json_ld_reviews,
    _map_json_ld_review,
    collect_tripadvisor_for_brand,
)
from bs4 import BeautifulSoup

BRAND = {"id": "brand-sr-001"}
LISTING_URL = (
    "https://www.tripadvisor.in/Attraction_Review-g297679-d3440016-"
    "Reviews-Nilgiri_Mountain_Railway-Ooty.html"
)
CONFIG_ON  = {"tripadvisor_enabled": True,  "tripadvisor_listing_url": LISTING_URL}
CONFIG_OFF = {"tripadvisor_enabled": False, "tripadvisor_listing_url": LISTING_URL}
CONFIG_NO_URL = {"tripadvisor_enabled": True, "tripadvisor_listing_url": ""}

JSON_LD_REVIEW = {
    "@type": "TouristAttraction",
    "name": "Nilgiri Mountain Railway",
    "review": [
        {
            "@id": "review-001",
            "reviewBody": "Breathtaking ride through the Nilgiri hills.",
            "name": "Must-do experience",
            "reviewRating": {"ratingValue": "5"},
            "author": {"name": "Jane Doe"},
            "datePublished": "2024-04-10",
        },
        {
            "@id": "review-002",
            "reviewBody": "Beautiful views but trains run late.",
            "name": "Scenic but delayed",
            "reviewRating": {"ratingValue": "3"},
            "author": {"name": "John Smith"},
            "datePublished": "2024-03-20",
        },
    ],
}

HTML_WITH_JSON_LD = f"""
<html><head>
<script type="application/ld+json">{json.dumps(JSON_LD_REVIEW)}</script>
</head><body></body></html>
"""

HTML_NO_REVIEWS = "<html><body><p>No reviews yet.</p></body></html>"


def test_content_hash_stable():
    h1 = _content_hash("b1", "review-001")
    h2 = _content_hash("b1", "review-001")
    assert h1 == h2


def test_content_hash_differs_by_brand():
    assert _content_hash("b1", "r1") != _content_hash("b2", "r1")


def test_extract_json_ld_reviews_finds_reviews():
    soup = BeautifulSoup(HTML_WITH_JSON_LD, "lxml")
    reviews = _extract_json_ld_reviews(soup)
    assert len(reviews) == 2
    assert reviews[0]["@id"] == "review-001"


def test_extract_json_ld_reviews_empty_page():
    soup = BeautifulSoup(HTML_NO_REVIEWS, "lxml")
    reviews = _extract_json_ld_reviews(soup)
    assert reviews == []


def test_map_json_ld_review_structure():
    review = JSON_LD_REVIEW["review"][0]
    article = _map_json_ld_review(review, BRAND["id"], LISTING_URL)
    assert article is not None
    assert article["source_type"] == "tripadvisor_review"
    assert article["source_credibility"] == 0.82
    assert "★★★★★" in article["title"]
    assert "Breathtaking" in article["body"]
    assert article["author"] == "Jane Doe"


def test_map_json_ld_review_no_body_returns_none():
    review = {"@id": "empty", "reviewBody": "", "name": "", "reviewRating": {"ratingValue": "0"}}
    assert _map_json_ld_review(review, BRAND["id"], LISTING_URL) is None


def test_collect_disabled_returns_empty():
    assert collect_tripadvisor_for_brand(BRAND, CONFIG_OFF) == []


def test_collect_no_url_returns_empty():
    assert collect_tripadvisor_for_brand(BRAND, CONFIG_NO_URL) == []


def test_collect_success_json_ld():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = HTML_WITH_JSON_LD

    with patch("app.ingestion.tripadvisor_collector._fetch_with_retry", return_value=mock_resp):
        result = collect_tripadvisor_for_brand(BRAND, CONFIG_ON)

    assert len(result) == 2
    assert result[0]["portal_id"] == "tripadvisor"
    assert result[0]["brand_id"] == BRAND["id"]


def test_collect_handles_fetch_failure():
    with patch("app.ingestion.tripadvisor_collector._fetch_with_retry", return_value=None):
        result = collect_tripadvisor_for_brand(BRAND, CONFIG_ON)
    assert result == []
