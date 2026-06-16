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


def _make_client_as(user_id: str, roles: list[dict] | None = None):
    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
    from app.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": user_id, "email": "t@t.com", "roles": roles or [],
    }
    return TestClient(app)


BRANDS = [
    {"id": "brand-1", "name": "Acme Cola", "agency_id": "agency-1"},
    {"id": "brand-2", "name": "Acme Snacks", "agency_id": "agency-2"},
]

EMPTY_KPI = {"total": 0, "positive": 0, "negative": 0, "neutral": 0,
             "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0}


def test_overview_rejects_user_without_brand_access():
    fake_db = _FakeDB({"user_roles": [], "brands": BRANDS})
    client = _make_client_as("no-access-user")
    with patch("app.tenants.access.get_db", return_value=fake_db):
        resp = client.get("/dashboard/overview/brand-1")
    assert resp.status_code == 403


def test_overview_allowed_for_user_with_agency_grant():
    db_roles = [{"user_id": "admin-1", "agency_id": "agency-1", "brand_id": None}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS})
    client = _make_client_as("admin-1")
    with patch("app.tenants.access.get_db", return_value=fake_db), \
         patch("app.dashboard.router.get_kpi_summary", return_value=EMPTY_KPI), \
         patch("app.dashboard.router.query_sentiment_trend", return_value=[]), \
         patch("app.dashboard.router.get_articles", return_value=[]):
        resp = client.get("/dashboard/overview/brand-1")
    assert resp.status_code == 200


def test_overview_allowed_for_user_with_direct_brand_grant():
    db_roles = [{"user_id": "viewer-1", "agency_id": None, "brand_id": "brand-2"}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS})
    client = _make_client_as("viewer-1")
    with patch("app.tenants.access.get_db", return_value=fake_db), \
         patch("app.dashboard.router.get_kpi_summary", return_value=EMPTY_KPI), \
         patch("app.dashboard.router.query_sentiment_trend", return_value=[]), \
         patch("app.dashboard.router.get_articles", return_value=[]):
        resp = client.get("/dashboard/overview/brand-2")
    assert resp.status_code == 200


def test_mentions_rejects_user_without_brand_access():
    fake_db = _FakeDB({"user_roles": [], "brands": BRANDS})
    client = _make_client_as("no-access-user")
    with patch("app.tenants.access.get_db", return_value=fake_db):
        resp = client.get("/dashboard/mentions/brand-1")
    assert resp.status_code == 403


def test_mentions_allowed_for_user_with_brand_access():
    db_roles = [{"user_id": "admin-1", "agency_id": "agency-1", "brand_id": None}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS})
    client = _make_client_as("admin-1")
    with patch("app.tenants.access.get_db", return_value=fake_db), \
         patch("app.dashboard.router.get_articles", return_value=[]):
        resp = client.get("/dashboard/mentions/brand-1")
    assert resp.status_code == 200


def test_mentions_rejects_admin_of_a_different_agency():
    db_roles = [{"user_id": "admin-2", "agency_id": "agency-2", "brand_id": None}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS})
    client = _make_client_as("admin-2")
    with patch("app.tenants.access.get_db", return_value=fake_db):
        resp = client.get("/dashboard/mentions/brand-1")
    assert resp.status_code == 403
