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
