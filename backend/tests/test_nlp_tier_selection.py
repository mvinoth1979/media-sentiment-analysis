"""
Tests for NLP tier routing logic (app.nlp.api_router.select_tier).

select_tier is a pure function mapping (source_type, language, word_count, has_star)
→ NLPTier enum. No external calls — fast deterministic tests.
"""

import pytest
from unittest.mock import patch
from app.nlp.api_router import NLPTier, select_tier


# ─── Tier 0: NONE — no LLM cost ───────────────────────────────────────────────

class TestTierNone:

    def test_google_review_with_star_is_tier_0(self):
        tier = select_tier("google_review", "en", 50, has_star=True)
        assert tier == NLPTier.NONE

    def test_google_review_without_star_escapes_tier_0(self):
        # No star → falls through to language/source checks
        tier = select_tier("google_review", "en", 50, has_star=False)
        assert tier != NLPTier.NONE

    def test_short_article_8_words_is_tier_0(self):
        tier = select_tier("news", "en", 8, has_star=False)
        assert tier == NLPTier.NONE

    def test_9_words_escapes_tier_0(self):
        tier = select_tier("news", "en", 9, has_star=False)
        assert tier != NLPTier.NONE

    def test_zero_words_is_tier_0(self):
        tier = select_tier("news", "en", 0, has_star=False)
        assert tier == NLPTier.NONE

    def test_star_rating_zero_treated_as_falsy(self):
        # star_rating=0 → has_star=False (Python falsy); google_review won't get NONE
        tier = select_tier("google_review", "en", 50, has_star=False)
        assert tier != NLPTier.NONE


# ─── Tier 1: GROQ — social EN comments ────────────────────────────────────────

class TestTierGroq:

    def test_youtube_comment_en_is_groq(self):
        tier = select_tier("youtube_comment", "en", 20, has_star=False)
        assert tier == NLPTier.GROQ

    def test_reddit_comment_en_is_groq(self):
        tier = select_tier("reddit_comment", "en", 30, has_star=False)
        assert tier == NLPTier.GROQ

    def test_youtube_comment_indic_is_still_groq(self):
        # Comments always go to Groq regardless of language (Tier 1 check runs first)
        tier = select_tier("youtube_comment", "ta", 25, has_star=False)
        assert tier == NLPTier.GROQ

    def test_youtube_video_en_is_groq(self):
        tier = select_tier("youtube_video", "en", 100, has_star=False)
        assert tier == NLPTier.GROQ

    def test_reddit_post_en_is_groq(self):
        tier = select_tier("reddit_post", "en", 80, has_star=False)
        assert tier == NLPTier.GROQ

    def test_reddit_post_indic_escapes_groq_to_paid(self):
        # Indic-language social post → Tier 3 (paid), not Groq
        tier = select_tier("reddit_post", "ta", 80, has_star=False)
        assert tier == NLPTier.GEMINI_PAID


# ─── Tier 2: GEMINI_FREE — EN news ────────────────────────────────────────────

class TestTierGeminiFree:

    def test_news_en_with_free_key_is_gemini_free(self):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key-123"
            tier = select_tier("news", "en", 200, has_star=False)
        assert tier == NLPTier.GEMINI_FREE

    def test_rss_blog_en_with_free_key_is_gemini_free(self):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key"
            tier = select_tier("blog", "en", 150, has_star=False)
        assert tier == NLPTier.GEMINI_FREE

    def test_play_store_review_en_with_free_key_is_gemini_free(self):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key"
            tier = select_tier("play_store_review", "en", 50, has_star=False)
        assert tier == NLPTier.GEMINI_FREE

    def test_no_free_key_falls_to_gemini_paid(self):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = ""
            tier = select_tier("news", "en", 200, has_star=False)
        assert tier == NLPTier.GEMINI_PAID


# ─── Tier 3: GEMINI_PAID — Indic languages ────────────────────────────────────

class TestTierGeminiPaid:

    @pytest.mark.parametrize("lang", ["ta", "hi", "gu", "bn", "kn"])
    def test_indic_news_is_always_paid(self, lang):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key"
            tier = select_tier("news", lang, 200, has_star=False)
        assert tier == NLPTier.GEMINI_PAID

    def test_indic_youtube_video_is_paid(self):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key"
            tier = select_tier("youtube_video", "hi", 100, has_star=False)
        assert tier == NLPTier.GEMINI_PAID

    def test_indic_rss_is_paid(self):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key"
            tier = select_tier("rss", "ta", 80, has_star=False)
        assert tier == NLPTier.GEMINI_PAID


# ─── Edge cases ───────────────────────────────────────────────────────────────

class TestTierEdgeCases:

    def test_unknown_source_type_en_gets_gemini(self):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key"
            tier = select_tier("unknown_source", "en", 100, has_star=False)
        assert tier in (NLPTier.GEMINI_FREE, NLPTier.GEMINI_PAID)

    def test_return_type_is_nlptier_enum(self):
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key"
            tier = select_tier("news", "en", 100, has_star=False)
        assert isinstance(tier, NLPTier)

    def test_star_review_beats_word_count_check(self):
        # 5-word google review with star → NONE (not too-short check)
        tier = select_tier("google_review", "en", 5, has_star=True)
        assert tier == NLPTier.NONE

    def test_very_long_article_en_is_not_groq(self):
        # News article with 2000 words → not social, should go to Gemini
        with patch("app.nlp.api_router.settings") as mock_s:
            mock_s.gemini_free_api_key = "free-key"
            tier = select_tier("news", "en", 2000, has_star=False)
        assert tier in (NLPTier.GEMINI_FREE, NLPTier.GEMINI_PAID)
        assert tier != NLPTier.GROQ
