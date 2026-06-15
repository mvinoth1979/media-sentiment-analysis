import json
from unittest.mock import patch, MagicMock
from app.nlp.gemini_handler import analyse_with_gemini
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
        result = analyse_with_gemini("Amul launches affordable product in Chennai", "en")

    assert isinstance(result, NLPResult)
    assert result.sentiment_label == "positive"
    assert result.sentiment_score == 0.75
    assert "Amul" in result.entities
    assert result.model_used == "gemini-2.0-flash"

def test_gemini_handles_invalid_json():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "not json"

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result = analyse_with_gemini("Some text", "en")

    assert result is None

def test_gemini_handles_markdown_fenced_json():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = f"```json\n{MOCK_RESPONSE}\n```"

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result = analyse_with_gemini("Amul product in Chennai", "en")

    assert result is not None
    assert result.sentiment_label == "positive"

def test_gemini_handles_bare_fence():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = f"```\n{MOCK_RESPONSE}\n```"

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result = analyse_with_gemini("Amul product", "en")

    assert result is not None
    assert result.sentiment_score == 0.75

def test_gemini_api_exception_returns_none():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API error")

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result = analyse_with_gemini("Some text", "en")

    assert result is None

def test_gemini_clamps_out_of_range_score():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        "sentiment_score": 1.8,
        "sentiment_label": "positive",
        "confidence": 0.9
    })

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result = analyse_with_gemini("Some text", "en")

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
        result = analyse_with_gemini("Some text", "en")

    assert result is not None
    assert result.sentiment_label == "neutral"
