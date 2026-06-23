"""
Tests for article rejection store (app.storage.rejection_store).

Covers: _extract_words, is_rejected (URL match + title overlap), save_rejections.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from app.storage.rejection_store import (
    _extract_words,
    is_rejected,
    save_rejections,
    SIMILARITY_THRESHOLD,
)


# ─── _extract_words ────────────────────────────────────────────────────────────

class TestExtractWords:

    def test_strips_stopwords(self):
        words = _extract_words("the company is launching a new product")
        assert "the" not in words
        assert "is" not in words
        assert "a" not in words

    def test_returns_meaningful_words(self):
        words = _extract_words("Amul launches new product line")
        assert "amul" in words
        assert "launches" in words
        assert "product" in words
        assert "line" in words

    def test_minimum_word_length_3_chars(self):
        # "is", "in", "on" are 2 chars — excluded by regex \b[a-z]{3,}\b
        words = _extract_words("go to it on in at")
        assert words == []

    def test_empty_string_returns_empty(self):
        assert _extract_words("") == []

    def test_all_stopwords_returns_empty(self):
        words = _extract_words("the and or but in on")
        assert words == []

    def test_mixed_case_lowercased(self):
        words = _extract_words("Amul Dairy Products")
        assert "amul" in words
        assert "dairy" in words
        assert "products" in words

    def test_numbers_excluded(self):
        words = _extract_words("company earned 5000 crores")
        assert "5000" not in words

    def test_punctuation_stripped(self):
        words = _extract_words("company's products, prices, quality!")
        assert "company" in words or "products" in words


# ─── is_rejected ──────────────────────────────────────────────────────────────

def _make_db(exact_match: bool = False, stored_title_words: list[list] = None):
    """Build a mock DB with controlled behaviour."""
    mock_db = MagicMock()

    # Exact URL match chain
    exact_result = MagicMock()
    exact_result.data = [{"id": "r1"}] if exact_match else []
    mock_db.table.return_value.select.return_value \
        .eq.return_value.eq.return_value \
        .limit.return_value.execute.return_value = exact_result

    # Title word overlap chain
    stored_rows = [{"title_words": words} for words in (stored_title_words or [])]
    overlap_result = MagicMock()
    overlap_result.data = stored_rows

    # Second call to .select().eq().execute() returns overlap rows
    # We patch get_db to return the same mock, so we need to handle both call patterns.
    # Use side_effect on select to differentiate exact vs overlap queries.
    call_count = {"n": 0}

    def select_side_effect(fields):
        call_count["n"] += 1
        m = MagicMock()
        if call_count["n"] == 1:
            # First select: exact URL match ("id")
            m.eq.return_value.eq.return_value.limit.return_value.execute.return_value = exact_result
        else:
            # Second select: title words ("title_words")
            m.eq.return_value.execute.return_value = overlap_result
        return m

    mock_db.table.return_value.select.side_effect = select_side_effect
    return mock_db


class TestIsRejected:

    def test_exact_url_match_returns_true(self):
        mock_db = _make_db(exact_match=True)
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            result = is_rejected("brand-1", "https://example.com/story", "Any Title")
        assert result is True

    def test_no_match_returns_false(self):
        mock_db = _make_db(exact_match=False, stored_title_words=[])
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            result = is_rejected("brand-1", "https://new.com/story", "New Unrelated Title")
        assert result is False

    def test_title_word_overlap_above_threshold_returns_true(self):
        # Candidate: "amul dairy recall"  → words: [amul, dairy, recall]
        # Stored: [amul, dairy, recall, products] → overlap = 3/3 = 1.0 >= 0.6
        stored = [["amul", "dairy", "recall", "products"]]
        mock_db = _make_db(exact_match=False, stored_title_words=stored)
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            result = is_rejected("brand-1", "https://new.com/a", "Amul Dairy Recall Notice")
        assert result is True

    def test_title_word_overlap_below_threshold_returns_false(self):
        # Candidate: "amul launches product" → words: [amul, launches, product]
        # Stored: [amul, dairy, milk, recall, factory] → overlap = 1/3 = 0.33 < 0.6
        stored = [["amul", "dairy", "milk", "recall", "factory"]]
        mock_db = _make_db(exact_match=False, stored_title_words=stored)
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            result = is_rejected("brand-1", "https://new.com/b", "Amul Launches Product")
        assert result is False

    def test_empty_candidate_words_returns_false(self):
        # Title is all stopwords → candidate set empty → returns False immediately
        stored = [["amul", "dairy"]]
        mock_db = _make_db(exact_match=False, stored_title_words=stored)
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            result = is_rejected("brand-1", "https://x.com/c", "The and or but")
        assert result is False

    def test_empty_stored_words_skipped(self):
        # Stored row has empty title_words → should not divide by zero
        stored = [[], ["amul", "quality"]]
        mock_db = _make_db(exact_match=False, stored_title_words=stored)
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            result = is_rejected("brand-1", "https://x.com/d", "Amul Quality Issue")
        # Should not raise ZeroDivisionError
        assert isinstance(result, bool)

    def test_stored_none_title_words_skipped(self):
        stored_with_none = [None, ["amul", "problem", "service"]]

        mock_db = MagicMock()
        exact_result = MagicMock()
        exact_result.data = []
        overlap_result = MagicMock()
        overlap_result.data = [{"title_words": None}, {"title_words": ["amul", "problem", "service"]}]

        call_count = {"n": 0}
        def select_side_effect(fields):
            call_count["n"] += 1
            m = MagicMock()
            if call_count["n"] == 1:
                m.eq.return_value.eq.return_value.limit.return_value.execute.return_value = exact_result
            else:
                m.eq.return_value.execute.return_value = overlap_result
            return m
        mock_db.table.return_value.select.side_effect = select_side_effect

        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            result = is_rejected("brand-1", "https://x.com/e", "Amul Problem Service")
        # Should not raise, row with None title_words is skipped
        assert isinstance(result, bool)


# ─── save_rejections ──────────────────────────────────────────────────────────

class TestSaveRejections:

    def test_inserts_rows_for_each_article(self):
        mock_db = MagicMock()
        articles = [
            {"id": "a1", "url": "https://x.com/1", "title": "Amul recall notice",
             "portal_id": "p1", "language": "en"},
            {"id": "a2", "url": "https://x.com/2", "title": "Price hike announced",
             "portal_id": "p2", "language": "en"},
        ]

        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            save_rejections("brand-1", articles, rejected_by="user")

        mock_db.table.assert_called_once_with("article_rejections")
        insert_call = mock_db.table.return_value.insert.call_args
        rows = insert_call[0][0]
        assert len(rows) == 2
        assert rows[0]["brand_id"] == "brand-1"
        assert rows[0]["article_url"] == "https://x.com/1"
        assert rows[0]["rejected_by"] == "user"
        assert isinstance(rows[0]["title_words"], list)

    def test_title_words_excludes_stopwords(self):
        mock_db = MagicMock()
        articles = [{"id": "a1", "url": "u", "title": "The Amul dairy products", "portal_id": None, "language": "en"}]

        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            save_rejections("brand-1", articles)

        rows = mock_db.table.return_value.insert.call_args[0][0]
        assert "the" not in rows[0]["title_words"]
        assert "amul" in rows[0]["title_words"]

    def test_empty_articles_list_skips_insert(self):
        mock_db = MagicMock()
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            save_rejections("brand-1", [])
        mock_db.table.return_value.insert.assert_not_called()

    def test_article_missing_url_uses_empty_string(self):
        mock_db = MagicMock()
        articles = [{"id": "a1", "title": "Something happened"}]  # no url
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            save_rejections("brand-1", articles)
        rows = mock_db.table.return_value.insert.call_args[0][0]
        assert rows[0]["article_url"] == ""

    def test_article_missing_title_uses_empty_string(self):
        mock_db = MagicMock()
        articles = [{"id": "a1", "url": "https://x.com"}]  # no title
        with patch("app.storage.rejection_store.get_db", return_value=mock_db):
            save_rejections("brand-1", articles)
        rows = mock_db.table.return_value.insert.call_args[0][0]
        assert rows[0]["title"] == ""
        assert rows[0]["title_words"] == []
