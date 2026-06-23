import pytest
from app.pipeline.perception import calculate_perception_score

def test_all_positive_gives_high_score():
    articles = [
        {"sentiment_score": 0.9, "source_credibility": 0.9, "reach_score": 5000},
        {"sentiment_score": 0.8, "source_credibility": 0.85, "reach_score": 3000},
    ]
    score = calculate_perception_score(articles)
    assert score > 70

def test_all_negative_gives_low_score():
    articles = [
        {"sentiment_score": -0.9, "source_credibility": 0.9, "reach_score": 5000},
        {"sentiment_score": -0.8, "source_credibility": 0.85, "reach_score": 3000},
    ]
    score = calculate_perception_score(articles)
    assert score < 30

def test_empty_articles_returns_fifty():
    assert calculate_perception_score([]) == 50.0

def test_score_in_valid_range():
    articles = [
        {"sentiment_score": 0.5, "source_credibility": 0.7, "reach_score": 1000},
        {"sentiment_score": -0.3, "source_credibility": 0.5, "reach_score": 500},
    ]
    score = calculate_perception_score(articles)
    assert 0.0 <= score <= 100.0

def test_high_credibility_source_weighted_more():
    low_credibility = [{"sentiment_score": -0.9, "source_credibility": 0.1, "reach_score": 100}]
    high_credibility = [{"sentiment_score": 0.9, "source_credibility": 0.95, "reach_score": 10000}]
    score = calculate_perception_score(low_credibility + high_credibility)
    assert score > 50


# ─── Edge cases ───────────────────────────────────────────────────────────────

def test_none_sentiment_score_defaults_to_zero():
    """Article with sentiment_score=None treated as neutral (0.0)."""
    articles = [
        {"sentiment_score": None, "source_credibility": 0.8, "reach_score": 1000},
    ]
    score = calculate_perception_score(articles)
    # None score → 0.0 → neutral → score near 50
    assert 40.0 <= score <= 60.0


def test_zero_total_weight_returns_baseline():
    """When all weights compute to zero, returns 50.0 (no division by zero)."""
    # source_credibility=0 → base weight=0; reach_score=0 → log(1)=0; very old → low recency
    articles = [
        {
            "sentiment_score": 0.9,
            "source_credibility": 0.0,
            "reach_score": 0,
            "collected_at": "2020-01-01T00:00:00Z",  # very old → low recency weight
        }
    ]
    score = calculate_perception_score(articles)
    # Should not raise ZeroDivisionError; result should be valid
    assert 0.0 <= score <= 100.0


def test_score_always_bounded_between_0_and_100():
    """Extreme inputs never produce out-of-range scores."""
    extremes = [
        [{"sentiment_score": -1.0, "source_credibility": 1.0, "reach_score": 1_000_000}],
        [{"sentiment_score": 1.0, "source_credibility": 1.0, "reach_score": 1_000_000}],
        [{"sentiment_score": 0.0, "source_credibility": 0.0, "reach_score": 0}],
    ]
    for articles in extremes:
        score = calculate_perception_score(articles)
        assert 0.0 <= score <= 100.0, f"Out of range: {score} for {articles}"


def test_many_articles_does_not_crash():
    """Large batch (1000 articles) processes without error."""
    articles = [
        {"sentiment_score": (-1) ** i * 0.5, "source_credibility": 0.7, "reach_score": 500}
        for i in range(1000)
    ]
    score = calculate_perception_score(articles)
    assert 0.0 <= score <= 100.0


def test_missing_credibility_and_reach_default_gracefully():
    """Articles missing optional fields should not crash the scorer."""
    articles = [{"sentiment_score": 0.6}]  # no credibility, no reach_score
    score = calculate_perception_score(articles)
    assert 0.0 <= score <= 100.0
