from unittest.mock import patch, MagicMock
from app.nlp.router import analyse_article
from app.nlp.schemas import NLPResult


def _ok(label: str, model: str) -> tuple:
    """Helper: successful (result, rate_limited=False) from _call_gemini/_call_groq."""
    return (NLPResult(sentiment_score=0.5, sentiment_label=label,
                      model_used=model, confidence=0.9), False)


def _fail() -> tuple:
    return (None, False)


# _call_gemini and _call_groq are the internal tier helpers in router.py.
# Patching these is cleaner than going through APIRouter + analyse_with_gemini.
_GEMINI = "app.nlp.router._call_gemini"
_GROQ   = "app.nlp.router._call_groq"

# Articles must be >8 words to bypass the short-text Tier-0 gate.
_EN_ARTICLE = {
    "title": "Amul quarterly profits rise sharply",
    "body":  "Amul reported strong quarterly results with revenue and profitability both rising significantly above analyst expectations this quarter.",
    "language": "en",
}
_TA_ARTICLE = {
    "title": "அமுல் நிறுவனம் விலை உயர்வு அறிவித்தது",
    "body":  "அமுல் நிறுவனம் பால் மற்றும் வெண்ணெய் விலையை அடுத்த மாதம் முதல் உயர்த்தப் போவதாக அறிவித்துள்ளது.",
    "language": "ta",
}


def test_english_article_uses_gemini():
    with patch(_GEMINI, return_value=_ok("positive", "gemini-2.5-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("en", 0.99)):
        result = analyse_article(_EN_ARTICLE)

    assert result.model_used == "gemini-2.5-flash"
    mock_g.assert_called_once()


def test_tamil_article_uses_gemini():
    with patch(_GEMINI, return_value=_ok("negative", "gemini-2.5-flash")), \
         patch("app.nlp.router.detect_language", return_value=("ta", 0.97)):
        result = analyse_article(_TA_ARTICLE)

    assert result is not None


def test_gemini_failure_falls_back_to_groq():
    with patch(_GEMINI, return_value=_fail()), \
         patch(_GROQ, return_value=_ok("neutral", "groq-llama-3.1-8b-instant")) as mock_q, \
         patch("app.nlp.router.detect_language", return_value=("en", 0.99)):
        result = analyse_article(_EN_ARTICLE)

    assert result.model_used == "groq-llama-3.1-8b-instant"
    mock_q.assert_called_once()


def test_both_fail_returns_none():
    with patch(_GEMINI, return_value=_fail()), \
         patch(_GROQ, return_value=_fail()), \
         patch("app.nlp.router.detect_language", return_value=("en", 0.9)):
        result = analyse_article(_EN_ARTICLE)

    assert result is None


def test_low_confidence_detection_uses_declared_language():
    ta_article = {**_TA_ARTICLE, "language": "ta"}
    with patch(_GEMINI, return_value=_ok("neutral", "gemini-2.5-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("fr", 0.4)):
        analyse_article(ta_article)

    # Low confidence (0.4 < 0.75) → stays with declared "ta" → Gemini paid tier
    # _call_gemini(text, language, source_type, title, body, paid)
    call_args = mock_g.call_args
    assert call_args[0][1] == "ta"


def test_unsupported_language_defaults_to_english():
    article = {**_EN_ARTICLE, "language": "de"}
    with patch(_GEMINI, return_value=_ok("neutral", "gemini-2.5-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("de", 0.95)):
        analyse_article(article)

    call_args = mock_g.call_args
    assert call_args[0][1] == "en"


def test_missing_title_and_body_defaults_to_english():
    # Article without language key and with sufficient body text
    article = {
        "title": "Quarterly results beat estimates",
        "body":  "The company reported revenue growth beating most analyst estimates by wide margin this quarter.",
    }
    with patch(_GEMINI, return_value=_ok("neutral", "gemini-2.5-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("unknown", 0.0)):
        result = analyse_article(article)

    assert result is not None
    call_args = mock_g.call_args
    assert call_args[0][1] == "en"


def test_missing_declared_language_defaults_to_english():
    article = {
        "title": "Brand sales performance review",
        "body":  "Company announced strong sales performance across all product categories and market segments this fiscal year.",
    }
    with patch(_GEMINI, return_value=_ok("positive", "gemini-2.5-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("fr", 0.3)):
        # Low confidence detection, no declared language → default "en"
        analyse_article(article)

    call_args = mock_g.call_args
    assert call_args[0][1] == "en"
