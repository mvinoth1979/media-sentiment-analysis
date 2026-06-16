from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows
        self._pending_update = None

    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) == val]
        return self

    def in_(self, col, vals):
        vals = set(vals)
        self._rows = [r for r in self._rows if r.get(col) in vals]
        return self

    def update(self, values):
        self._pending_update = values
        return self

    def execute(self):
        if self._pending_update is not None:
            for r in self._rows:
                r.update(self._pending_update)
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
    {"id": "brand-3", "name": "Globex Tea", "agency_id": "agency-2"},
]

BRAND_CONFIGS = [
    {"id": "cfg-1", "brand_id": "brand-1", "keywords": ["old-keyword"],
     "languages": ["en"], "states": [], "competitors": [], "portal_ids": []},
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


def test_update_brand_config_allowed_for_agency_admin_of_owning_agency():
    db_roles = [{"user_id": "admin-1", "agency_id": "agency-1", "brand_id": None}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS,
                        "brand_configs": [dict(c) for c in BRAND_CONFIGS]})

    client = _make_client_as(
        "admin-1",
        roles=[{"role": "agency_admin", "agency_id": "agency-1", "brand_id": None}],
    )
    with patch("app.tenants.router.get_db", return_value=fake_db):
        resp = client.put("/tenants/brands/brand-1/config", json={"keywords": ["new-keyword"]})

    assert resp.status_code == 200
    assert resp.json()["keywords"] == ["new-keyword"]


def test_update_brand_config_allowed_for_directly_granted_brand_admin():
    db_roles = [{"user_id": "brand-admin-1", "agency_id": None, "brand_id": "brand-1"}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS,
                        "brand_configs": [dict(c) for c in BRAND_CONFIGS]})

    client = _make_client_as(
        "brand-admin-1",
        roles=[{"role": "brand_admin", "agency_id": None, "brand_id": "brand-1"}],
    )
    with patch("app.tenants.router.get_db", return_value=fake_db):
        resp = client.put("/tenants/brands/brand-1/config", json={"competitors": ["RivalCo"]})

    assert resp.status_code == 200
    assert resp.json()["competitors"] == ["RivalCo"]


def test_update_brand_config_rejects_viewer_role():
    client = _make_client_as(
        "viewer-1",
        roles=[{"role": "brand_viewer", "agency_id": None, "brand_id": "brand-1"}],
    )
    with patch("app.tenants.router.get_db") as mock_get_db:
        resp = client.put("/tenants/brands/brand-1/config", json={"keywords": ["x"]})

    assert resp.status_code == 403
    mock_get_db.assert_not_called()


def test_update_brand_config_rejects_admin_of_a_different_agency():
    db_roles = [{"user_id": "admin-2", "agency_id": "agency-2", "brand_id": None}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS,
                        "brand_configs": [dict(c) for c in BRAND_CONFIGS]})

    client = _make_client_as(
        "admin-2",
        roles=[{"role": "agency_admin", "agency_id": "agency-2", "brand_id": None}],
    )
    with patch("app.tenants.router.get_db", return_value=fake_db):
        resp = client.put("/tenants/brands/brand-1/config", json={"keywords": ["x"]})

    assert resp.status_code == 403
