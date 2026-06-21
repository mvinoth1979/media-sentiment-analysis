"""Tests for Item 8: GET /dashboard/brand-risk-scores/{brand_id} endpoint
and review-queue endpoints."""
import math
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── client helper ─────────────────────────────────────────────────────────────

_MASTER_ADMIN_ROLES = [
    {"user_id": "admin-1", "role": "master_admin", "agency_id": None, "brand_id": None}
]


def _make_client_as_admin():
    """Create a TestClient with master_admin identity (bypasses all brand checks).

    The auth dependency checker re-queries user_roles from the DB even when
    get_current_user is overridden, so we also need a fake DB that returns
    the master_admin role row.
    """
    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
    from app.auth.dependencies import get_current_user

    # Fake DB that returns master_admin role for any user_id query
    fake_roles_db = _FakeDB({"user_roles": _MASTER_ADMIN_ROLES})

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "admin-1",
        "email": "admin@test.com",
        "roles": _MASTER_ADMIN_ROLES,
    }

    # We'll return a contextmanager-style client that also patches auth get_db
    client = TestClient(app)
    client._auth_db_patcher = patch("app.auth.dependencies.get_db", return_value=fake_roles_db)
    client._auth_db_patcher.start()
    return client


class _FakeQuery:
    """Minimal Supabase query mock that chains .select/.eq/.in_/.gte/.order/.limit."""
    def __init__(self, rows):
        self._rows = list(rows)

    def select(self, *_a, **_k): return self
    def eq(self, col, val): self._rows = [r for r in self._rows if r.get(col) == val]; return self
    def in_(self, col, vals): vals = set(vals); self._rows = [r for r in self._rows if r.get(col) in vals]; return self
    def gte(self, *_a, **_k): return self
    def order(self, *_a, **_k): return self
    def limit(self, *_a, **_k): return self
    def update(self, data): self._update = data; return self
    def execute(self): return SimpleNamespace(data=self._rows)


class _FakeDB:
    def __init__(self, tables: dict):
        self._tables = tables
        self._last_update = None

    def table(self, name):
        return _FakeQuery(self._tables.get(name, []))


# ── risk score formula ─────────────────────────────────────────────────────────

def test_risk_score_formula_positive_sentiment():
    """High-view positive video should have positive risk score."""
    from app.dashboard.router import _compute_risk_score

    score = _compute_risk_score(
        sentiment_score=0.8,
        view_count=1_000_000,
        like_count=50_000,
        comment_count=5_000,
        days_old=0,
    )
    assert score > 0


def test_risk_score_formula_negative_sentiment():
    """High-view negative video should have negative risk score."""
    from app.dashboard.router import _compute_risk_score

    score = _compute_risk_score(
        sentiment_score=-0.8,
        view_count=1_000_000,
        like_count=50_000,
        comment_count=5_000,
        days_old=0,
    )
    assert score < 0


def test_risk_score_zero_views():
    """Zero view count should produce risk score of 0."""
    from app.dashboard.router import _compute_risk_score

    score = _compute_risk_score(
        sentiment_score=-1.0,
        view_count=0,
        like_count=0,
        comment_count=0,
        days_old=0,
    )
    assert score == 0.0


def test_risk_score_decays_with_age():
    """Older videos should have lower absolute risk score (recency decay)."""
    from app.dashboard.router import _compute_risk_score

    fresh = _compute_risk_score(
        sentiment_score=-0.8,
        view_count=500_000,
        like_count=10_000,
        comment_count=2_000,
        days_old=0,
    )
    old = _compute_risk_score(
        sentiment_score=-0.8,
        view_count=500_000,
        like_count=10_000,
        comment_count=2_000,
        days_old=29,
    )
    assert abs(fresh) > abs(old)


# ── reach tier helper ──────────────────────────────────────────────────────────

def test_reach_tier_viral():
    from app.dashboard.router import _brand_risk_reach_tier
    assert _brand_risk_reach_tier(1_000_001) == "Viral"


def test_reach_tier_high():
    from app.dashboard.router import _brand_risk_reach_tier
    assert _brand_risk_reach_tier(100_000) == "High"


def test_reach_tier_mid():
    from app.dashboard.router import _brand_risk_reach_tier
    assert _brand_risk_reach_tier(50_000) == "Mid"


def test_reach_tier_low():
    from app.dashboard.router import _brand_risk_reach_tier
    assert _brand_risk_reach_tier(999) == "Low"


# ── endpoint tests ─────────────────────────────────────────────────────────────

def _yt_article(i, views=100_000, likes=5_000, comments=500, score=0.5, days_old=5):
    """Build a minimal YouTube article dict."""
    from datetime import datetime, timezone, timedelta
    pub_at = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
    return {
        "id": f"art-{i}",
        "title": f"Video {i}",
        "url": f"https://youtube.com/watch?v=vid{i}",
        "portal_id": f"youtube_ch_{i}",
        "source_type": "youtube_video",
        "sentiment_score": score,
        "sentiment_label": "positive" if score > 0 else "negative",
        "published_at": pub_at,
        "collected_at": pub_at,
        "reach_metadata": {
            "view_count": views,
            "like_count": likes,
            "comment_count": comments,
        },
    }


def test_brand_risk_scores_returns_200():
    client = _make_client_as_admin()
    videos = [_yt_article(i) for i in range(3)]
    fake_db = _FakeDB({"articles": videos})

    with patch("app.dashboard.router.get_db", return_value=fake_db):
        resp = client.get("/dashboard/brand-risk-scores/brand-1")

    assert resp.status_code == 200
    data = resp.json()
    assert "videos" in data
    assert "brand_id" in data
    assert data["brand_id"] == "brand-1"


def test_brand_risk_scores_returns_top10_by_abs_risk():
    """Returns at most 10 videos sorted by abs(risk_score) desc."""
    client = _make_client_as_admin()
    # 15 videos with varying sentiment scores
    videos = [_yt_article(i, score=(-1) ** i * 0.5, views=i * 100_000) for i in range(1, 16)]
    fake_db = _FakeDB({"articles": videos})

    with patch("app.dashboard.router.get_db", return_value=fake_db):
        resp = client.get("/dashboard/brand-risk-scores/brand-1")

    assert resp.status_code == 200
    result_videos = resp.json()["videos"]
    assert len(result_videos) <= 10
    # sorted by abs(risk_score) descending
    risk_scores = [abs(v["risk_score"]) for v in result_videos]
    assert risk_scores == sorted(risk_scores, reverse=True)


def test_brand_risk_scores_empty_when_no_youtube_data():
    client = _make_client_as_admin()
    fake_db = _FakeDB({"articles": []})

    with patch("app.dashboard.router.get_db", return_value=fake_db):
        resp = client.get("/dashboard/brand-risk-scores/brand-1")

    assert resp.status_code == 200
    assert resp.json()["videos"] == []


def test_brand_risk_scores_requires_auth():
    """Without override, endpoint should reject unauthenticated requests."""
    with patch("app.pipeline.scheduler.start_scheduler"), \
         patch("asyncio.create_task"):
        from app.main import app
    # Clear any overrides
    app.dependency_overrides.clear()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/dashboard/brand-risk-scores/brand-1")
    assert resp.status_code == 403


def test_brand_risk_scores_reach_tier_in_response():
    """Each video in the response includes a reach_tier string."""
    client = _make_client_as_admin()
    videos = [
        _yt_article(1, views=2_000_000),   # Viral
        _yt_article(2, views=500_000),     # High
        _yt_article(3, views=50_000),      # Mid
        _yt_article(4, views=500),         # Low
    ]
    fake_db = _FakeDB({"articles": videos})

    with patch("app.dashboard.router.get_db", return_value=fake_db):
        resp = client.get("/dashboard/brand-risk-scores/brand-1")

    assert resp.status_code == 200
    for v in resp.json()["videos"]:
        assert v["reach_tier"] in ("Viral", "High", "Mid", "Low")


# ── review queue endpoint tests ────────────────────────────────────────────────

def test_review_queue_get_returns_200():
    client = _make_client_as_admin()
    queue_items = [
        {
            "id": "q-1", "brand_id": "brand-1", "article_id": "art-1",
            "reason": "low_confidence_crisis", "status": "pending",
            "reviewer_id": None, "reviewed_at": None,
            "created_at": "2026-06-21T00:00:00Z",
        }
    ]
    fake_db = _FakeDB({
        "human_review_queue": queue_items,
        "articles": [{"id": "art-1", "title": "Test", "url": "https://x.com"}],
    })

    with patch("app.dashboard.router.get_db", return_value=fake_db):
        resp = client.get("/dashboard/review-queue/brand-1")

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 0


def test_review_queue_requires_write_role():
    """Review queue endpoints should require at least WRITE_ROLES (not just read)."""
    from app.auth.dependencies import WRITE_ROLES, READ_ROLES
    # WRITE_ROLES is a subset of READ_ROLES — verify the spec restriction
    write_set = set(WRITE_ROLES)
    read_set = set(READ_ROLES)
    # brand_viewer and agency_analyst are in READ but not WRITE
    assert "brand_viewer" not in write_set
    assert "agency_analyst" not in write_set


def test_review_queue_patch_approve():
    """PATCH /review-queue/{item_id} with status=approved → 200."""
    client = _make_client_as_admin()

    updated = [{"id": "q-1", "status": "approved"}]

    class _PatchDB:
        def table(self, name):
            return self

        def update(self, data):
            self._data = data
            return self

        def eq(self, *_a, **_k):
            return self

        def execute(self):
            return SimpleNamespace(data=updated)

    with patch("app.dashboard.router.get_db", return_value=_PatchDB()):
        resp = client.patch(
            "/dashboard/review-queue/q-1",
            json={"status": "approved"},
        )

    assert resp.status_code == 200


def test_review_queue_patch_reject():
    """PATCH /review-queue/{item_id} with status=rejected → 200."""
    client = _make_client_as_admin()
    updated = [{"id": "q-1", "status": "rejected"}]

    class _PatchDB:
        def table(self, name): return self
        def update(self, data): return self
        def eq(self, *_a, **_k): return self
        def execute(self): return SimpleNamespace(data=updated)

    with patch("app.dashboard.router.get_db", return_value=_PatchDB()):
        resp = client.patch(
            "/dashboard/review-queue/q-1",
            json={"status": "rejected"},
        )

    assert resp.status_code == 200
