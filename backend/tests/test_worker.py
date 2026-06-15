from unittest.mock import patch, MagicMock, call
import json
from app.pipeline.worker import enqueue_brand, process_queue, QUEUE_KEY


def test_enqueue_brand_pushes_to_redis():
    mock_redis = MagicMock()
    brand = {"id": "b1", "name": "Amul"}
    config = {"keywords": ["Amul"], "languages": ["en"]}

    with patch("app.pipeline.worker.get_redis", return_value=mock_redis):
        enqueue_brand(brand, config)

    mock_redis.rpush.assert_called_once()
    call_args = mock_redis.rpush.call_args
    assert call_args[0][0] == QUEUE_KEY
    payload = json.loads(call_args[0][1])
    assert payload["brand"] == brand
    assert payload["config"] == config


def test_process_queue_processes_items():
    mock_redis = MagicMock()
    item = json.dumps({"brand": {"id": "b1"}, "config": {"keywords": []}})
    mock_redis.lpop.side_effect = [item, None]

    with patch("app.pipeline.worker.get_redis", return_value=mock_redis), \
         patch("app.pipeline.worker.run_brand_pipeline",
               return_value={"brand_id": "b1", "processed": 1}) as mock_pipeline:
        count = process_queue()

    assert count == 1
    mock_pipeline.assert_called_once_with({"id": "b1"}, {"keywords": []})


def test_process_queue_returns_zero_when_empty():
    mock_redis = MagicMock()
    mock_redis.lpop.return_value = None

    with patch("app.pipeline.worker.get_redis", return_value=mock_redis):
        count = process_queue()

    assert count == 0


def test_process_queue_continues_on_pipeline_error():
    mock_redis = MagicMock()
    item = json.dumps({"brand": {"id": "b1"}, "config": {}})
    mock_redis.lpop.side_effect = [item, None]

    with patch("app.pipeline.worker.get_redis", return_value=mock_redis), \
         patch("app.pipeline.worker.run_brand_pipeline", side_effect=Exception("boom")):
        count = process_queue()

    assert count == 1  # still counts the attempt


def test_process_queue_respects_max_items():
    mock_redis = MagicMock()
    item = json.dumps({"brand": {"id": "b1"}, "config": {}})
    mock_redis.lpop.return_value = item  # always returns item (no None)

    with patch("app.pipeline.worker.get_redis", return_value=mock_redis), \
         patch("app.pipeline.worker.run_brand_pipeline", return_value={}):
        count = process_queue(max_items=3)

    assert count == 3
