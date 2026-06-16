from unittest.mock import patch

import pytest
from app.config import get_settings


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """app.main.app is a process-wide singleton; tests that use
    app.dependency_overrides must not leak overrides into unrelated tests."""
    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """Patch env vars and reset cached settings so tests get fresh config."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("INFLUXDB_URL", "https://test.influxdb.com")
    monkeypatch.setenv("INFLUXDB_TOKEN", "test-token")
    monkeypatch.setenv("INFLUXDB_ORG", "test-org")
    monkeypatch.setenv("INFLUXDB_BUCKET", "test-bucket")
    monkeypatch.setenv("R2_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("R2_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("UPSTASH_REDIS_HOST", "test.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_PORT", "6379")
    monkeypatch.setenv("UPSTASH_REDIS_PASSWORD", "test-pass")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-32-chars-minimum!!")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
