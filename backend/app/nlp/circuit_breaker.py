import threading
import time

_lock = threading.Lock()
_open_until = 0.0
COOLDOWN_SECONDS = 60


def is_open() -> bool:
    with _lock:
        return time.monotonic() < _open_until


def trip():
    global _open_until
    with _lock:
        _open_until = time.monotonic() + COOLDOWN_SECONDS
