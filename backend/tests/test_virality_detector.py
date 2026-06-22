"""
Tests for virality_detector.py (Item 3) and alerts._check_review_cluster (Item 7).

TDD approach: tests were written before the implementation.
All DB calls are mocked; no live Supabase connection is needed.
"""
from unittest.mock import patch, MagicMock
from datetime import date, timedelta

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(article_id: str, days_ago: int, views: int, comments: int, negative: int) -> dict:
    """Build a fake video_metrics_history row."""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return {
        "article_id": article_id,
        "snapshot_date": d,
        "view_count": views,
        "comment_count": comments,
        "negative_count": negative,
    }


# ---------------------------------------------------------------------------
# virality_detector — compute_virality_flags
# ---------------------------------------------------------------------------

class TestComputeViralityFlags:
    """Unit tests for compute_virality_flags()."""

    def _run(self, snapshots_by_article: dict, today_rows: list) -> list:
        """
        Patch get_db() so that:
        - history query returns snapshots_by_article[article_id]
        - today query returns today_rows (list of article dicts with reach_metadata)

        The mock tracks which article_id was used in the first .eq() call on the
        video_metrics_history table and returns the corresponding snapshots.
        """
        from app.pipeline.virality_detector import compute_virality_flags

        mock_db = MagicMock()

        def _make_articles_mock():
            """Mock chain for the articles table query."""
            m = MagicMock()
            # .select().eq().eq().gte().execute().data
            m.select.return_value.eq.return_value.eq.return_value\
             .gte.return_value.execute.return_value.data = today_rows
            return m

        def _make_history_mock():
            """Mock chain for video_metrics_history — captures article_id from first .eq()."""
            m = MagicMock()

            def _first_eq(field, value):
                """Called with ('article_id', <article_id>) on first .eq()."""
                article_id = value
                rows = snapshots_by_article.get(article_id, [])

                inner = MagicMock()
                # .eq(brand_id).gte(date).order().execute().data
                inner.eq.return_value.gte.return_value\
                     .order.return_value.execute.return_value.data = rows
                return inner

            m.select.return_value.eq.side_effect = _first_eq
            return m

        def _table_chain(table_name):
            if table_name == "articles":
                return _make_articles_mock()
            if table_name == "video_metrics_history":
                return _make_history_mock()
            return MagicMock()

        mock_db.table.side_effect = _table_chain

        with patch("app.pipeline.virality_detector.get_db", return_value=mock_db):
            return compute_virality_flags("brand-1")

    def test_returns_empty_when_no_youtube_articles(self):
        result = self._run({}, [])
        assert result == []

    def test_no_flag_when_below_3x_threshold(self):
        # 7-day avg views = 1000, today = 2999 → < 3×, no flag
        article_id = "art-1"
        history = [_make_snapshot(article_id, i, 1000, 10, 2) for i in range(1, 8)]
        today_rows = [{
            "id": article_id,
            "title": "Test Video",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 2999, "comment_count": 10},
            "negative_count": 2,
        }]
        result = self._run({article_id: history}, today_rows)
        assert result == []

    def test_view_spike_triggers_flag_level_1(self):
        # avg views = 1000, today = 3001 → > 3×  → flag
        article_id = "art-2"
        history = [_make_snapshot(article_id, i, 1000, 5, 1) for i in range(1, 8)]
        today_rows = [{
            "id": article_id,
            "title": "Viral Video",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 3001, "comment_count": 5},
            "negative_count": 1,
        }]
        result = self._run({article_id: history}, today_rows)
        assert len(result) == 1
        entry = result[0]
        assert entry["article_id"] == article_id
        assert entry["title"] == "Viral Video"
        assert "view_count" in entry["triggered_metrics"]
        assert entry["flag_level"] >= 1

    def test_comment_spike_triggers_flag(self):
        # avg comments = 10, today = 31 → > 3×
        article_id = "art-3"
        history = [_make_snapshot(article_id, i, 500, 10, 1) for i in range(1, 8)]
        today_rows = [{
            "id": article_id,
            "title": "Commented Video",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 500, "comment_count": 31},
            "negative_count": 1,
        }]
        result = self._run({article_id: history}, today_rows)
        assert len(result) == 1
        assert "comment_count" in result[0]["triggered_metrics"]

    def test_negative_spike_triggers_flag(self):
        # avg negatives = 5, today = 16 → > 3×
        article_id = "art-4"
        history = [_make_snapshot(article_id, i, 500, 10, 5) for i in range(1, 8)]
        today_rows = [{
            "id": article_id,
            "title": "Negative Video",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 500, "comment_count": 10},
            "negative_count": 16,
        }]
        result = self._run({article_id: history}, today_rows)
        assert len(result) == 1
        assert "negative_count" in result[0]["triggered_metrics"]

    def test_two_spikes_raises_flag_level(self):
        # views AND comments both spike → flag_level 2
        article_id = "art-5"
        history = [_make_snapshot(article_id, i, 1000, 10, 2) for i in range(1, 8)]
        today_rows = [{
            "id": article_id,
            "title": "Double Spike",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 3500, "comment_count": 35},
            "negative_count": 2,
        }]
        result = self._run({article_id: history}, today_rows)
        assert len(result) == 1
        entry = result[0]
        assert entry["flag_level"] >= 2
        assert "view_count" in entry["triggered_metrics"]
        assert "comment_count" in entry["triggered_metrics"]

    def test_all_three_spikes_gives_crisis_level_3(self):
        # All three metrics spike → flag_level 3
        article_id = "art-6"
        history = [_make_snapshot(article_id, i, 1000, 10, 5) for i in range(1, 8)]
        today_rows = [{
            "id": article_id,
            "title": "Crisis Video",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 4000, "comment_count": 40},
            "negative_count": 20,
        }]
        result = self._run({article_id: history}, today_rows)
        assert len(result) == 1
        entry = result[0]
        assert entry["flag_level"] == 3
        assert set(entry["triggered_metrics"]) == {"view_count", "comment_count", "negative_count"}

    def test_no_history_below_absolute_threshold_not_flagged(self):
        # Day 0: values below absolute thresholds (50K views / 500 comments) → no flag
        article_id = "art-7"
        today_rows = [{
            "id": article_id,
            "title": "No History Low",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 9999, "comment_count": 100},
            "negative_count": 50,
        }]
        result = self._run({article_id: []}, today_rows)
        assert result == []

    def test_no_history_above_absolute_threshold_flagged(self):
        # Day 0: views > 50K OR comments > 500 → flag even without history
        article_id = "art-7b"
        today_rows = [{
            "id": article_id,
            "title": "Instant Viral",
            "url": "https://yt.test/v",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 60000, "comment_count": 600},
            "negative_count": 10,
        }]
        result = self._run({article_id: []}, today_rows)
        assert len(result) == 1
        assert result[0]["flag_level"] >= 1
        assert result[0]["history_days"] == 0
        assert "view_count" in result[0]["triggered_metrics"]
        assert "comment_count" in result[0]["triggered_metrics"]

    def test_multiple_articles_flagged_independently(self):
        art1, art2 = "art-8", "art-9"
        h1 = [_make_snapshot(art1, i, 100, 5, 1) for i in range(1, 8)]
        h2 = [_make_snapshot(art2, i, 200, 8, 2) for i in range(1, 8)]
        today_rows = [
            {
                "id": art1,
                "title": "Video 1",
                "source_type": "youtube_video",
                # art1: avg views=100 → 3×=300; today=280 → no spike
                #        avg comments=5 → 3×=15; today=5 → no spike
                "reach_metadata": {"view_count": 280, "comment_count": 5},
                "negative_count": 1,
            },
            {
                "id": art2,
                "title": "Video 2",
                "source_type": "youtube_video",
                # art2: avg comments=8 → 3×=24; today=25 → spike!
                "reach_metadata": {"view_count": 400, "comment_count": 25},
                "negative_count": 2,
            },
        ]
        # Only art2 has a comment spike (avg 8, today 25 > 24)
        result = self._run({art1: h1, art2: h2}, today_rows)
        ids = [r["article_id"] for r in result]
        assert art2 in ids
        assert art1 not in ids

    def test_flag_level_is_integer(self):
        article_id = "art-10"
        history = [_make_snapshot(article_id, i, 1000, 10, 5) for i in range(1, 8)]
        today_rows = [{
            "id": article_id,
            "title": "Type Check",
            "source_type": "youtube_video",
            "reach_metadata": {"view_count": 4000, "comment_count": 5},
            "negative_count": 5,
        }]
        result = self._run({article_id: history}, today_rows)
        if result:
            assert isinstance(result[0]["flag_level"], int)


# ---------------------------------------------------------------------------
# virality_detector — save_snapshot
# ---------------------------------------------------------------------------

class TestSaveSnapshot:
    def test_upserts_row_to_db(self):
        from app.pipeline.virality_detector import save_snapshot

        mock_db = MagicMock()
        mock_db.table.return_value.upsert.return_value.execute.return_value.data = [{"id": 1}]

        with patch("app.pipeline.virality_detector.get_db", return_value=mock_db):
            save_snapshot(
                article_id="art-1",
                brand_id="brand-1",
                view_count=5000,
                comment_count=200,
                negative_count=30,
            )

        mock_db.table.assert_called_once_with("video_metrics_history")
        upsert_call = mock_db.table.return_value.upsert.call_args
        row = upsert_call[0][0]
        assert row["article_id"] == "art-1"
        assert row["brand_id"] == "brand-1"
        assert row["view_count"] == 5000
        assert row["comment_count"] == 200
        assert row["negative_count"] == 30
        assert "snapshot_date" in row

    def test_save_snapshot_handles_db_error_gracefully(self):
        from app.pipeline.virality_detector import save_snapshot

        mock_db = MagicMock()
        mock_db.table.return_value.upsert.side_effect = Exception("DB down")

        with patch("app.pipeline.virality_detector.get_db", return_value=mock_db):
            # Should not raise
            save_snapshot("art-1", "brand-1", 100, 10, 2)


# ---------------------------------------------------------------------------
# alerts._check_review_cluster (Item 7)
# ---------------------------------------------------------------------------

class TestCheckReviewCluster:
    """Unit tests for alerts._check_review_cluster()."""

    def _run(self, db_rows: list, threshold: int = 3):
        from app.storage.alerts import _check_review_cluster

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value\
            .eq.return_value.eq.return_value\
            .gte.return_value.not_.is_.return_value\
            .execute.return_value.data = db_rows

        with patch("app.storage.alerts.get_db", return_value=mock_db):
            return _check_review_cluster("brand-1", threshold)

    def test_returns_none_when_no_negative_articles(self):
        result = self._run([])
        assert result is None

    def test_returns_none_when_below_threshold(self):
        # 2 articles in "Product Quality" but threshold=3
        rows = [
            {"issue_category": "Product Quality"},
            {"issue_category": "Product Quality"},
        ]
        result = self._run(rows, threshold=3)
        assert result is None

    def test_returns_count_and_category_when_at_threshold(self):
        rows = [{"issue_category": "Customer Service"}] * 3
        result = self._run(rows, threshold=3)
        assert result is not None
        count, category = result
        assert count == 3
        assert category == "Customer Service"

    def test_returns_dominant_category_when_multiple(self):
        rows = (
            [{"issue_category": "Pricing"} for _ in range(5)] +
            [{"issue_category": "Product Quality"} for _ in range(2)]
        )
        result = self._run(rows, threshold=3)
        assert result is not None
        count, category = result
        assert category == "Pricing"
        assert count == 5

    def test_ignores_null_issue_category(self):
        # 5 rows but category is None → should not trigger
        rows = [{"issue_category": None}] * 5
        result = self._run(rows, threshold=3)
        assert result is None

    def test_threshold_is_respected_exactly(self):
        # Exactly at threshold=4
        rows = [{"issue_category": "Shipping"} for _ in range(4)]
        result = self._run(rows, threshold=4)
        assert result is not None
        count, _ = result
        assert count == 4

    def test_returns_tuple_types(self):
        rows = [{"issue_category": "Refunds"}] * 5
        result = self._run(rows, threshold=3)
        assert result is not None
        count, category = result
        assert isinstance(count, int)
        assert isinstance(category, str)


# ---------------------------------------------------------------------------
# alerts.check_and_fire_alerts — review_cluster alert type (integration)
# ---------------------------------------------------------------------------

class TestCheckAndFireAlertsReviewCluster:
    """Verify review_cluster alert type wired into check_and_fire_alerts."""

    def test_review_cluster_alert_fires_when_triggered(self):
        from app.storage.alerts import check_and_fire_alerts

        configs = [{
            "id": "cfg-1",
            "alert_type": "review_cluster",
            "threshold": 3.0,
            "notify_email": "test@example.com",
            "enabled": True,
            "last_triggered_at": None,
        }]

        with patch("app.storage.alerts.settings") as mock_settings, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._check_review_cluster", return_value=(5, "Pricing")) as mock_check, \
             patch("app.storage.alerts._send_alert_email") as mock_send, \
             patch("app.storage.alerts.get_db") as mock_get_db:
            mock_settings.resend_api_key = "test-key"
            mock_get_db.return_value.table.return_value.update.return_value\
                .eq.return_value.execute.return_value.data = []
            check_and_fire_alerts(
                brand_id="brand-1",
                brand_name="TestBrand",
                perception_score=60.0,
                negative_pct=30.0,
                mention_count=100,
            )

        mock_check.assert_called_once_with("brand-1", 3)
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        assert call_kwargs[0][2] == "review_cluster"

    def test_review_cluster_does_not_fire_below_threshold(self):
        from app.storage.alerts import check_and_fire_alerts

        configs = [{
            "id": "cfg-2",
            "alert_type": "review_cluster",
            "threshold": 5.0,
            "notify_email": "test@example.com",
            "enabled": True,
            "last_triggered_at": None,
        }]

        with patch("app.storage.alerts.settings") as mock_settings, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._check_review_cluster", return_value=None), \
             patch("app.storage.alerts._send_alert_email") as mock_send:
            mock_settings.resend_api_key = "test-key"
            check_and_fire_alerts(
                brand_id="brand-1",
                brand_name="TestBrand",
                perception_score=60.0,
                negative_pct=30.0,
                mention_count=100,
            )

        mock_send.assert_not_called()
