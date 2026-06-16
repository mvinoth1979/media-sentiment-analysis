import pytest
from unittest.mock import patch
from app.main import _queue_loop, lifespan, app
from app.config import get_settings


@pytest.mark.asyncio
async def test_queue_loop_runs_process_queue_and_retry_dead_letters():
    with patch("app.pipeline.worker.process_queue") as mock_process, \
         patch("app.pipeline.dead_letter.retry_dead_letters") as mock_retry, \
         patch("asyncio.sleep", side_effect=StopAsyncIteration):
        with pytest.raises(StopAsyncIteration):
            await _queue_loop()

    mock_process.assert_called_once_with(max_items=50)
    mock_retry.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_skips_scheduler_when_disabled(monkeypatch):
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    get_settings.cache_clear()
    with patch("app.main.start_scheduler") as mock_start, \
         patch("asyncio.create_task") as mock_task:
        async with lifespan(app):
            pass

    mock_start.assert_not_called()
    mock_task.assert_not_called()


@pytest.mark.asyncio
async def test_lifespan_starts_scheduler_when_not_disabled(monkeypatch):
    monkeypatch.setenv("DISABLE_SCHEDULER", "false")
    get_settings.cache_clear()
    with patch("app.main.start_scheduler") as mock_start, \
         patch("asyncio.create_task") as mock_task:
        async with lifespan(app):
            pass

    mock_start.assert_called_once()
    mock_task.assert_called_once()
