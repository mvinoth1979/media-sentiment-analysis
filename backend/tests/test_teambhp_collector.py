"""Tests for Team-BHP collector."""

import pytest
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from app.ingestion.teambhp_collector import (
    _content_hash,
    _parse_search_results,
    collect_teambhp_for_brand,
)

BRAND = {"id": "brand-maruti-001"}
CONFIG_ON  = {"team_bhp_enabled": True,  "team_bhp_keywords": ["Maruti Swift", "Maruti Baleno"]}
CONFIG_OFF = {"team_bhp_enabled": False, "team_bhp_keywords": ["Maruti Swift"]}
CONFIG_NO_KW = {"team_bhp_enabled": True, "team_bhp_keywords": []}

HTML_SEARCH = """
<html><body>
<article class="post">
  <h2 class="entry-title"><a href="https://www.team-bhp.com/reviews/maruti-swift-2024">Maruti Swift 2024 Review</a></h2>
  <div class="entry-excerpt"><p>The new Swift is surprisingly refined for its class.</p></div>
  <time datetime="2024-05-01T10:00:00">May 1, 2024</time>
</article>
<article class="post">
  <h2 class="entry-title"><a href="https://www.team-bhp.com/forum/ownership-reviews/swift-ownership">Swift 1-year ownership</a></h2>
  <div class="entry-excerpt"><p>Running the Swift for 15,000 km — here is what I found.</p></div>
  <time datetime="2024-03-15T08:00:00">Mar 15, 2024</time>
</article>
</body></html>
"""

HTML_NO_RESULTS = "<html><body><p>No results found.</p></body></html>"


def test_content_hash_stable():
    h1 = _content_hash("b1", "https://team-bhp.com/x")
    h2 = _content_hash("b1", "https://team-bhp.com/x")
    assert h1 == h2


def test_content_hash_differs_by_brand():
    assert _content_hash("b1", "url") != _content_hash("b2", "url")


def test_parse_search_results_extracts_articles():
    soup = BeautifulSoup(HTML_SEARCH, "lxml")
    articles = _parse_search_results(soup, "Maruti Swift", BRAND["id"])
    assert len(articles) == 2
    assert articles[0]["url"] == "https://www.team-bhp.com/reviews/maruti-swift-2024"
    assert "Swift" in articles[0]["title"]


def test_parse_search_results_empty_page():
    soup = BeautifulSoup(HTML_NO_RESULTS, "lxml")
    articles = _parse_search_results(soup, "Maruti Swift", BRAND["id"])
    assert articles == []


def test_parse_article_fields():
    soup = BeautifulSoup(HTML_SEARCH, "lxml")
    articles = _parse_search_results(soup, "Maruti Swift", BRAND["id"])
    a = articles[0]
    assert a["source_type"] == "team_bhp_review"
    assert a["source_credibility"] == 0.80
    assert a["portal_id"] == "team_bhp"
    assert a["brand_id"] == BRAND["id"]
    assert a["reach_metadata"]["keyword"] == "Maruti Swift"


def test_collect_disabled_returns_empty():
    assert collect_teambhp_for_brand(BRAND, CONFIG_OFF) == []


def test_collect_no_keywords_returns_empty():
    assert collect_teambhp_for_brand(BRAND, CONFIG_NO_KW) == []


def test_collect_deduplicates_same_url():
    # If two keywords both return the same article URL, only one should be kept
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = HTML_SEARCH  # same HTML for both keyword searches

    with patch("app.ingestion.teambhp_collector._fetch_with_retry", return_value=mock_resp):
        with patch("app.ingestion.teambhp_collector.time.sleep"):
            result = collect_teambhp_for_brand(BRAND, CONFIG_ON)

    urls = [a["url"] for a in result]
    assert len(urls) == len(set(urls)), "Duplicate URLs found"


def test_collect_handles_fetch_failure():
    with patch("app.ingestion.teambhp_collector._fetch_with_retry", return_value=None):
        result = collect_teambhp_for_brand(BRAND, CONFIG_ON)
    assert result == []


def test_collect_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = HTML_SEARCH

    with patch("app.ingestion.teambhp_collector._fetch_with_retry", return_value=mock_resp):
        with patch("app.ingestion.teambhp_collector.time.sleep"):
            result = collect_teambhp_for_brand(BRAND, {"team_bhp_enabled": True, "team_bhp_keywords": ["Maruti Swift"]})

    assert len(result) == 2
    assert all(a["portal_id"] == "team_bhp" for a in result)
