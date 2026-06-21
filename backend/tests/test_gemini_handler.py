import json
from unittest.mock import patch, MagicMock
from app.nlp.gemini_handler import analyse_with_gemini, _parse_creator_type
from app.nlp.schemas import NLPResult

MOCK_RESPONSE = json.dumps({
    "sentiment_score": 0.75,
    "sentiment_label": "positive",
    "entities": ["Amul", "Chennai"],
    "topics": ["product_launch", "pricing"],
    "keywords": ["new", "product", "affordable"],
    "confidence": 0.91
})

def test_gemini_returns_nlp_result():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = MOCK_RESPONSE

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, rate_limited = analyse_with_gemini("Amul launches affordable product in Chennai", "en")

    assert isinstance(result, NLPResult)
    assert result.sentiment_label == "positive"
    assert result.sentiment_score == 0.75
    assert "Amul" in result.entities
    assert result.model_used == "gemini-2.0-flash"
    assert rate_limited is False

def test_gemini_handles_invalid_json():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "not json"

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, rate_limited = analyse_with_gemini("Some text", "en")

    assert result is None
    assert rate_limited is False

def test_gemini_handles_markdown_fenced_json():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = f"```json\n{MOCK_RESPONSE}\n```"

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("Amul product in Chennai", "en")

    assert result is not None
    assert result.sentiment_label == "positive"

def test_gemini_handles_bare_fence():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = f"```\n{MOCK_RESPONSE}\n```"

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("Amul product", "en")

    assert result is not None
    assert result.sentiment_score == 0.75

def test_gemini_api_exception_returns_none():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API error")

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, rate_limited = analyse_with_gemini("Some text", "en")

    assert result is None
    assert rate_limited is False

def test_gemini_clamps_out_of_range_score():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        "sentiment_score": 1.8,
        "sentiment_label": "positive",
        "confidence": 0.9
    })

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("Some text", "en")

    assert result is not None
    assert result.sentiment_score == 1.0

def test_gemini_normalizes_invalid_label():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        "sentiment_score": 0.3,
        "sentiment_label": "mixed",
        "confidence": 0.7
    })

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("Some text", "en")

    assert result is not None
    assert result.sentiment_label == "neutral"


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
    assert _parse_creator_type("  Journalist  ") == "journalist"
    assert _parse_creator_type("Industry Expert") == "industry_expert"
    assert _parse_creator_type("REVIEWER") == "reviewer"

def test_parse_creator_type_invalid_falls_back_to_unknown():
    assert _parse_creator_type("random_type") == "unknown"
    assert _parse_creator_type("") == "unknown"
    assert _parse_creator_type("celebrity") == "unknown"

def test_gemini_creator_type_set_for_youtube_video():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        "sentiment_score": 0.5,
        "sentiment_label": "positive",
        "entities": [],
        "topics": [],
        "keywords": [],
        "states_mentioned": [],
        "issue_category": "other",
        "creator_type": "reviewer",
        "confidence": 0.85,
    })

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("Great product review!", "en", source_type="youtube_video")

    assert result is not None
    assert result.creator_type == "reviewer"
    assert result.source_type == "youtube_video"

def test_gemini_creator_type_unknown_for_non_youtube():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        "sentiment_score": 0.3,
        "sentiment_label": "neutral",
        "entities": [],
        "topics": [],
        "keywords": [],
        "states_mentioned": [],
        "issue_category": "other",
        "creator_type": "journalist",  # would be set in prompt, but source is news
        "confidence": 0.7,
    })

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("News article text", "en", source_type="news")

    assert result is not None
    assert result.creator_type == "unknown"

def test_gemini_creator_type_defaults_unknown_when_missing_in_response():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        "sentiment_score": 0.4,
        "sentiment_label": "neutral",
        "entities": [],
        "topics": [],
        "keywords": [],
        "confidence": 0.7,
        # creator_type field absent
    })

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("YT video text", "en", source_type="youtube_video")

    assert result is not None
    assert result.creator_type == "unknown"

def test_gemini_creator_type_invalid_value_falls_back_to_unknown():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        "sentiment_score": 0.6,
        "sentiment_label": "positive",
        "entities": [],
        "topics": [],
        "keywords": [],
        "creator_type": "celebrity",  # invalid value
        "confidence": 0.8,
    })

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("YT video text", "en", source_type="youtube_video")

    assert result is not None
    assert result.creator_type == "unknown"

def test_gemini_creator_type_in_to_dict():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        "sentiment_score": 0.5,
        "sentiment_label": "positive",
        "entities": [],
        "topics": [],
        "keywords": [],
        "creator_type": "influencer",
        "confidence": 0.9,
    })

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result, _ = analyse_with_gemini("YT video", "en", source_type="youtube_video")

    assert result is not None
    d = result.to_dict()
    assert "creator_type" in d
    assert d["creator_type"] == "influencer"
