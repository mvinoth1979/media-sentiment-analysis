import json
from unittest.mock import patch, MagicMock
from app.nlp.groq_handler import analyse_with_groq, _parse_creator_type
from app.nlp.schemas import NLPResult

MOCK_RESPONSE = json.dumps({
    "sentiment_score": -0.6,
    "sentiment_label": "negative",
    "entities": ["Amul"],
    "topics": ["pricing"],
    "keywords": ["price", "hike", "expensive"],
    "confidence": 0.82
})

def _make_mock_client(content: str) -> MagicMock:
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices = [mock_choice]
    return mock_client

def test_groq_returns_nlp_result():
    mock_client = _make_mock_client(MOCK_RESPONSE)

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result, rate_limited = analyse_with_groq("Amul hikes prices again", "en")

    assert isinstance(result, NLPResult)
    assert result.sentiment_label == "negative"
    assert result.model_used == "groq-llama-3.1-8b-instant"
    assert rate_limited is False

def test_groq_returns_none_on_failure():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result, rate_limited = analyse_with_groq("Some text", "ta")

    assert result is None
    assert rate_limited is False


# ── Item 9: creator_type tests ─────────────────────────────────────────────────

def test_parse_creator_type_valid():
    assert _parse_creator_type("journalist") == "journalist"
    assert _parse_creator_type("reviewer") == "reviewer"
    assert _parse_creator_type("influencer") == "influencer"
    assert _parse_creator_type("customer") == "customer"
    assert _parse_creator_type("industry_expert") == "industry_expert"
    assert _parse_creator_type("activist") == "activist"
    assert _parse_creator_type("competitor_affiliate") == "competitor_affiliate"
    assert _parse_creator_type("unknown") == "unknown"

def test_parse_creator_type_normalizes_case_and_spaces():
    assert _parse_creator_type("  Reviewer  ") == "reviewer"
    assert _parse_creator_type("Industry Expert") == "industry_expert"
    assert _parse_creator_type("INFLUENCER") == "influencer"

def test_parse_creator_type_invalid_falls_back_to_unknown():
    assert _parse_creator_type("random_type") == "unknown"
    assert _parse_creator_type("") == "unknown"
    assert _parse_creator_type("celebrity") == "unknown"

def test_groq_creator_type_set_for_youtube_video():
    payload = json.dumps({
        "sentiment_score": 0.6,
        "sentiment_label": "positive",
        "entities": [],
        "topics": [],
        "keywords": [],
        "states_mentioned": [],
        "issue_category": "other",
        "creator_type": "influencer",
        "confidence": 0.88,
    })
    mock_client = _make_mock_client(payload)

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_groq("Check out this product!", "en", source_type="youtube_video")

    assert result is not None
    assert result.creator_type == "influencer"
    assert result.source_type == "youtube_video"

def test_groq_creator_type_unknown_for_non_youtube():
    payload = json.dumps({
        "sentiment_score": 0.1,
        "sentiment_label": "neutral",
        "entities": [],
        "topics": [],
        "keywords": [],
        "creator_type": "journalist",  # LLM may return this but source is reddit
        "confidence": 0.7,
    })
    mock_client = _make_mock_client(payload)

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_groq("Reddit post text", "en", source_type="reddit_post")

    assert result is not None
    assert result.creator_type == "unknown"

def test_groq_creator_type_defaults_unknown_when_missing_in_response():
    payload = json.dumps({
        "sentiment_score": 0.4,
        "sentiment_label": "neutral",
        "entities": [],
        "topics": [],
        "keywords": [],
        "confidence": 0.7,
        # creator_type absent
    })
    mock_client = _make_mock_client(payload)

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_groq("YT video text", "en", source_type="youtube_video")

    assert result is not None
    assert result.creator_type == "unknown"

def test_groq_creator_type_invalid_value_falls_back_to_unknown():
    payload = json.dumps({
        "sentiment_score": 0.5,
        "sentiment_label": "positive",
        "entities": [],
        "topics": [],
        "keywords": [],
        "creator_type": "vlogger",  # not a valid type
        "confidence": 0.8,
    })
    mock_client = _make_mock_client(payload)

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_groq("YT video text", "en", source_type="youtube_video")

    assert result is not None
    assert result.creator_type == "unknown"

def test_groq_creator_type_in_to_dict():
    payload = json.dumps({
        "sentiment_score": 0.7,
        "sentiment_label": "positive",
        "entities": [],
        "topics": [],
        "keywords": [],
        "creator_type": "activist",
        "confidence": 0.9,
    })
    mock_client = _make_mock_client(payload)

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_groq("YT video", "en", source_type="youtube_video")

    assert result is not None
    d = result.to_dict()
    assert "creator_type" in d
    assert d["creator_type"] == "activist"
