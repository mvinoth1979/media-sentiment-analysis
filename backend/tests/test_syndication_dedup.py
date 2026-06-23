"""
Tests for story-level syndication deduplication (filter_syndicated).

Separate from test_deduplication.py which only covers filter_new_articles.
"""

from unittest.mock import MagicMock, patch, call


def _make_article(story_hash: str, title: str = "Test Article") -> dict:
    return {"story_hash": story_hash, "title": title, "content_hash": f"ch_{story_hash}"}


def _mock_db(existing_rows: list) -> MagicMock:
    """DB mock where existing_rows are pre-existing articles with story_hash."""
    mock = MagicMock()
    mock.table.return_value.select.return_value \
        .eq.return_value.in_.return_value \
        .gte.return_value.execute.return_value.data = existing_rows
    return mock


class TestFilterSyndicated:

    def test_empty_input_returns_empty(self):
        from app.ingestion.deduplication import filter_syndicated
        with patch("app.ingestion.deduplication.get_supabase", return_value=MagicMock()):
            new, count = filter_syndicated([], "brand-1")
        assert new == []
        assert count == 0

    def test_no_story_hashes_passes_all_through(self):
        from app.ingestion.deduplication import filter_syndicated
        articles = [{"title": "No hash article", "content_hash": "ch1"}]
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.in_.return_value \
            .gte.return_value.execute.return_value.data = []
        with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
            new, count = filter_syndicated(articles, "brand-1")
        assert new == articles
        assert count == 0

    def test_new_article_passes_through(self):
        from app.ingestion.deduplication import filter_syndicated
        article = _make_article("sh1")
        with patch("app.ingestion.deduplication.get_supabase", return_value=_mock_db([])):
            new, count = filter_syndicated([article], "brand-1")
        assert len(new) == 1
        assert count == 0

    def test_known_story_is_filtered_and_counted(self):
        from app.ingestion.deduplication import filter_syndicated
        existing = [{"id": "db-id-1", "story_hash": "sh1", "syndication_count": 1}]
        article = _make_article("sh1", "Same Story Different Portal")
        mock_db = _mock_db(existing)
        with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
            new, count = filter_syndicated([article], "brand-1")
        assert len(new) == 0
        assert count == 1
        # DB update should have been called to increment syndication_count
        mock_db.table.return_value.update.assert_called_once()

    def test_syndication_count_incremented_correctly(self):
        from app.ingestion.deduplication import filter_syndicated
        existing = [{"id": "db-id-1", "story_hash": "sh1", "syndication_count": 3}]
        article = _make_article("sh1")
        mock_db = _mock_db(existing)
        with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
            filter_syndicated([article], "brand-1")
        update_call = mock_db.table.return_value.update.call_args
        assert update_call[0][0]["syndication_count"] == 4  # 3 + 1

    def test_within_batch_duplicate_only_first_passes(self):
        """Same story_hash appearing twice in one batch → only first article kept."""
        from app.ingestion.deduplication import filter_syndicated
        articles = [
            _make_article("sh_dup", "Story from The Hindu"),
            _make_article("sh_dup", "Same Story from Times of India"),
        ]
        with patch("app.ingestion.deduplication.get_supabase", return_value=_mock_db([])):
            new, count = filter_syndicated(articles, "brand-1")
        assert len(new) == 1
        assert new[0]["title"] == "Story from The Hindu"
        assert count == 1

    def test_within_batch_duplicate_does_not_call_db_update(self):
        """Within-batch dedup (both new to DB) should not call DB update."""
        from app.ingestion.deduplication import filter_syndicated
        articles = [
            _make_article("sh_dup", "First occurrence"),
            _make_article("sh_dup", "Second occurrence"),
        ]
        mock_db = _mock_db([])
        with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
            filter_syndicated(articles, "brand-1")
        # No DB record exists → no update needed
        mock_db.table.return_value.update.assert_not_called()

    def test_mix_of_new_and_syndicated(self):
        from app.ingestion.deduplication import filter_syndicated
        existing = [{"id": "db-id-1", "story_hash": "sh_old", "syndication_count": 2}]
        articles = [
            _make_article("sh_new", "Brand new story"),
            _make_article("sh_old", "Republished story"),
        ]
        with patch("app.ingestion.deduplication.get_supabase", return_value=_mock_db(existing)):
            new, count = filter_syndicated(articles, "brand-1")
        assert len(new) == 1
        assert new[0]["story_hash"] == "sh_new"
        assert count == 1

    def test_db_row_with_none_id_skips_update(self):
        """Existing row with id=None (already incremented this run) → skip update."""
        from app.ingestion.deduplication import filter_syndicated
        existing = [{"id": None, "story_hash": "sh1", "syndication_count": 1}]
        article = _make_article("sh1")
        mock_db = _mock_db(existing)
        with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
            new, count = filter_syndicated([article], "brand-1")
        # Filtered out (known hash), but no DB update since id is None
        mock_db.table.return_value.update.assert_not_called()
        assert count == 1

    def test_multiple_articles_multiple_known_hashes(self):
        from app.ingestion.deduplication import filter_syndicated
        existing = [
            {"id": "id-1", "story_hash": "sh_a", "syndication_count": 1},
            {"id": "id-2", "story_hash": "sh_b", "syndication_count": 2},
        ]
        articles = [
            _make_article("sh_a"),
            _make_article("sh_b"),
            _make_article("sh_c"),  # new
        ]
        with patch("app.ingestion.deduplication.get_supabase", return_value=_mock_db(existing)):
            new, count = filter_syndicated(articles, "brand-1")
        assert len(new) == 1
        assert new[0]["story_hash"] == "sh_c"
        assert count == 2

    def test_null_syndication_count_treated_as_1(self):
        """syndication_count=None in DB → (None or 1) + 1 = 2 — no crash."""
        from app.ingestion.deduplication import filter_syndicated
        existing = [{"id": "id-1", "story_hash": "sh1", "syndication_count": None}]
        article = _make_article("sh1")
        mock_db = _mock_db(existing)
        with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
            filter_syndicated([article], "brand-1")
        update_call = mock_db.table.return_value.update.call_args
        assert update_call[0][0]["syndication_count"] == 2  # (None or 1) + 1
