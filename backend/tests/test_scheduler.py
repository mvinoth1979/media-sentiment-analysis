from unittest.mock import MagicMock
from app.pipeline.scheduler import _order_by_staleness


def test_never_processed_brand_goes_first():
    brands = [{"id": "fresh", "name": "Fresh"}, {"id": "stale", "name": "Stale"}]
    db = MagicMock()
    db.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"brand_id": "fresh", "collected_at": "2026-06-16T10:00:00+00:00"},
    ]

    ordered = _order_by_staleness(db, brands)

    assert [b["id"] for b in ordered] == ["stale", "fresh"]


def test_oldest_collected_at_goes_before_newer():
    brands = [{"id": "newer", "name": "Newer"}, {"id": "older", "name": "Older"}]
    db = MagicMock()
    db.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"brand_id": "newer", "collected_at": "2026-06-16T10:00:00+00:00"},
        {"brand_id": "older", "collected_at": "2026-06-16T05:00:00+00:00"},
    ]

    ordered = _order_by_staleness(db, brands)

    assert [b["id"] for b in ordered] == ["older", "newer"]
