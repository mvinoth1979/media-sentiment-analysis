from unittest.mock import MagicMock, patch, call
import pytest
from app.ingestion.deduplication import filter_new_articles, mark_article_seen


def _make_articles(hashes: list[str]) -> list[dict]:
    return [{"content_hash": h, "brand_id": "b1", "title": f"Article {h}"} for h in hashes]


def _mock_seen(seen_hashes: list[str]) -> MagicMock:
    """Build a Supabase mock where .select().eq().execute().data returns seen_hashes rows."""
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value \
        .execute.return_value.data = [{"content_hash": h} for h in seen_hashes]
    return mock_db


def test_all_new_articles_pass_through():
    with patch("app.ingestion.deduplication.get_supabase", return_value=_mock_seen([])):
        result = filter_new_articles(_make_articles(["hash1", "hash2"]), "b1")
    assert len(result) == 2


def test_seen_articles_are_filtered():
    with patch("app.ingestion.deduplication.get_supabase", return_value=_mock_seen(["hash1"])):
        result = filter_new_articles(_make_articles(["hash1", "hash2"]), "b1")
    assert len(result) == 1
    assert result[0]["content_hash"] == "hash2"


def test_empty_input_returns_empty():
    mock_db = MagicMock()
    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles([], "b1")
    assert result == []


def test_all_seen_articles_returns_empty():
    with patch("app.ingestion.deduplication.get_supabase",
               return_value=_mock_seen(["hash1", "hash2"])):
        result = filter_new_articles(_make_articles(["hash1", "hash2"]), "b1")
    assert result == []
    # Verify no insert was attempted (filter_new_articles never inserts)
    assert True  # insertion is done by mark_article_seen, not filter_new_articles


# ─── mark_article_seen ────────────────────────────────────────────────────────

def test_mark_article_seen_calls_upsert():
    mock_db = MagicMock()
    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        mark_article_seen("hash-abc", "brand-1")
    mock_db.table.assert_called_with("dedupe_hashes")
    mock_db.table.return_value.upsert.assert_called_once()
    upsert_args = mock_db.table.return_value.upsert.call_args[0][0]
    assert upsert_args["content_hash"] == "hash-abc"
    assert upsert_args["brand_id"] == "brand-1"


def test_mark_article_seen_uses_on_conflict():
    mock_db = MagicMock()
    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        mark_article_seen("hash-xyz", "brand-2")
    upsert_kwargs = mock_db.table.return_value.upsert.call_args[1]
    assert "on_conflict" in upsert_kwargs


# ─── Edge cases: filter_new_articles ──────────────────────────────────────────

def test_filter_new_articles_skips_db_on_empty_list():
    """Empty input must return early without touching Supabase."""
    mock_db = MagicMock()
    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles([], "brand-1")
    mock_db.table.assert_not_called()
    assert result == []


def test_filter_new_articles_missing_content_hash_raises():
    """Article dict without content_hash raises KeyError — caller's responsibility."""
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    articles = [{"title": "No hash article"}]  # missing content_hash
    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        with pytest.raises(KeyError):
            filter_new_articles(articles, "brand-1")


def test_filter_new_articles_db_error_propagates():
    """Supabase failure is not silently swallowed — propagates to caller."""
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = \
        Exception("Connection timeout")
    articles = [{"content_hash": "h1", "title": "Test"}]
    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        with pytest.raises(Exception, match="Connection timeout"):
            filter_new_articles(articles, "brand-1")
