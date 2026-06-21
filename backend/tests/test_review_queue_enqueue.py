"""Tests for Item 5: auto-enqueue in save_article when confidence is low
and issue_category is crisis_controversy or regulatory_compliance."""
from unittest.mock import MagicMock, patch, call


def _make_db(article_id="art-1"):
    """Return a MagicMock Supabase client that returns article_id on upsert."""
    db = MagicMock()
    db.table.return_value.upsert.return_value.execute.return_value.data = [{"id": article_id}]
    db.table.return_value.insert.return_value.execute.return_value.data = [{"id": "queue-1"}]
    return db


# ── enqueue trigger conditions ────────────────────────────────────────────────

def test_save_article_enqueues_when_low_confidence_crisis():
    """confidence < 0.5 + crisis_controversy → queue row inserted."""
    from app.storage.postgres import save_article

    article = {"brand_id": "brand-1", "url": "https://x.com", "content_hash": "abc"}
    nlp = {
        "confidence": 0.3,
        "issue_category": "crisis_controversy",
        "sentiment_label": "negative",
        "sentiment_score": 0.1,
    }

    db = _make_db()
    with patch("app.storage.postgres.get_db", return_value=db):
        result = save_article(article, nlp)

    assert result == "art-1"
    # insert should have been called once for the queue row
    insert_calls = [c for c in db.table.call_args_list if c.args[0] == "human_review_queue"]
    assert len(insert_calls) == 1


def test_save_article_enqueues_when_low_confidence_regulatory():
    """confidence < 0.5 + regulatory_compliance → queue row inserted."""
    from app.storage.postgres import save_article

    article = {"brand_id": "brand-1", "url": "https://x.com", "content_hash": "def"}
    nlp = {
        "confidence": 0.49,
        "issue_category": "regulatory_compliance",
        "sentiment_label": "negative",
        "sentiment_score": 0.2,
    }

    db = _make_db()
    with patch("app.storage.postgres.get_db", return_value=db):
        save_article(article, nlp)

    insert_calls = [c for c in db.table.call_args_list if c.args[0] == "human_review_queue"]
    assert len(insert_calls) == 1


def test_save_article_does_not_enqueue_when_confidence_high():
    """confidence >= 0.5 → no queue row even if crisis_controversy."""
    from app.storage.postgres import save_article

    article = {"brand_id": "brand-1", "url": "https://x.com", "content_hash": "ghi"}
    nlp = {
        "confidence": 0.5,
        "issue_category": "crisis_controversy",
        "sentiment_label": "negative",
        "sentiment_score": 0.1,
    }

    db = _make_db()
    with patch("app.storage.postgres.get_db", return_value=db):
        save_article(article, nlp)

    insert_calls = [c for c in db.table.call_args_list if c.args[0] == "human_review_queue"]
    assert len(insert_calls) == 0


def test_save_article_does_not_enqueue_non_sensitive_category():
    """confidence < 0.5 but category is 'financial_results' → no queue row."""
    from app.storage.postgres import save_article

    article = {"brand_id": "brand-1", "url": "https://x.com", "content_hash": "jkl"}
    nlp = {
        "confidence": 0.2,
        "issue_category": "financial_results",
        "sentiment_label": "negative",
        "sentiment_score": 0.1,
    }

    db = _make_db()
    with patch("app.storage.postgres.get_db", return_value=db):
        save_article(article, nlp)

    insert_calls = [c for c in db.table.call_args_list if c.args[0] == "human_review_queue"]
    assert len(insert_calls) == 0


def test_save_article_does_not_enqueue_when_no_confidence():
    """Missing confidence → no queue row (treat as high confidence)."""
    from app.storage.postgres import save_article

    article = {"brand_id": "brand-1", "url": "https://x.com", "content_hash": "mno"}
    nlp = {
        "issue_category": "crisis_controversy",
        "sentiment_label": "negative",
        "sentiment_score": 0.1,
    }

    db = _make_db()
    with patch("app.storage.postgres.get_db", return_value=db):
        save_article(article, nlp)

    insert_calls = [c for c in db.table.call_args_list if c.args[0] == "human_review_queue"]
    assert len(insert_calls) == 0


def test_save_article_queue_row_has_correct_fields():
    """Queue row inserted with brand_id, article_id, reason, status=pending."""
    from app.storage.postgres import save_article

    article = {"brand_id": "brand-42", "url": "https://x.com", "content_hash": "pqr"}
    nlp = {
        "confidence": 0.1,
        "issue_category": "crisis_controversy",
        "sentiment_label": "negative",
        "sentiment_score": 0.05,
    }

    db = _make_db(article_id="art-99")
    with patch("app.storage.postgres.get_db", return_value=db):
        save_article(article, nlp)

    # Find the insert call on human_review_queue
    queue_table_call = None
    for call_item in db.table.call_args_list:
        if call_item.args[0] == "human_review_queue":
            queue_table_call = call_item
            break

    assert queue_table_call is not None
    # The insert payload is the arg to .insert()
    insert_payload = db.table.return_value.insert.call_args.args[0]
    assert insert_payload["brand_id"] == "brand-42"
    assert insert_payload["article_id"] == "art-99"
    assert insert_payload["status"] == "pending"
    assert "reason" in insert_payload


def test_save_article_enqueue_failure_does_not_raise():
    """If inserting into human_review_queue fails, save_article still returns article_id."""
    from app.storage.postgres import save_article

    article = {"brand_id": "brand-1", "url": "https://x.com", "content_hash": "stu"}
    nlp = {
        "confidence": 0.2,
        "issue_category": "crisis_controversy",
        "sentiment_label": "negative",
        "sentiment_score": 0.1,
    }

    db = _make_db()
    # Make the queue insert raise
    db.table.return_value.insert.return_value.execute.side_effect = Exception("DB error")
    with patch("app.storage.postgres.get_db", return_value=db):
        result = save_article(article, nlp)

    # Article was still saved
    assert result == "art-1"
