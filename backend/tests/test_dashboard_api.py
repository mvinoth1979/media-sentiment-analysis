from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from jose import jwt


def _make_client():
    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
    return TestClient(app)


def _auth_header():
    from app.config import settings
    token = jwt.encode({"sub": "u1", "email": "t@t.com"},
                       settings.supabase_anon_key, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_overview_returns_200():
    client = _make_client()
    kpi = {"total": 5, "positive": 3, "negative": 1, "neutral": 1,
           "positive_pct": 60.0, "negative_pct": 20.0, "neutral_pct": 20.0}
    articles = []

    with patch("app.dashboard.router.get_kpi_summary", return_value=kpi), \
         patch("app.dashboard.router.query_sentiment_trend", return_value=[]), \
         patch("app.dashboard.router.get_articles", return_value=articles):
        resp = client.get("/dashboard/overview/brand-123", headers=_auth_header())

    assert resp.status_code == 200
    data = resp.json()
    assert "kpi" in data
    assert "trend" in data
    assert "recent_mentions" in data


def test_mentions_returns_200():
    client = _make_client()
    with patch("app.dashboard.router.get_articles", return_value=[]):
        resp = client.get("/dashboard/mentions/brand-123", headers=_auth_header())

    assert resp.status_code == 200


def test_overview_requires_auth():
    client = _make_client()
    resp = client.get("/dashboard/overview/brand-123")
    assert resp.status_code == 403


def test_overview_includes_wow_delta_fields():
    client = _make_client()
    kpi = {"total": 5, "positive": 3, "negative": 1, "neutral": 1,
           "positive_pct": 60.0, "negative_pct": 20.0, "neutral_pct": 20.0}

    with patch("app.dashboard.router.get_kpi_summary", return_value=kpi), \
         patch("app.dashboard.router.query_sentiment_trend", return_value=[]), \
         patch("app.dashboard.router.get_articles", return_value=[]):
        resp = client.get("/dashboard/overview/brand-123", headers=_auth_header())

    assert resp.status_code == 200
    kpi_out = resp.json()["kpi"]
    assert kpi_out["perception_score_delta"] is None
    assert kpi_out["mentions_delta_pct"] is None


def test_compute_wow_delta_with_previous_data():
    from app.dashboard.router import _compute_wow_delta

    current = {"count": 10, "perception_score": 70.0}
    previous = {"count": 5, "perception_score": 50.0}

    delta = _compute_wow_delta(current, previous)

    assert delta["perception_score_delta"] == 20.0
    assert delta["mentions_delta_pct"] == 100.0


def test_compute_wow_delta_with_no_previous_data():
    from app.dashboard.router import _compute_wow_delta

    current = {"count": 10, "perception_score": 70.0}
    previous = {"count": 0, "perception_score": 50.0}

    delta = _compute_wow_delta(current, previous)

    assert delta["perception_score_delta"] is None
    assert delta["mentions_delta_pct"] is None


# --- rejection knowledge tests ---

def test_extract_words_removes_stopwords():
    from app.storage.rejection_store import _extract_words

    words = _extract_words("CIPET opens new campus in Vijayawada")
    assert "the" not in words
    assert "in" not in words
    assert "cipet" in words
    assert "campus" in words
    assert "vijayawada" in words


def test_extract_words_filters_short_tokens():
    from app.storage.rejection_store import _extract_words

    words = _extract_words("No go up at it")
    assert words == []


def test_is_rejected_exact_url():
    from app.storage.rejection_store import is_rejected

    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"id": "abc"}
    ]

    with patch("app.storage.rejection_store.get_db", return_value=mock_db):
        result = is_rejected("brand-1", "https://example.com/article", "Some title")

    assert result is True


def test_is_rejected_similar_title():
    from app.storage.rejection_store import is_rejected

    stored_words = ["cipet", "campus", "vijayawada", "opens"]
    mock_db = MagicMock()
    # URL check returns no match
    mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    # Title words query returns stored rejections
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"title_words": stored_words}
    ]

    with patch("app.storage.rejection_store.get_db", return_value=mock_db):
        # "CIPET opens its new campus" → words: cipet, opens, campus → 3/3 = 100% overlap
        result = is_rejected("brand-1", "https://other.com/news", "CIPET opens its new campus")

    assert result is True


def test_is_rejected_unrelated_title_not_blocked():
    from app.storage.rejection_store import is_rejected

    stored_words = ["cipet", "campus", "vijayawada", "opens"]
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"title_words": stored_words}
    ]

    with patch("app.storage.rejection_store.get_db", return_value=mock_db):
        # "stock market rally india" → words: stock, market, rally, india → 0% overlap
        result = is_rejected("brand-1", "https://other.com/stocks", "Stock market rally india")

    assert result is False


def test_delete_mentions_endpoint():
    client = _make_client()
    article = {
        "id": "art-1", "brand_id": "brand-123",
        "url": "https://example.com/1", "title": "Test article",
        "portal_id": "test_portal", "language": "en",
    }

    with patch("app.dashboard.router.delete_articles", return_value=[article]) as mock_del, \
         patch("app.dashboard.router.save_rejections") as mock_save:
        resp = client.request(
            "DELETE",
            "/dashboard/mentions/brand-123",
            json={"ids": ["art-1"]},
            headers=_auth_header(),
        )

    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1
    mock_del.assert_called_once_with(["art-1"], "brand-123")
    mock_save.assert_called_once()
