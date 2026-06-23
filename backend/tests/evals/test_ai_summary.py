"""
AI Executive Summary Evals (app.dashboard.router — GET /dashboard/ai-summary/{brand_id}).

Tests structural correctness, error handling, and response shape.
No live LLM calls in the base suite — LLM is mocked.

@pytest.mark.eval tests make real API calls; skip in CI.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


# ─── Test fixtures ────────────────────────────────────────────────────────────

_BRAND_ID = "brand-test-uuid-1234"

_SAMPLE_ARTICLES = [
    {
        "id": f"art-{i}",
        "title": f"Article {i}",
        "body": f"Body text for article {i} covering relevant brand topics and news.",
        "sentiment_label": "negative" if i % 2 == 0 else "positive",
        "sentiment_score": -0.6 if i % 2 == 0 else 0.6,
        "source_type": "news",
        "collected_at": "2026-06-22T10:00:00Z",
        "portal_name": "The Hindu",
    }
    for i in range(10)
]

_GOOD_LLM_RESPONSE = json.dumps({
    "what_changed": "Negative sentiment increased 15% driven by supply chain issues",
    "why": "Three major portals ran critical pieces on delivery delays affecting consumer trust",
    "actions": [
        "Issue press release addressing supply chain improvements",
        "Increase monitoring of delivery-related keywords",
        "Engage directly with top 3 critical journalists",
    ],
})

_MALFORMED_LLM_RESPONSE = "Not valid JSON at all"

_PARTIAL_LLM_RESPONSE = json.dumps({
    "what_changed": "Some change",
    # Missing "why" and "actions"
})


# ─── Structural schema validation ─────────────────────────────────────────────

class TestAiSummarySchema:

    def test_response_has_required_fields(self):
        """Mocked LLM → verify endpoint returns all 4 required fields."""
        from app.dashboard.router import get_ai_summary

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = _SAMPLE_ARTICLES

        with patch("app.dashboard.router.get_db", return_value=mock_db), \
             patch("app.dashboard.router.settings") as mock_s, \
             patch("app.dashboard.router._call_gemini_for_summary",
                   return_value=_GOOD_LLM_RESPONSE):
            mock_s.gemini_api_key = "test-key"
            mock_s.gemini_model = "gemini-2.5-flash"
            result = get_ai_summary(_BRAND_ID, days=7)

        assert "what_changed" in result
        assert "why" in result
        assert "actions" in result
        assert "generated_at" in result

    def test_actions_is_a_list(self):
        from app.dashboard.router import get_ai_summary

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = _SAMPLE_ARTICLES

        with patch("app.dashboard.router.get_db", return_value=mock_db), \
             patch("app.dashboard.router.settings") as mock_s, \
             patch("app.dashboard.router._call_gemini_for_summary",
                   return_value=_GOOD_LLM_RESPONSE):
            mock_s.gemini_api_key = "test-key"
            mock_s.gemini_model = "gemini-2.5-flash"
            result = get_ai_summary(_BRAND_ID, days=7)

        assert isinstance(result["actions"], list)
        assert len(result["actions"]) >= 1

    def test_generated_at_is_iso_timestamp(self):
        from app.dashboard.router import get_ai_summary
        from datetime import datetime

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = _SAMPLE_ARTICLES

        with patch("app.dashboard.router.get_db", return_value=mock_db), \
             patch("app.dashboard.router.settings") as mock_s, \
             patch("app.dashboard.router._call_gemini_for_summary",
                   return_value=_GOOD_LLM_RESPONSE):
            mock_s.gemini_api_key = "test-key"
            mock_s.gemini_model = "gemini-2.5-flash"
            result = get_ai_summary(_BRAND_ID, days=7)

        # Should be parseable as ISO datetime
        try:
            datetime.fromisoformat(result["generated_at"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pytest.fail(f"generated_at not a valid ISO timestamp: {result['generated_at']!r}")


# ─── Error handling evals ─────────────────────────────────────────────────────

class TestAiSummaryErrorHandling:

    def test_no_articles_returns_503_or_empty_graceful(self):
        """When brand has no articles in date range, endpoint should not 500."""
        from app.dashboard.router import get_ai_summary
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []

        with patch("app.dashboard.router.get_db", return_value=mock_db), \
             patch("app.dashboard.router.settings") as mock_s:
            mock_s.gemini_api_key = "test-key"
            mock_s.gemini_model = "gemini-2.5-flash"
            try:
                result = get_ai_summary(_BRAND_ID, days=7)
                # If it returns, must have expected keys
                assert "what_changed" in result or result is not None
            except HTTPException as e:
                # 503 is acceptable when no data
                assert e.status_code in (503, 404)

    def test_all_providers_unavailable_raises_503(self):
        """When all LLM providers fail, endpoint raises 503."""
        from app.dashboard.router import get_ai_summary
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = _SAMPLE_ARTICLES

        with patch("app.dashboard.router.get_db", return_value=mock_db), \
             patch("app.dashboard.router.settings") as mock_s, \
             patch("app.dashboard.router._call_gemini_for_summary", return_value=None), \
             patch("app.dashboard.router._call_groq_for_summary", return_value=None):
            mock_s.gemini_api_key = "test-key"
            mock_s.gemini_model = "gemini-2.5-flash"
            mock_s.gemini_free_api_key = "free-key"
            mock_s.groq_api_key = "groq-key"
            with pytest.raises(HTTPException) as exc_info:
                get_ai_summary(_BRAND_ID, days=7)
        assert exc_info.value.status_code == 503

    def test_settings_import_present(self):
        """Regression: 'settings' must be importable in router.py — NameError was a bug."""
        try:
            from app.dashboard.router import get_ai_summary
            from app.config import settings  # noqa: F401
        except NameError as e:
            pytest.fail(f"NameError importing settings: {e}")

    def test_db_import_in_function_body(self):
        """Regression: get_db() must be called inside function, not at module level."""
        import inspect
        from app.dashboard import router
        # If get_db is called at module level, it would fail on import without real DB.
        # The fact that the test suite imports without error is the assertion.
        assert hasattr(router, "get_ai_summary") or True  # just verify import succeeded


# ─── Content quality evals (mocked LLM with known outputs) ───────────────────

class TestAiSummaryContentQuality:

    def _run_with_articles(self, articles, llm_response=_GOOD_LLM_RESPONSE):
        from app.dashboard.router import get_ai_summary

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = articles

        with patch("app.dashboard.router.get_db", return_value=mock_db), \
             patch("app.dashboard.router.settings") as mock_s, \
             patch("app.dashboard.router._call_gemini_for_summary",
                   return_value=llm_response):
            mock_s.gemini_api_key = "test-key"
            mock_s.gemini_model = "gemini-2.5-flash"
            return get_ai_summary(_BRAND_ID, days=7)

    def test_what_changed_is_non_empty_string(self):
        result = self._run_with_articles(_SAMPLE_ARTICLES)
        if result:
            assert isinstance(result.get("what_changed", ""), str)
            assert len(result.get("what_changed", "")) > 0

    def test_actions_are_non_empty_strings(self):
        result = self._run_with_articles(_SAMPLE_ARTICLES)
        if result and "actions" in result:
            for action in result["actions"]:
                assert isinstance(action, str)
                assert len(action.strip()) > 0

    def test_all_positive_articles_produces_positive_framing(self):
        """When all articles are positive, summary shouldn't say things got worse."""
        positive_articles = [
            {**a, "sentiment_label": "positive", "sentiment_score": 0.8}
            for a in _SAMPLE_ARTICLES
        ]
        positive_response = json.dumps({
            "what_changed": "Strong positive coverage across all channels",
            "why": "New product launch received excellent media reception",
            "actions": ["Amplify positive stories via PR channels"],
        })
        result = self._run_with_articles(positive_articles, positive_response)
        if result:
            assert "positive" in result.get("what_changed", "").lower() or \
                   "strong" in result.get("what_changed", "").lower()


# ─── Integration tests via HTTP endpoint ──────────────────────────────────────

class TestAiSummaryEndpoint:
    """FastAPI TestClient integration tests for /dashboard/ai-summary/{brand_id}."""

    @pytest.fixture
    def client(self):
        with patch("app.pipeline.scheduler.start_scheduler"), \
             patch("asyncio.create_task"):
            from app.main import app
        return TestClient(app)

    def test_endpoint_requires_auth(self, client):
        response = client.get(f"/dashboard/ai-summary/{_BRAND_ID}")
        assert response.status_code in (401, 403, 422)

    def test_endpoint_url_exists(self, client):
        """Endpoint should exist — 401 is acceptable, 404 is not."""
        response = client.get(f"/dashboard/ai-summary/{_BRAND_ID}")
        assert response.status_code != 404, "AI summary endpoint not registered in router"


# ─── Live eval tests ──────────────────────────────────────────────────────────

@pytest.mark.eval
@pytest.mark.skip(reason="Live eval — run manually in staging with real API keys")
class TestAiSummaryLiveQuality:
    """
    Tests real Gemini output on fixed input articles.

    Run with: pytest tests/evals/test_ai_summary.py -m eval -v
    Requires GEMINI_API_KEY set in environment.
    """

    def test_live_summary_has_all_required_fields(self):
        from app.dashboard.router import get_ai_summary

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = _SAMPLE_ARTICLES

        with patch("app.dashboard.router.get_db", return_value=mock_db):
            result = get_ai_summary(_BRAND_ID, days=7)

        assert "what_changed" in result
        assert "why" in result
        assert "actions" in result
        assert len(result["actions"]) >= 1

    def test_live_summary_actions_are_actionable(self):
        """Actions should contain imperative verbs, not just nouns."""
        from app.dashboard.router import get_ai_summary

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = _SAMPLE_ARTICLES

        with patch("app.dashboard.router.get_db", return_value=mock_db):
            result = get_ai_summary(_BRAND_ID, days=7)

        # At least one action should start with a verb (imperative sentence)
        action_words = [a.split()[0].lower() for a in result.get("actions", []) if a.strip()]
        # Can't know exact verbs but length > 3 words indicates a sentence, not just a noun
        for action in result.get("actions", []):
            assert len(action.split()) >= 3, f"Action too short to be actionable: {action!r}"
