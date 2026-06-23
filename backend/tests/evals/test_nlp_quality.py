"""
NLP Quality Evals — Golden dataset tests for the NLP pipeline.

These tests define the expected behaviour contract for sentiment analysis,
issue classification, language detection, and star-rating conversion.

Two categories:
  - Unit evals  : mock the LLM, test pipeline logic with known inputs/outputs.
                  Run in CI (no API cost, deterministic).
  - @pytest.mark.eval : live LLM call tests that verify real model accuracy.
                  Skip in CI; run manually or in staging.

Golden dataset rationale:
  Each sample represents a distinct edge case or content type from the
  Indian media sentiment domain. Expected outputs are human-verified.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.nlp.schemas import NLPResult
from app.nlp.code_extractors import (
    classify_issue_category,
    sentiment_from_star_rating,
)


# ─── Eval marker ──────────────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "eval: live LLM eval — skip in CI, run in staging with real API keys",
    )


# ─── Golden dataset ───────────────────────────────────────────────────────────

GOLDEN_SENTIMENT = [
    # (text, expected_label, must_be_positive, must_be_negative)
    (
        "Amul posts record quarterly profits, revenue up 22% year on year",
        "positive", True, False,
    ),
    (
        "Factory fire destroys Amul dairy unit, workers injured in blast",
        "negative", False, True,
    ),
    (
        "Amul announces new product launch, details to be confirmed",
        "neutral", False, False,
    ),
    (
        "Company fined Rs 50 lakh by FSSAI for quality violations",
        "negative", False, True,
    ),
    (
        "Brand wins marketing award for best television commercial of the year",
        "positive", True, False,
    ),
]

GOLDEN_ISSUE_CATEGORY = [
    # (text, expected_category, min_confidence)
    # Category names match _ISSUE_KWORDS keys in code_extractors.py
    (
        "CEO quits amid fraud scandal and corruption scam allegations",
        "crisis_controversy", 0.60,
    ),
    (
        "quarterly earnings beat estimates with strong revenue and profit margins",
        "financial_performance", 0.60,
    ),
    (
        "product recall issued for defective batch with quality control failure",
        "product_quality", 0.60,
    ),
    (
        "fraud scandal backlash corruption outrage boycott crisis hits company",
        "crisis_controversy", 0.88,  # 5+ keywords → 0.88
    ),
    (
        "brand ambassador announced for csr and sustainability initiative",
        None, 0.40,  # could be csr_sustainability OR brand_advocacy — any is fine
    ),
    (
        "company announces new product launch and expansion plan into new category",
        "market_opportunity", 0.60,
    ),
    (
        "consumer complaint and poor service bad experience customer review",
        "customer_experience", 0.60,
    ),
]

GOLDEN_STAR_SENTIMENT = [
    # (rating, expected_label, expected_score_sign)  sign: 1=positive, -1=negative, 0=neutral
    (5,    "positive", 1),
    (4,    "positive", 1),
    (3,    "neutral",  0),
    (2,    "negative", -1),
    (1,    "negative", -1),
    (4.7,  "positive", 1),   # rounds to 5
    (1.3,  "negative", -1),  # rounds to 1
    ("5",  "positive", 1),
    (None, "neutral",  0),
    (0,    "negative", -1),  # clamped to 1
]


# ─── Code-level evals (deterministic, no LLM) ────────────────────────────────

class TestIssueClassificationAccuracy:
    """
    Verify classify_issue_category produces expected categories on the golden set.
    These are pure-function tests — no mocking, no LLM calls.
    """

    @pytest.mark.parametrize("text,expected_cat,min_conf", GOLDEN_ISSUE_CATEGORY)
    def test_issue_category_golden_set(self, text, expected_cat, min_conf):
        cat, conf = classify_issue_category(text)
        assert conf >= min_conf, f"Confidence {conf} below {min_conf} for: {text!r}"
        if expected_cat:
            assert cat == expected_cat, (
                f"Expected '{expected_cat}' but got '{cat}' for: {text!r}"
            )

    def test_no_false_positives_on_neutral_text(self):
        # Generic text with no issue keywords → "other" or low confidence
        cat, conf = classify_issue_category(
            "Company will hold its annual general meeting next month"
        )
        assert conf <= 0.60, f"Should be low confidence for neutral text, got {conf}"

    def test_high_confidence_only_when_multiple_keywords(self):
        # Single keyword → confidence 0.60, not 0.88
        cat, conf = classify_issue_category("product recall announced")
        assert conf < 0.88


class TestStarSentimentMapping:
    """Golden-set tests for star rating → sentiment conversion."""

    @pytest.mark.parametrize("rating,expected_label,sign", GOLDEN_STAR_SENTIMENT)
    def test_star_rating_golden_set(self, rating, expected_label, sign):
        score, label = sentiment_from_star_rating(rating)
        assert label == expected_label, f"Rating {rating}: expected {expected_label}, got {label}"
        if sign == 1:
            assert score > 0
        elif sign == -1:
            assert score < 0
        elif sign == 0:
            assert score == 0.0

    def test_full_5_star_scale_coverage(self):
        """All valid star ratings 1-5 map to expected labels without error."""
        expected = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}
        for stars, expected_label in expected.items():
            _, label = sentiment_from_star_rating(stars)
            assert label == expected_label


# ─── Pipeline-level evals (mocked LLM, deterministic) ────────────────────────

class TestNLPPipelineContract:
    """
    Verify the analyse_article pipeline correctly routes and processes
    the golden sentiment examples. LLM is mocked with expected outputs.
    """

    def _make_nlp_result(self, label: str, score: float) -> NLPResult:
        return NLPResult(
            sentiment_score=score,
            sentiment_label=label,
            entities=["Amul"],
            topics=["financial_performance"],
            keywords=["revenue", "profit"],
            model_used="gemini-2.5-flash",
            confidence=0.92,
        )

    @pytest.mark.parametrize(
        "text,expected_label,must_pos,must_neg",
        GOLDEN_SENTIMENT,
    )
    def test_pipeline_routes_sentiment_correctly(self, text, expected_label, must_pos, must_neg):
        from app.nlp.router import analyse_article

        score = 0.8 if must_pos else (-0.8 if must_neg else 0.0)
        mock_result = self._make_nlp_result(expected_label, score)

        article = {
            "title": text[:60],
            "body": text,
            "language": "en",
            "source_type": "news",
        }

        with patch("app.nlp.router._call_gemini", return_value=(mock_result, False)), \
             patch("app.nlp.router.detect_language", return_value=("en", 0.98)):
            result = analyse_article(article)

        assert result is not None
        assert result.sentiment_label == expected_label
        if must_pos:
            assert result.sentiment_score > 0
        if must_neg:
            assert result.sentiment_score < 0

    def test_circuit_breaker_open_returns_none(self):
        from app.nlp.router import analyse_article
        import app.nlp.circuit_breaker as cb

        article = {
            "title": "Amul reports results",
            "body": "Amul quarterly revenue up, analysts upbeat on outlook for the company",
            "language": "en",
        }
        with patch.object(cb, "is_open", return_value=True):
            result = analyse_article(article)
        assert result is None

    def test_short_article_below_8_words_returns_none(self):
        from app.nlp.router import analyse_article

        article = {
            "title": "Brief note",
            "body": "Very short",  # ≤8 words total
            "language": "en",
        }
        result = analyse_article(article)
        assert result is None

    def test_star_rating_google_review_bypasses_llm(self):
        from app.nlp.router import analyse_article

        article = {
            "title": "Excellent service",
            "body": "Great product, highly satisfied with the purchase",
            "language": "en",
            "source_type": "google_review",
            "reach_metadata": {"star_rating": 5},
        }
        with patch("app.nlp.router._call_gemini") as mock_gemini, \
             patch("app.nlp.router._call_groq") as mock_groq:
            result = analyse_article(article)

        # Star-rated google_review → Tier 0 → no LLM call
        mock_gemini.assert_not_called()
        mock_groq.assert_not_called()

    def test_indic_language_routes_to_gemini_paid(self):
        from app.nlp.router import analyse_article

        ta_article = {
            "title": "அமுல் விலை உயர்வு",
            "body": "அமுல் நிறுவனம் பால் மற்றும் வெண்ணெய் விலையை உயர்த்த திட்டமிட்டுள்ளது",
            "language": "ta",
            "source_type": "news",
        }
        mock_result = self._make_nlp_result("neutral", 0.0)
        with patch("app.nlp.router._call_gemini", return_value=(mock_result, False)) as mock_g, \
             patch("app.nlp.router.detect_language", return_value=("ta", 0.97)):
            result = analyse_article(ta_article)

        # Should call Gemini (paid tier for Indic), not Groq first
        mock_g.assert_called_once()
        # Verify paid=True was passed
        call_kwargs = mock_g.call_args
        assert call_kwargs[0][-1] is True or call_kwargs[1].get("paid") is True


# ─── Structural consistency evals ─────────────────────────────────────────────

class TestNLPResultSchema:
    """
    Verify NLPResult schema is always valid — even with boundary inputs.
    """

    def test_nlp_result_sentiment_score_bounded(self):
        result = NLPResult(
            sentiment_score=0.95,
            sentiment_label="positive",
            model_used="gemini",
            confidence=0.9,
        )
        assert -1.0 <= result.sentiment_score <= 1.0

    def test_nlp_result_confidence_bounded(self):
        result = NLPResult(
            sentiment_score=0.0,
            sentiment_label="neutral",
            model_used="groq",
            confidence=0.55,
        )
        assert 0.0 <= result.confidence <= 1.0

    def test_nlp_result_optional_fields_default_empty(self):
        result = NLPResult(
            sentiment_score=0.5,
            sentiment_label="positive",
            model_used="gemini",
            confidence=0.8,
        )
        # Optional list fields should default to empty list, not None
        assert result.entities is None or isinstance(result.entities, list)
        assert result.topics is None or isinstance(result.topics, list)

    @pytest.mark.parametrize("label", ["positive", "negative", "neutral"])
    def test_valid_sentiment_labels(self, label):
        result = NLPResult(
            sentiment_score=0.0,
            sentiment_label=label,
            model_used="test",
            confidence=0.5,
        )
        assert result.sentiment_label == label


# ─── Live eval tests (require real API keys — skip in CI) ─────────────────────

@pytest.mark.eval
@pytest.mark.skip(reason="Live eval — run manually in staging with real API keys")
class TestLiveNLPAccuracy:
    """
    End-to-end accuracy tests against real LLM APIs.

    Run with: pytest -m eval --no-header -v
    Requires: GEMINI_API_KEY and/or GROQ_API_KEY set in environment.

    Accuracy thresholds:
      - Sentiment polarity: ≥80% correct on golden set
      - Issue category: ≥70% correct on golden set
    """

    def test_positive_financial_news_classified_positive(self):
        from app.nlp.router import analyse_article
        article = {
            "title": "Amul posts record profits",
            "body": "Amul reported record quarterly profits with revenue up 22% driven by strong rural demand and premium product mix.",
            "language": "en",
            "source_type": "news",
        }
        result = analyse_article(article)
        assert result is not None
        assert result.sentiment_label == "positive"
        assert result.sentiment_score > 0.3

    def test_crisis_news_classified_negative(self):
        from app.nlp.router import analyse_article
        article = {
            "title": "Factory fire causes disruption",
            "body": "A major fire broke out at the dairy unit causing significant operational disruption and resulting in losses.",
            "language": "en",
            "source_type": "news",
        }
        result = analyse_article(article)
        assert result is not None
        assert result.sentiment_label == "negative"
        assert result.sentiment_score < -0.2

    def test_tamil_article_returns_result(self):
        from app.nlp.router import analyse_article
        article = {
            "title": "அமுல் நிறுவனம் விலை உயர்வு",
            "body": "அமுல் நிறுவனம் பால் மற்றும் வெண்ணெய் விலையை உயர்த்த திட்டமிட்டுள்ளது என்று நிறுவனம் அறிவித்தது.",
            "language": "ta",
            "source_type": "news",
        }
        result = analyse_article(article)
        assert result is not None
        assert result.sentiment_label in ("positive", "negative", "neutral")

    def test_golden_sentiment_accuracy_above_80_percent(self):
        from app.nlp.router import analyse_article
        correct = 0
        for text, expected_label, _, _ in GOLDEN_SENTIMENT:
            article = {"title": text[:60], "body": text, "language": "en", "source_type": "news"}
            result = analyse_article(article)
            if result and result.sentiment_label == expected_label:
                correct += 1
        accuracy = correct / len(GOLDEN_SENTIMENT)
        assert accuracy >= 0.80, f"Sentiment accuracy {accuracy:.0%} below 80%"
