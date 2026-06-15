from unittest.mock import MagicMock, patch
from app.ingestion.deduplication import filter_new_articles


def _make_articles(hashes: list[str]) -> list[dict]:
    return [{"content_hash": h, "brand_id": "b1", "title": f"Article {h}"} for h in hashes]


def test_all_new_articles_pass_through():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value.data = []

    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles(_make_articles(["hash1", "hash2"]), "b1")

    assert len(result) == 2


def test_seen_articles_are_filtered():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value.data = [
        {"content_hash": "hash1"}
    ]

    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles(_make_articles(["hash1", "hash2"]), "b1")

    assert len(result) == 1
    assert result[0]["content_hash"] == "hash2"


def test_empty_input_returns_empty():
    mock_db = MagicMock()
    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles([], "b1")
    assert result == []


def test_all_seen_articles_returns_empty():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value.data = [
        {"content_hash": "hash1"},
        {"content_hash": "hash2"},
    ]

    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles(_make_articles(["hash1", "hash2"]), "b1")

    assert result == []
    # Verify no insert was attempted
    insert_calls = mock_db.table.return_value.insert.call_count
    assert insert_calls == 0
