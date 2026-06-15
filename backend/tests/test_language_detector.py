from app.nlp.language_detector import detect_language


def test_detects_english():
    lang, conf = detect_language("The company announced record profits this quarter.")
    assert lang == "en"
    assert conf > 0.8


def test_detects_tamil():
    lang, conf = detect_language("நிறுவனம் இந்த காலாண்டில் சாதனை லாபத்தை அறிவித்தது.")
    assert lang == "ta"
    assert conf > 0.8


def test_short_text_returns_result():
    lang, conf = detect_language("hello")
    assert isinstance(lang, str)
    assert 0.0 <= conf <= 1.0


def test_empty_text_returns_unknown():
    lang, conf = detect_language("")
    assert lang == "unknown"
    assert conf == 0.0
