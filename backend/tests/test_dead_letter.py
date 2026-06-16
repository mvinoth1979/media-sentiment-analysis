import json
from unittest.mock import patch, MagicMock
from app.pipeline.dead_letter import push_to_dlq, retry_dead_letters, DLQ_KEY, MAX_RETRIES
from app.nlp.schemas import NLPResult


def _nlp_result():
    return NLPResult(0.7, "positive", ["Amul"], ["pricing"], ["good"],
                      "gemini-2.0-flash", 0.9)


def test_push_to_dlq_stores_article_with_retry_count():
    mock_redis = MagicMock()
    article = {"content_hash": "h1", "title": "t"}

    with patch("app.pipeline.dead_letter.get_redis", return_value=mock_redis):
        push_to_dlq(article, "b1")

    mock_redis.rpush.assert_called_once()
    call_args = mock_redis.rpush.call_args
    assert call_args[0][0] == DLQ_KEY
    payload = json.loads(call_args[0][1])
    assert payload["article"] == article
    assert payload["brand_id"] == "b1"
    assert payload["retry_count"] == 0


def test_retry_recovers_article_on_success():
    mock_redis = MagicMock()
    entry = json.dumps({"article": {"content_hash": "h1", "title": "t"},
                         "brand_id": "b1", "retry_count": 0})
    mock_redis.lpop.side_effect = [entry, None]

    with patch("app.pipeline.dead_letter.get_redis", return_value=mock_redis), \
         patch("app.pipeline.dead_letter.analyse_article", return_value=_nlp_result()), \
         patch("app.pipeline.dead_letter.archive_article"), \
         patch("app.pipeline.dead_letter.save_article"), \
         patch("app.pipeline.dead_letter.mark_article_seen"):
        stats = retry_dead_letters()

    assert stats == {"retried": 1, "recovered": 1, "dropped": 0}
    mock_redis.rpush.assert_not_called()


def test_retry_requeues_with_incremented_count_on_failure():
    mock_redis = MagicMock()
    entry = json.dumps({"article": {"content_hash": "h1", "title": "t"},
                         "brand_id": "b1", "retry_count": 1})
    mock_redis.lpop.side_effect = [entry, None]

    with patch("app.pipeline.dead_letter.get_redis", return_value=mock_redis), \
         patch("app.pipeline.dead_letter.analyse_article", return_value=None):
        stats = retry_dead_letters()

    assert stats == {"retried": 1, "recovered": 0, "dropped": 0}
    mock_redis.rpush.assert_called_once()
    payload = json.loads(mock_redis.rpush.call_args[0][1])
    assert payload["retry_count"] == 2


def test_retry_drops_after_max_retries():
    mock_redis = MagicMock()
    entry = json.dumps({"article": {"content_hash": "h1", "title": "t"},
                         "brand_id": "b1", "retry_count": MAX_RETRIES - 1})
    mock_redis.lpop.side_effect = [entry, None]

    with patch("app.pipeline.dead_letter.get_redis", return_value=mock_redis), \
         patch("app.pipeline.dead_letter.analyse_article", return_value=None):
        stats = retry_dead_letters()

    assert stats == {"retried": 1, "recovered": 0, "dropped": 1}
    mock_redis.rpush.assert_not_called()


def test_retry_respects_max_items():
    mock_redis = MagicMock()
    entry = json.dumps({"article": {"content_hash": "h1", "title": "t"},
                         "brand_id": "b1", "retry_count": 0})
    mock_redis.lpop.return_value = entry

    with patch("app.pipeline.dead_letter.get_redis", return_value=mock_redis), \
         patch("app.pipeline.dead_letter.analyse_article", return_value=None):
        stats = retry_dead_letters(max_items=3)

    assert stats["retried"] == 3
