from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) == val]
        return self

    def in_(self, col, vals):
        vals = set(vals)
        self._rows = [r for r in self._rows if r.get(col) in vals]
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows)


class _FakeDB:
    def __init__(self, tables):
        self._tables = tables

    def table(self, name):
        return _FakeQuery(list(self._tables.get(name, [])))


def _make_client_as(user_id: str):
    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
    from app.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": user_id, "email": "t@t.com", "roles": [],
    }
    return TestClient(app)


BRANDS = [{"id": "brand-1", "name": "Acme Cola", "agency_id": "agency-1"}]


def _grant_db():
    db_roles = [{"user_id": "admin-1", "agency_id": "agency-1", "brand_id": None}]
    return _FakeDB({"user_roles": db_roles, "brands": BRANDS})


def test_overview_includes_last_processed_timestamp():
    client = _make_client_as("admin-1")
    kpi = {"total": 2, "positive": 1, "negative": 1, "neutral": 0,
           "positive_pct": 50.0, "negative_pct": 50.0, "neutral_pct": 0.0}
    articles = [
        {"collected_at": "2026-06-16T08:00:00Z", "sentiment_label": "positive"},
        {"collected_at": "2026-06-15T08:00:00Z", "sentiment_label": "negative"},
    ]

    with patch("app.tenants.access.get_db", return_value=_grant_db()), \
         patch("app.dashboard.router.get_kpi_summary", return_value=kpi), \
         patch("app.dashboard.router.query_sentiment_trend", return_value=[]), \
         patch("app.dashboard.router.get_articles", return_value=articles):
        resp = client.get("/dashboard/overview/brand-1")

    assert resp.status_code == 200
    assert resp.json()["last_processed_at"] == "2026-06-16T08:00:00Z"


def test_overview_last_processed_is_none_when_no_articles():
    client = _make_client_as("admin-1")
    kpi = {"total": 0, "positive": 0, "negative": 0, "neutral": 0,
           "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0}

    with patch("app.tenants.access.get_db", return_value=_grant_db()), \
         patch("app.dashboard.router.get_kpi_summary", return_value=kpi), \
         patch("app.dashboard.router.query_sentiment_trend", return_value=[]), \
         patch("app.dashboard.router.get_articles", return_value=[]):
        resp = client.get("/dashboard/overview/brand-1")

    assert resp.status_code == 200
    assert resp.json()["last_processed_at"] is None
