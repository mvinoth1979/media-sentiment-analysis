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
