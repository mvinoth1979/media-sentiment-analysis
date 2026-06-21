import pathlib
import fasttext

_MODEL_PATH = pathlib.Path(__file__).parent.parent.parent / "models" / "lid.176.bin"

# Load once at module import; fasttext.load_model is thread-safe for inference.
try:
    _model = fasttext.load_model(str(_MODEL_PATH))
except Exception as _e:
    _model = None
    import warnings
    warnings.warn(f"FastText LID model not loaded: {_e}. Language detection will return 'unknown'.")


def detect_language(text: str) -> tuple[str, float]:
    if not text or not text.strip():
        return "unknown", 0.0
    if _model is None:
        return "unknown", 0.0
    clean = text[:500].replace("\n", " ")
    labels, scores = _model.predict(clean, k=1)
    lang = labels[0].replace("__label__", "")
    return lang, float(scores[0])
