import os
import fasttext

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "lid.176.bin")
_model = None


def _get_model():
    global _model
    if _model is None:
        fasttext.FastText.eprint = lambda x: None  # suppress warnings
        _model = fasttext.load_model(_MODEL_PATH)
    return _model


def detect_language(text: str) -> tuple[str, float]:
    if not text or not text.strip():
        return "unknown", 0.0
    model = _get_model()
    clean = text.replace("\n", " ").strip()[:500]
    labels, probs = model.predict(clean, k=1)
    lang = labels[0].replace("__label__", "")
    return lang, float(probs[0])
