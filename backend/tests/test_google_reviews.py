"""Tests for Google Business Reviews collector.

Uses legacy Places Details API (maps.googleapis.com/maps/api/place/details/json).
All HTTP calls are mocked with unittest.mock.patch — no real network calls.
"""

import hashlib
from unittest.mock import MagicMock, call, patch

import httpx

# ---------------------------------------------------------------------------
# Helpers — legacy Places Details API response format
# ---------------------------------------------------------------------------

_BRAND = {"id": "brand-abc-123", "name": "Amul Dairy"}
_CONFIG_ENABLED = {
    "google_reviews_enabled": True,
    "google_places_id": "ChIJtesting12345",
}
_CONFIG_NO_ID = {
    "google_reviews_enabled": True,
    "google_places_id": "",
}
_CONFIG_DISABLED = {
    "google_reviews_enabled": False,
    "google_places_id": "ChIJtesting12345",
}

# Legacy API uses author_name (str), text (str), time (unix int)
_FAKE_REVIEW_1 = {
    "author_name": "Happy Customer",
    "rating": 5,
    "text": "Excellent products, very fresh milk every day!",
    "time": 1704880800,  # 2024-01-10T10:00:00Z
    "relative_time_description": "2 days ago",
}

_FAKE_REVIEW_2 = {
    "author_name": "Disappointed User",
    "rating": 2,
    "text": "Delivery was late and butter was melted.",
    "time": 1704614400,  # 2024-01-07T08:00:00Z
    "relative_time_description": "5 days ago",
}

# Legacy API wraps everything under result + status
_PLACES_RESPONSE = {
    "status": "OK",
    "result": {
        "name": "Amul Dairy",
        "rating": 4.2,
        "reviews": [_FAKE_REVIEW_1, _FAKE_REVIEW_2],
    },
}

# Legacy text search response format
_SEARCH_RESPONSE = {
    "status": "OK",
    "results": [
        {"place_id": "ChIJresolved99999", "name": "Amul Dairy"}
    ],
}


def _make_mock_response(json_data: dict, status_code: int = 200):
    """Return a mock httpx.Response with given JSON data."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status = MagicMock()
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=mock_resp
        )
    return mock_resp


# ---------------------------------------------------------------------------
# Test: no-op when GOOGLE_PLACES_API_KEY is absent
# ---------------------------------------------------------------------------

def test_collect_noop_when_api_key_absent(monkeypatch):
    """Collector returns [] immediately if GOOGLE_PLACES_API_KEY is not set."""
    monkeypatch.setattr("app.config.settings.google_places_api_key", "")
    from app.ingestion.google_reviews_collector import collect_google_reviews_for_brand
    result = collect_google_reviews_for_brand(_BRAND, _CONFIG_ENABLED)
    assert result == []


# ---------------------------------------------------------------------------
# Test: no-op when google_reviews_enabled is False
# ---------------------------------------------------------------------------

def test_collect_noop_when_disabled(monkeypatch):
    """Collector returns [] if google_reviews_enabled is False."""
    monkeypatch.setattr("app.config.settings.google_places_api_key", "fake-api-key")
    from app.ingestion.google_reviews_collector import collect_google_reviews_for_brand
    result = collect_google_reviews_for_brand(_BRAND, _CONFIG_DISABLED)
    assert result == []


# ---------------------------------------------------------------------------
# Test: fetches reviews using known places_id
# ---------------------------------------------------------------------------

def test_collect_with_known_places_id(monkeypatch):
    """When google_places_id is set, GETs the place directly and maps reviews."""
    monkeypatch.setattr("app.config.settings.google_places_api_key", "fake-api-key")

    with patch("httpx.get", return_value=_make_mock_response(_PLACES_RESPONSE)) as mock_get:
        from importlib import reload
        import app.ingestion.google_reviews_collector as mod
        reload(mod)
        result = mod.collect_google_reviews_for_brand(_BRAND, _CONFIG_ENABLED)

    assert len(result) == 2
    # Verify the GET was called with the legacy details endpoint
    call_url = mock_get.call_args[0][0]
    assert "place/details" in call_url

    # Verify article structure
    article = result[0]
    assert article["brand_id"] == "brand-abc-123"
    assert article["source_type"] == "google_review"
    assert article["portal_id"] == "google_business"
    assert article["source_credibility"] == 0.70
    assert "content_hash" in article
    assert len(article["content_hash"]) == 64  # SHA256 hex = 64 chars
    assert "published_at" in article
    assert "body" in article
    assert "title" in article


# ---------------------------------------------------------------------------
# Test: content_hash is deterministic
# ---------------------------------------------------------------------------

def test_content_hash_deterministic():
    """Same brand_id + author + unix_time always yields same hash."""
    brand_id = "brand-abc-123"
    author = "Happy Customer"
    # Legacy API uses unix timestamp (int) as the publish_key
    time_val = 1704880800
    expected = hashlib.sha256(f"{brand_id}:{author}:{time_val}".encode()).hexdigest()

    with patch("httpx.get", return_value=_make_mock_response(_PLACES_RESPONSE)):
        from importlib import reload
        import app.config as cfg_mod
        cfg_mod.settings.google_places_api_key = "fake-api-key"
        import app.ingestion.google_reviews_collector as mod
        reload(mod)
        result = mod.collect_google_reviews_for_brand(_BRAND, _CONFIG_ENABLED)

    assert result[0]["content_hash"] == expected


# ---------------------------------------------------------------------------
# Test: resolves place ID via text search when google_places_id is empty
# ---------------------------------------------------------------------------

def test_resolves_place_id_via_search(monkeypatch):
    """When google_places_id is empty, GETs text search and resolves ID."""
    monkeypatch.setattr("app.config.settings.google_places_api_key", "fake-api-key")

    # Both search and details use GET in the legacy API
    place_details_response = {
        "status": "OK",
        "result": {
            "name": "Amul Dairy",
            "reviews": [_FAKE_REVIEW_1],
        },
    }
    search_resp = _make_mock_response(_SEARCH_RESPONSE)
    place_resp = _make_mock_response(place_details_response)

    import app.ingestion.google_reviews_collector as mod

    with patch("httpx.get", side_effect=[search_resp, place_resp]) as mock_get, \
         patch.object(mod, "_save_places_id") as mock_save:
        result = mod.collect_google_reviews_for_brand(_BRAND, _CONFIG_NO_ID)

    # First GET → text search endpoint
    first_url = mock_get.call_args_list[0][0][0]
    assert "textsearch" in first_url

    # Second GET → place details with resolved ID in params
    second_kwargs = mock_get.call_args_list[1][1]
    assert second_kwargs["params"]["place_id"] == "ChIJresolved99999"

    # Verify the resolved ID was saved back
    mock_save.assert_called_once_with("brand-abc-123", "ChIJresolved99999")

    assert len(result) == 1


# ---------------------------------------------------------------------------
# Test: graceful no-op when search returns no results
# ---------------------------------------------------------------------------

def test_graceful_noop_when_search_empty(monkeypatch):
    """Returns [] when text search finds no places."""
    monkeypatch.setattr("app.config.settings.google_places_api_key", "fake-api-key")

    empty_search = _make_mock_response({"status": "ZERO_RESULTS", "results": []})
    with patch("httpx.get", return_value=empty_search):
        from importlib import reload
        import app.ingestion.google_reviews_collector as mod
        reload(mod)
        result = mod.collect_google_reviews_for_brand(_BRAND, _CONFIG_NO_ID)

    assert result == []


# ---------------------------------------------------------------------------
# Test: graceful no-op when HTTP error occurs
# ---------------------------------------------------------------------------

def test_graceful_noop_on_http_error(monkeypatch):
    """Returns [] and does not raise when the Places API returns an error."""
    monkeypatch.setattr("app.config.settings.google_places_api_key", "fake-api-key")

    with patch("httpx.get", return_value=_make_mock_response({}, status_code=403)):
        from importlib import reload
        import app.ingestion.google_reviews_collector as mod
        reload(mod)
        result = mod.collect_google_reviews_for_brand(_BRAND, _CONFIG_ENABLED)

    assert result == []


# ---------------------------------------------------------------------------
# Test: caps results at 5 reviews
# ---------------------------------------------------------------------------

def test_caps_at_five_reviews(monkeypatch):
    """Collector returns at most 5 reviews even if API returns more."""
    monkeypatch.setattr("app.config.settings.google_places_api_key", "fake-api-key")

    many_reviews = [
        {
            "author_name": f"User{i}",
            "rating": 4,
            "text": f"Review text number {i} with enough content",
            "time": 1704880800 + i * 86400,
            "relative_time_description": f"{i} days ago",
        }
        for i in range(10)
    ]
    response_with_many = {
        "status": "OK",
        "result": {
            "name": "Amul Dairy",
            "reviews": many_reviews,
        },
    }

    with patch("httpx.get", return_value=_make_mock_response(response_with_many)):
        from importlib import reload
        import app.ingestion.google_reviews_collector as mod
        reload(mod)
        result = mod.collect_google_reviews_for_brand(_BRAND, _CONFIG_ENABLED)

    assert len(result) <= 5


# ---------------------------------------------------------------------------
# Test: NLP source context entries exist in both handlers
# ---------------------------------------------------------------------------

def test_gemini_handler_has_google_review_context():
    """gemini_handler._SOURCE_CONTEXT contains 'google_review' key."""
    from app.nlp.gemini_handler import _SOURCE_CONTEXT
    assert "google_review" in _SOURCE_CONTEXT
    ctx = _SOURCE_CONTEXT["google_review"]
    assert isinstance(ctx, str)
    assert len(ctx) > 10


def test_groq_handler_has_google_review_context():
    """groq_handler._SOURCE_CONTEXT contains 'google_review' key."""
    from app.nlp.groq_handler import _SOURCE_CONTEXT
    assert "google_review" in _SOURCE_CONTEXT
    ctx = _SOURCE_CONTEXT["google_review"]
    assert isinstance(ctx, str)
    assert len(ctx) > 10


# ---------------------------------------------------------------------------
# Test: BrandConfigUpdate model accepts new fields
# ---------------------------------------------------------------------------

def test_brand_config_update_accepts_google_fields():
    """BrandConfigUpdate Pydantic model accepts google_places_id and google_reviews_enabled."""
    from app.tenants.router import BrandConfigUpdate
    payload = BrandConfigUpdate(
        google_places_id="ChIJtesting12345",
        google_reviews_enabled=True,
    )
    assert payload.google_places_id == "ChIJtesting12345"
    assert payload.google_reviews_enabled is True


def test_brand_config_update_google_fields_default_none():
    """google_places_id and google_reviews_enabled default to None when not provided."""
    from app.tenants.router import BrandConfigUpdate
    payload = BrandConfigUpdate()
    assert payload.google_places_id is None
    assert payload.google_reviews_enabled is None
