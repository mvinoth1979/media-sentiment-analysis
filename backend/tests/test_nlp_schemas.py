from app.nlp.schemas import NLPResult

def test_nlp_result_defaults():
    r = NLPResult(sentiment_score=0.5, sentiment_label="positive")
    assert r.entities == []
    assert r.topics == []
    assert r.keywords == []
    assert r.model_used == ""
    assert r.confidence == 0.0

def test_nlp_result_to_dict():
    r = NLPResult(
        sentiment_score=-0.8,
        sentiment_label="negative",
        entities=["Amul"],
        topics=["pricing"],
        keywords=["expensive"],
        model_used="gemini-2.0-flash",
        confidence=0.91,
    )
    d = r.to_dict()
    assert d["sentiment_score"] == -0.8
    assert d["sentiment_label"] == "negative"
    assert d["entities"] == ["Amul"]
    assert d["model_used"] == "gemini-2.0-flash"

def test_nlp_result_mutable_defaults_are_independent():
    r1 = NLPResult(sentiment_score=0.0, sentiment_label="neutral")
    r2 = NLPResult(sentiment_score=0.0, sentiment_label="neutral")
    r1.entities.append("Test")
    assert r2.entities == []  # Verify field(default_factory=list) creates separate lists


# ── Item 9: creator_type tests ─────────────────────────────────────────────────

def test_nlp_result_creator_type_default():
    r = NLPResult(sentiment_score=0.0, sentiment_label="neutral")
    assert r.creator_type == "unknown"

def test_nlp_result_creator_type_set():
    r = NLPResult(
        sentiment_score=0.5,
        sentiment_label="positive",
        creator_type="reviewer",
    )
    assert r.creator_type == "reviewer"

def test_nlp_result_creator_type_in_to_dict():
    r = NLPResult(
        sentiment_score=0.5,
        sentiment_label="positive",
        creator_type="influencer",
    )
    d = r.to_dict()
    assert "creator_type" in d
    assert d["creator_type"] == "influencer"

def test_nlp_result_creator_type_default_in_to_dict():
    r = NLPResult(sentiment_score=0.0, sentiment_label="neutral")
    d = r.to_dict()
    assert d["creator_type"] == "unknown"

def test_nlp_result_all_valid_creator_types():
    valid_types = [
        "journalist", "reviewer", "influencer", "customer",
        "industry_expert", "activist", "competitor_affiliate", "unknown",
    ]
    for ct in valid_types:
        r = NLPResult(sentiment_score=0.0, sentiment_label="neutral", creator_type=ct)
        assert r.creator_type == ct
        assert r.to_dict()["creator_type"] == ct
