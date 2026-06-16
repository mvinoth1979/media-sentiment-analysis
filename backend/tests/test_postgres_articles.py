from types import SimpleNamespace
from unittest.mock import patch


class _FakeQuery:
    def __init__(self, rows):
        self._rows = list(rows)

    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) == val]
        return self

    def gte(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) >= val]
        return self

    def lte(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) <= val]
        return self

    def contains(self, col, vals):
        self._rows = [r for r in self._rows if set(vals) <= set(r.get(col) or [])]
        return self

    def ilike(self, col, pattern):
        needle = pattern.strip("%").lower()
        self._rows = [r for r in self._rows if needle in (r.get(col) or "").lower()]
        return self

    def order(self, *_a, **_k):
        return self

    def range(self, start, end):
        self._rows = self._rows[start:end + 1]
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows)


class _FakeDB:
    def __init__(self, tables):
        self._tables = tables

    def table(self, name):
        return _FakeQuery(list(self._tables.get(name, [])))


ARTICLES = [
    {"id": "a1", "brand_id": "brand-1", "portal_id": "thehindu",
     "topics": ["politics", "economy"], "collected_at": "2026-06-01T00:00:00Z",
     "title": "Economy grows steadily"},
    {"id": "a2", "brand_id": "brand-1", "portal_id": "dinamani",
     "topics": ["sports"], "collected_at": "2026-06-10T00:00:00Z",
     "title": "Cricket match update"},
    {"id": "a3", "brand_id": "brand-1", "portal_id": "thehindu",
     "topics": ["politics"], "collected_at": "2026-06-15T00:00:00Z",
     "title": "Election results announced"},
]


def test_get_articles_filters_by_portal_id():
    from app.storage.postgres import get_articles
    fake_db = _FakeDB({"articles": ARTICLES})

    with patch("app.storage.postgres.get_db", return_value=fake_db):
        rows = get_articles("brand-1", portal_id="thehindu")

    assert {r["id"] for r in rows} == {"a1", "a3"}


def test_get_articles_filters_by_topic():
    from app.storage.postgres import get_articles
    fake_db = _FakeDB({"articles": ARTICLES})

    with patch("app.storage.postgres.get_db", return_value=fake_db):
        rows = get_articles("brand-1", topic="sports")

    assert {r["id"] for r in rows} == {"a2"}


def test_get_articles_filters_by_date_range():
    from app.storage.postgres import get_articles
    fake_db = _FakeDB({"articles": ARTICLES})

    with patch("app.storage.postgres.get_db", return_value=fake_db):
        rows = get_articles("brand-1", date_from="2026-06-05T00:00:00Z",
                            date_to="2026-06-12T00:00:00Z")

    assert {r["id"] for r in rows} == {"a2"}


def test_get_articles_filters_by_text_search():
    from app.storage.postgres import get_articles
    fake_db = _FakeDB({"articles": ARTICLES})

    with patch("app.storage.postgres.get_db", return_value=fake_db):
        rows = get_articles("brand-1", q="election")

    assert {r["id"] for r in rows} == {"a3"}


def test_get_articles_combines_filters():
    from app.storage.postgres import get_articles
    fake_db = _FakeDB({"articles": ARTICLES})

    with patch("app.storage.postgres.get_db", return_value=fake_db):
        rows = get_articles("brand-1", portal_id="thehindu", topic="politics")

    assert {r["id"] for r in rows} == {"a1", "a3"}
