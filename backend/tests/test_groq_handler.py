import json
from unittest.mock import patch, MagicMock
from app.nlp.groq_handler import analyse_with_groq
from app.nlp.schemas import NLPResult

MOCK_RESPONSE = json.dumps({
    "sentiment_score": -0.6,
    "sentiment_label": "negative",
    "entities": ["Amul"],
    "topics": ["pricing"],
    "keywords": ["price", "hike", "expensive"],
    "confidence": 0.82
})

def test_groq_returns_nlp_result():
    mock_choice = MagicMock()
    mock_choice.message.content = MOCK_RESPONSE
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result = analyse_with_groq("Amul hikes prices again", "en")

    assert isinstance(result, NLPResult)
    assert result.sentiment_label == "negative"
    assert result.model_used == "groq-gemma2-9b-it"

def test_groq_returns_none_on_failure():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result = analyse_with_groq("Some text", "ta")

    assert result is None
