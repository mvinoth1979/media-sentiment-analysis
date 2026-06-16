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

TWELVE_TOPIC_ARTICLES = [
    {"topics": [f"topic-{i}"], "sentiment_label": "positive"}
    for i in range(12)
]


def test_topics_rejects_user_without_brand_access():
    fake_db = _FakeDB({"user_roles": [], "brands": BRANDS})
    client = _make_client_as("no-access-user")
    with patch("app.tenants.access.get_db", return_value=fake_db):
        resp = client.get("/dashboard/topics/brand-1")
    assert resp.status_code == 403


def test_topics_returns_all_topics_not_capped_at_ten():
    db_roles = [{"user_id": "admin-1", "agency_id": "agency-1", "brand_id": None}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS})
    client = _make_client_as("admin-1")
    with patch("app.tenants.access.get_db", return_value=fake_db), \
         patch("app.dashboard.router.get_articles", return_value=TWELVE_TOPIC_ARTICLES):
        resp = client.get("/dashboard/topics/brand-1")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 12


def test_topics_counts_one_article_toward_each_of_its_multiple_topics():
    db_roles = [{"user_id": "admin-1", "agency_id": "agency-1", "brand_id": None}]
    fake_db = _FakeDB({"user_roles": db_roles, "brands": BRANDS})
    client = _make_client_as("admin-1")
    articles = [
        {"topics": ["recycling", "environment"], "sentiment_label": "positive"},
        {"topics": ["recycling"], "sentiment_label": "negative"},
    ]
    with patch("app.tenants.access.get_db", return_value=fake_db), \
         patch("app.dashboard.router.get_articles", return_value=articles):
        resp = client.get("/dashboard/topics/brand-1")

    assert resp.status_code == 200
    by_topic = {t["topic"]: t for t in resp.json()}
    assert by_topic["recycling"]["count"] == 2
    assert by_topic["recycling"]["positive"] == 1
    assert by_topic["recycling"]["negative"] == 1
    assert by_topic["environment"]["count"] == 1
    assert by_topic["environment"]["positive"] == 1
