from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows
        self._pending_insert = None

    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) == val]
        return self

    def in_(self, col, vals):
        vals = set(vals)
        self._rows = [r for r in self._rows if r.get(col) in vals]
        return self

    def order(self, col, desc=False):
        self._rows = sorted(self._rows, key=lambda r: r.get(col), reverse=desc)
        return self

    def insert(self, row):
        self._pending_insert = row
        return self

    def execute(self):
        if self._pending_insert is not None:
            new_row = {"id": "ann-new", "created_at": "2026-06-16T10:00:00Z", **self._pending_insert}
            self._rows.append(new_row)
            return SimpleNamespace(data=[new_row])
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


def _grant_db(extra_tables: dict | None = None):
    db_roles = [{"user_id": "admin-1", "agency_id": "agency-1", "brand_id": None}]
    tables = {"user_roles": db_roles, "brands": BRANDS, **(extra_tables or {})}
    return _FakeDB(tables)


def test_create_annotation_inserts_and_returns_row():
    client = _make_client_as("admin-1")
    db = _grant_db({"trend_annotations": []})

    with patch("app.tenants.access.get_db", return_value=db), \
         patch("app.dashboard.router.get_db", return_value=db):
        resp = client.post(
            "/dashboard/trends/brand-1/annotations",
            json={"date": "2026-06-10", "label": "Product recall announced"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == "2026-06-10"
    assert body["label"] == "Product recall announced"
    assert body["created_by"] == "admin-1"


def test_list_annotations_returns_existing_rows_sorted_by_date():
    client = _make_client_as("admin-1")
    existing = [
        {"id": "ann-2", "brand_id": "brand-1", "date": "2026-06-12",
         "label": "Later event", "created_by": "admin-1", "created_at": "2026-06-12T00:00:00Z"},
        {"id": "ann-1", "brand_id": "brand-1", "date": "2026-06-05",
         "label": "Earlier event", "created_by": "admin-1", "created_at": "2026-06-05T00:00:00Z"},
    ]
    db = _grant_db({"trend_annotations": existing})

    with patch("app.tenants.access.get_db", return_value=db), \
         patch("app.dashboard.router.get_db", return_value=db):
        resp = client.get("/dashboard/trends/brand-1/annotations")

    assert resp.status_code == 200
    body = resp.json()
    assert [a["id"] for a in body] == ["ann-1", "ann-2"]


def test_create_annotation_requires_brand_access():
    client = _make_client_as("nobody")
    db = _grant_db({"trend_annotations": []})

    with patch("app.tenants.access.get_db", return_value=db), \
         patch("app.dashboard.router.get_db", return_value=db):
        resp = client.post(
            "/dashboard/trends/brand-1/annotations",
            json={"date": "2026-06-10", "label": "Should be blocked"},
        )

    assert resp.status_code == 403
