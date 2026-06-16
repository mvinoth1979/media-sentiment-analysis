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
    app.dependency_overrides[get_current_user] = lambda: {"user_id": user_id, "email": "t@t.com"}
    return TestClient(app)


BRANDS = [
    {"id": "brand-1", "name": "Acme Cola", "agency_id": "agency-1"},
    {"id": "brand-2", "name": "Acme Snacks", "agency_id": "agency-2"},
    {"id": "brand-3", "name": "Globex Tea", "agency_id": "agency-2"},
]


def test_search_brands_only_returns_brands_for_users_own_agency():
    roles = [{"user_id": "user-in-agency-1", "agency_id": "agency-1", "brand_id": None}]
    fake_db = _FakeDB({"user_roles": roles, "brands": BRANDS})

    client = _make_client_as("user-in-agency-1")
    with patch("app.tenants.router.get_db", return_value=fake_db):
        resp = client.get("/tenants/brands")

    assert resp.status_code == 200
    ids = {b["id"] for b in resp.json()}
    assert ids == {"brand-1"}


def test_search_brands_includes_directly_granted_brand():
    roles = [{"user_id": "user-with-direct-grant", "agency_id": None, "brand_id": "brand-2"}]
    fake_db = _FakeDB({"user_roles": roles, "brands": BRANDS})

    client = _make_client_as("user-with-direct-grant")
    with patch("app.tenants.router.get_db", return_value=fake_db):
        resp = client.get("/tenants/brands")

    assert resp.status_code == 200
    ids = {b["id"] for b in resp.json()}
    assert ids == {"brand-2"}


def test_search_brands_with_no_roles_returns_nothing():
    fake_db = _FakeDB({"user_roles": [], "brands": BRANDS})

    client = _make_client_as("user-with-no-access")
    with patch("app.tenants.router.get_db", return_value=fake_db):
        resp = client.get("/tenants/brands")

    assert resp.status_code == 200
    assert resp.json() == []
