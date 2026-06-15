from unittest.mock import patch
from app.nlp.router import analyse_article
from app.nlp.schemas import NLPResult


def _mock_result(label: str, model: str) -> NLPResult:
    return NLPResult(sentiment_score=0.5, sentiment_label=label,
                     model_used=model, confidence=0.9)


def test_english_article_uses_gemini():
    with patch("app.nlp.router.analyse_with_gemini",
               return_value=_mock_result("positive", "gemini-2.0-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("en", 0.99)):
        result = analyse_article({"body": "Amul profits rise", "title": "Amul up", "language": "en"})

    assert result.model_used == "gemini-2.0-flash"
    mock_g.assert_called_once()


def test_tamil_article_uses_gemini():
    with patch("app.nlp.router.analyse_with_gemini",
               return_value=_mock_result("negative", "gemini-2.0-flash")), \
         patch("app.nlp.router.detect_language", return_value=("ta", 0.97)):
        result = analyse_article({"body": "அமுல் விலை", "title": "விலை", "language": "ta"})

    assert result is not None


def test_gemini_failure_falls_back_to_groq():
    with patch("app.nlp.router.analyse_with_gemini", return_value=None), \
         patch("app.nlp.router.analyse_with_groq",
               return_value=_mock_result("neutral", "groq-gemma2-9b-it")), \
         patch("app.nlp.router.detect_language", return_value=("en", 0.99)):
        result = analyse_article({"body": "Some text", "title": "Title", "language": "en"})

    assert result.model_used == "groq-gemma2-9b-it"


def test_both_fail_returns_none():
    with patch("app.nlp.router.analyse_with_gemini", return_value=None), \
         patch("app.nlp.router.analyse_with_groq", return_value=None), \
         patch("app.nlp.router.detect_language", return_value=("en", 0.9)):
        result = analyse_article({"body": "text", "title": "t", "language": "en"})

    assert result is None


def test_low_confidence_detection_uses_declared_language():
    with patch("app.nlp.router.analyse_with_gemini",
               return_value=_mock_result("neutral", "gemini-2.0-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("fr", 0.4)):
        result = analyse_article({"body": "Some text", "title": "Title", "language": "ta"})

    # Low confidence detection (0.4 < 0.75) → falls back to declared "ta"
    call_args = mock_g.call_args
    assert call_args[0][1] == "ta"


def test_unsupported_language_defaults_to_english():
    with patch("app.nlp.router.analyse_with_gemini",
               return_value=_mock_result("neutral", "gemini-2.0-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("de", 0.95)):
        analyse_article({"body": "German text", "title": "Title", "language": "de"})

    call_args = mock_g.call_args
    assert call_args[0][1] == "en"

def test_missing_title_and_body_defaults_to_english():
    with patch("app.nlp.router.analyse_with_gemini",
               return_value=_mock_result("neutral", "gemini-2.0-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("unknown", 0.0)):
        result = analyse_article({})

    assert result is not None
    call_args = mock_g.call_args
    assert call_args[0][1] == "en"

def test_missing_declared_language_defaults_to_english():
    with patch("app.nlp.router.analyse_with_gemini",
               return_value=_mock_result("positive", "gemini-2.0-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("fr", 0.3)):
        # Low confidence, no declared language → should default to "en"
        analyse_article({"body": "Some text", "title": "Title"})

    call_args = mock_g.call_args
    assert call_args[0][1] == "en"
