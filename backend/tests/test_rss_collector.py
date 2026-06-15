from unittest.mock import patch, MagicMock
from app.ingestion.rss_collector import collect_portal, keyword_matches

def test_keyword_matches_exact():
    assert keyword_matches("Amul launches new product", ["Amul"]) is True

def test_keyword_matches_case_insensitive():
    assert keyword_matches("AMUL dairy products", ["amul"]) is True

def test_keyword_matches_no_match():
    assert keyword_matches("Cricket match results", ["Amul", "dairy"]) is False

def test_keyword_matches_partial_word_excluded():
    # "Amul" should not match "Ramul"
    assert keyword_matches("Ramul is a name", ["\\bAmul\\b"]) is False

def test_collect_portal_returns_articles():
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_entry = MagicMock()
    mock_entry.title = "Amul announces price cut"
    mock_entry.link = "https://thehindu.com/story/1"
    mock_entry.get.side_effect = lambda k, d=None: {
        "summary": "Amul reduced prices by 5%",
        "author": "Staff Reporter",
        "published": "Mon, 15 Jun 2026 10:00:00 +0000",
    }.get(k, d)
    mock_feed.entries = [mock_entry]

    with patch("app.ingestion.rss_collector.feedparser.parse", return_value=mock_feed):
        articles = collect_portal(
            portal={"id": "the_hindu", "name": "The Hindu",
                    "rss_url": "https://rss.url", "language": "en", "credibility": 0.92},
            keywords=["Amul"],
            brand_id="brand-uuid-123"
        )

    assert len(articles) == 1
    assert articles[0]["title"] == "Amul announces price cut"
    assert articles[0]["portal_id"] == "the_hindu"
    assert articles[0]["brand_id"] == "brand-uuid-123"

def test_collect_portal_filters_non_matching():
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_entry = MagicMock()
    mock_entry.title = "Cricket World Cup preview"
    mock_entry.link = "https://thehindu.com/story/2"
    mock_entry.get.side_effect = lambda k, d=None: {"summary": "India vs Australia"}.get(k, d)
    mock_feed.entries = [mock_entry]

    with patch("app.ingestion.rss_collector.feedparser.parse", return_value=mock_feed):
        articles = collect_portal(
            portal={"id": "the_hindu", "name": "The Hindu",
                    "rss_url": "https://rss.url", "language": "en", "credibility": 0.92},
            keywords=["Amul"],
            brand_id="brand-uuid-123"
        )

    assert len(articles) == 0
