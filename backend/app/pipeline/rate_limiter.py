import threading
import time

class _TokenBucket:
    """Thread-safe token bucket: refills `rate` tokens/minute, blocks on empty."""

    def __init__(self, rate: int):
        self._rate = rate
        self._tokens = float(rate)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self):
        while True:
            with self._lock:
                now = time.monotonic()
                self._tokens = min(
                    float(self._rate),
                    self._tokens + (now - self._last) * (self._rate / 60.0),
                )
                self._last = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / (self._rate / 60.0)
            time.sleep(wait)


# 14 RPM leaves a 1-call buffer below Gemini's 15 RPM free-tier ceiling.
_gemini_bucket = _TokenBucket(rate=14)


def acquire_gemini_slot():
    _gemini_bucket.acquire()
