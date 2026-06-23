"""
Tests for NLP circuit breaker (app.nlp.circuit_breaker).

The circuit breaker is a module-level singleton — tests must reset state
between runs to avoid cross-test contamination.
"""

import time
import threading
from unittest.mock import patch
import pytest
import app.nlp.circuit_breaker as cb


@pytest.fixture(autouse=True)
def reset_circuit():
    """Reset the circuit to closed state before each test."""
    with cb._lock:
        cb._open_until = 0.0
    yield
    with cb._lock:
        cb._open_until = 0.0


class TestCircuitBreakerClosed:

    def test_initially_closed(self):
        assert cb.is_open() is False

    def test_closed_after_reset(self):
        cb.trip()
        with cb._lock:
            cb._open_until = 0.0
        assert cb.is_open() is False


class TestCircuitBreakerTrip:

    def test_trip_opens_circuit(self):
        cb.trip()
        assert cb.is_open() is True

    def test_trip_sets_cooldown_roughly_60s(self):
        before = time.monotonic()
        cb.trip()
        with cb._lock:
            until = cb._open_until
        # Should be ~60 seconds in the future
        assert until > before + 55
        assert until < before + 65

    def test_double_trip_is_idempotent_and_extends_window(self):
        cb.trip()
        with cb._lock:
            first_until = cb._open_until
        time.sleep(0.01)
        cb.trip()
        with cb._lock:
            second_until = cb._open_until
        # Second trip sets a later deadline
        assert second_until >= first_until

    def test_circuit_auto_closes_after_cooldown(self):
        # Fake a very short cooldown by setting _open_until in the past
        with cb._lock:
            cb._open_until = time.monotonic() - 1.0
        assert cb.is_open() is False

    def test_circuit_still_open_within_cooldown(self):
        with cb._lock:
            cb._open_until = time.monotonic() + 30.0
        assert cb.is_open() is True


class TestCircuitBreakerConcurrency:

    def test_concurrent_trip_calls_are_safe(self):
        errors = []

        def worker():
            try:
                cb.trip()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert cb.is_open() is True

    def test_concurrent_read_write_no_race(self):
        results = []
        errors = []

        def reader():
            for _ in range(50):
                try:
                    results.append(cb.is_open())
                except Exception as e:
                    errors.append(e)

        def writer():
            for _ in range(5):
                try:
                    cb.trip()
                    time.sleep(0.001)
                    with cb._lock:
                        cb._open_until = 0.0
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(5)]
        threads.append(threading.Thread(target=writer))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []

    def test_is_open_and_trip_return_correct_types(self):
        assert isinstance(cb.is_open(), bool)
        assert cb.trip() is None
