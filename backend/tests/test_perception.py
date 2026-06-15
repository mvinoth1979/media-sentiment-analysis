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
