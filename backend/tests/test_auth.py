from unittest.mock import patch
from fastapi.testclient import TestClient


def test_health_endpoint():
    # Import here to avoid triggering lifespan/scheduler during collection
    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
        client = TestClient(app)
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_verify_token_valid():
    import json
    from jose import jwt
    from unittest.mock import patch

    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
        from app.config import settings
        client = TestClient(app)

    token = jwt.encode(
        {"sub": "user-123", "email": "test@example.com"},
        settings.supabase_anon_key,
        algorithm="HS256",
    )
    resp = client.get("/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "user-123"


def test_verify_token_invalid():
    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
        client = TestClient(app)

    resp = client.get("/auth/verify", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401
