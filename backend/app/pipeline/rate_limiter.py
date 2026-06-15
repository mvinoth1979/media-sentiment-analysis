import threading
import time


class _TokenBucket:
    """Thread-safe token bucket: refills `rate` tokens/minute, blocks on empty.

    Starts with 1 token (not `rate`) to prevent the initial burst that would
    otherwise let all threads fire simultaneously on startup.
    """

    def __init__(self, rate: int):
        self._rate = rate
        self._tokens = 1.0          # start with 1, not rate — avoids burst
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


# 12 RPM total NLP calls — shared across all threads and both providers
# (Gemini limit: 15 RPM; Groq limit: 30 RPM; 12 stays safely below both)
_nlp_bucket = _TokenBucket(rate=12)


def acquire_nlp_slot():
    _nlp_bucket.acquire()
