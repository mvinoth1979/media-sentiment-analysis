import pytest
from unittest.mock import patch
from app.main import _queue_loop


@pytest.mark.asyncio
async def test_queue_loop_runs_process_queue_and_retry_dead_letters():
    with patch("app.pipeline.worker.process_queue") as mock_process, \
         patch("app.pipeline.dead_letter.retry_dead_letters") as mock_retry, \
         patch("asyncio.sleep", side_effect=StopAsyncIteration):
        with pytest.raises(StopAsyncIteration):
            await _queue_loop()

    mock_process.assert_called_once_with(max_items=50)
    mock_retry.assert_called_once()
