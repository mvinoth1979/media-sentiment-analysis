import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from app.config import get_settings

# ---------------------------------------------------------------------------
# The conftest patches "app.pipeline.scheduler.start_scheduler" which requires
# both `app.pipeline` and `app.pipeline.scheduler` to be present in sys.modules
# so that pkgutil.resolve_name can traverse the dotted path.
#
# Rather than importing the real scheduler (which has a deep chain of optional
# dependencies — apscheduler, redis, boto3, influxdb_client … — not all
# installed in the test virtualenv), we register a lightweight stub module that
# exposes just the `start_scheduler` name the patch targets.
# ---------------------------------------------------------------------------
import app.pipeline  # noqa: E402 — sets app.pipeline in sys.modules

if "app.pipeline.scheduler" not in sys.modules:
    _sched_stub = ModuleType("app.pipeline.scheduler")
    _sched_stub.start_scheduler = MagicMock()  # type: ignore[attr-defined]
    sys.modules["app.pipeline.scheduler"] = _sched_stub
    # Make the stub accessible as an attribute of the package object so that
    # getattr(app.pipeline, 'scheduler') works (required by pkgutil.resolve_name)
    import app.pipeline as _pipeline_pkg
    _pipeline_pkg.scheduler = _sched_stub  # type: ignore[attr-defined]


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
