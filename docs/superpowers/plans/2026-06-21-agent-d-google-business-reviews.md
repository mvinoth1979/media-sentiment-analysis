# Agent D — Google Business Review Connector

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Google Business reviews as a new ingestion source (Item 6). Reviews pull via the Google Places API, are ingested as `source_type=google_review`, and flow through the existing NLP pipeline. Brand admins configure their Google Place ID via the Channel Settings page.

**Architecture:** A new `google_reviews_collector.py` module handles the API calls. The collector follows the same pattern as `reddit_collector.py` — returns a list of article dicts using existing field names so no NLP or storage changes are needed. `orchestrator.py` calls it inside a new `if config.get("google_reviews_enabled")` block (identical in structure to the Reddit block). Two new columns in `brand_configs` store `google_places_id` and `google_reviews_enabled`.

**Tech Stack:** Python 3.12 · FastAPI · `httpx` (already a dependency for Resend alerts) · Supabase · React 19 · TypeScript · Tailwind CSS 4

## Global Constraints

- Python: use `from __future__ import annotations` in new files
- `httpx` is already available (used by `alerts.py`) — do not add new pip dependencies
- `GOOGLE_PLACES_API_KEY` env var: add to `app.config.settings`; collector must gracefully return `[]` when absent
- Migration naming: `019_google_reviews_config.sql` — run before application code
- `portal_id` for Google Business articles: `"google_business"` (constant string — not per-brand)
- `source_type`: `"google_review"` (new type — add to `_SOURCE_CONTEXT` in both NLP handlers)
- Credibility: `0.70` (mid-tier — below verified news portals but above social comments)
- Max 5 reviews per brand per run (Google Places API limit per Place Details response)

---

### Task 1: DB Migration — Google config columns

**Files:**
- Create: `backend/migrations/019_google_reviews_config.sql`

**Interfaces:**
- Produces: two new nullable columns on `brand_configs`: `google_places_id TEXT` and `google_reviews_enabled BOOLEAN DEFAULT FALSE`

- [ ] **Step 1: Write the migration**

```sql
-- backend/migrations/019_google_reviews_config.sql
-- Adds Google Business review configuration to brand_configs.

ALTER TABLE brand_configs
    ADD COLUMN IF NOT EXISTS google_places_id    TEXT,
    ADD COLUMN IF NOT EXISTS google_reviews_enabled BOOLEAN NOT NULL DEFAULT FALSE;
```

- [ ] **Step 2: Run the migration in Supabase**

Go to Supabase dashboard → SQL Editor → paste and run. Verify the two new columns appear on `brand_configs`.

---

### Task 2: Add `GOOGLE_PLACES_API_KEY` to settings

**Files:**
- Modify: `backend/app/config.py`

**Interfaces:**
- Produces: `settings.google_places_api_key: str | None`

- [ ] **Step 1: Read `config.py` and add the new setting**

Open `backend/app/config.py`. It defines a `Settings` class using Pydantic BaseSettings. Add:

```python
google_places_api_key: str | None = None
```

alongside the other optional API keys (after `groq_api_key` or similar). The field name must match the env var `GOOGLE_PLACES_API_KEY` exactly (Pydantic BaseSettings maps by field name, case-insensitive).

- [ ] **Step 2: Commit**

```bash
git add backend/app/config.py
git commit -m "config: add GOOGLE_PLACES_API_KEY to settings"
```

---

### Task 3: `google_reviews_collector.py` — New Collector

**Files:**
- Create: `backend/app/ingestion/google_reviews_collector.py`
- Test: `backend/tests/test_google_reviews.py`

**Interfaces:**
- Consumes:
  - `settings.google_places_api_key` from `app.config`
  - `brand: dict` — `{"id": "<uuid>", "name": "Brand Name", ...}`
  - `config: dict` — `{"google_places_id": "ChIJ...", "google_reviews_enabled": True, ...}`
- Produces: `collect_google_reviews_for_brand(brand, config) -> list[dict]`
  Each returned dict has: `brand_id`, `title`, `url`, `content_hash`, `language`, `source_type`, `source_platform`, `portal_id`, `portal_name`, `source_credibility`, `published_at`, `reach_metadata`

**API endpoints used:**
- Text Search: `POST https://places.googleapis.com/v1/places:searchText`
  - Body: `{"textQuery": "<brand_name>", "maxResultCount": 1}`
  - Header: `X-Goog-FieldMask: places.id`
- Place Details: `GET https://places.googleapis.com/v1/places/<place_id>`
  - Header: `X-Goog-FieldMask: id,displayName,reviews`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_google_reviews.py
from __future__ import annotations
from unittest.mock import patch, MagicMock
from app.ingestion.google_reviews_collector import collect_google_reviews_for_brand


def test_returns_empty_when_api_key_absent():
    brand  = {"id": "b1", "name": "Test Brand"}
    config = {"google_places_id": "ChIJabc", "google_reviews_enabled": True}
    with patch("app.ingestion.google_reviews_collector.settings") as mock_settings:
        mock_settings.google_places_api_key = None
        result = collect_google_reviews_for_brand(brand, config)
    assert result == []


def test_returns_empty_when_disabled():
    brand  = {"id": "b1", "name": "Test Brand"}
    config = {"google_places_id": "ChIJabc", "google_reviews_enabled": False}
    result = collect_google_reviews_for_brand(brand, config)
    assert result == []


def test_maps_review_to_article_dict():
    brand  = {"id": "b1", "name": "Test Brand"}
    config = {"google_places_id": "ChIJtest123", "google_reviews_enabled": True}

    fake_reviews = [
        {
            "name": "places/ChIJtest123/reviews/r1",
            "relativePublishTimeDescription": "2 weeks ago",
            "rating": 4,
            "text": {"text": "Great product, very happy with the service!"},
            "authorAttribution": {"displayName": "Happy Customer"},
            "publishTime": "2026-06-07T10:00:00Z",
        }
    ]
    fake_place_resp = MagicMock()
    fake_place_resp.status_code = 200
    fake_place_resp.json.return_value = {"id": "ChIJtest123", "reviews": fake_reviews}

    with patch("app.ingestion.google_reviews_collector.settings") as mock_settings, \
         patch("app.ingestion.google_reviews_collector.httpx.get", return_value=fake_place_resp):
        mock_settings.google_places_api_key = "fake-key"
        result = collect_google_reviews_for_brand(brand, config)

    assert len(result) == 1
    art = result[0]
    assert art["source_type"] == "google_review"
    assert art["portal_id"] == "google_business"
    assert art["brand_id"] == "b1"
    assert art["source_credibility"] == 0.70
    assert "Great product" in art["title"]
    assert art["reach_metadata"]["rating"] == 4
    assert "content_hash" in art


def test_text_search_used_when_no_places_id_stored():
    brand  = {"id": "b1", "name": "Test Brand"}
    config = {"google_places_id": "", "google_reviews_enabled": True}

    fake_search_resp = MagicMock()
    fake_search_resp.status_code = 200
    fake_search_resp.json.return_value = {"places": [{"id": "ChIJresolved"}]}

    fake_place_resp = MagicMock()
    fake_place_resp.status_code = 200
    fake_place_resp.json.return_value = {"id": "ChIJresolved", "reviews": []}

    with patch("app.ingestion.google_reviews_collector.settings") as mock_settings, \
         patch("app.ingestion.google_reviews_collector.httpx.post", return_value=fake_search_resp), \
         patch("app.ingestion.google_reviews_collector.httpx.get", return_value=fake_place_resp), \
         patch("app.ingestion.google_reviews_collector._save_places_id") as mock_save:
        mock_settings.google_places_api_key = "fake-key"
        result = collect_google_reviews_for_brand(brand, config)

    mock_save.assert_called_once_with("b1", "ChIJresolved")
    assert result == []  # no reviews in mock response
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && python -m pytest tests/test_google_reviews.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.ingestion.google_reviews_collector'`

- [ ] **Step 3: Implement `google_reviews_collector.py`**

```python
# backend/app/ingestion/google_reviews_collector.py
from __future__ import annotations
import hashlib
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.storage.postgres import get_db

log = logging.getLogger(__name__)

_PLACES_BASE  = "https://places.googleapis.com/v1"
_SEARCH_URL   = f"{_PLACES_BASE}/places:searchText"
_DETAIL_FIELD = "id,displayName,reviews"
_PORTAL_ID    = "google_business"
_PORTAL_NAME  = "Google Business"
_CREDIBILITY  = 0.70
_MAX_REVIEWS  = 5


def collect_google_reviews_for_brand(brand: dict, config: dict) -> list[dict]:
    if not config.get("google_reviews_enabled", False):
        return []
    api_key = settings.google_places_api_key
    if not api_key:
        log.debug("GOOGLE_PLACES_API_KEY not set — skipping Google reviews")
        return []

    brand_id   = brand["id"]
    brand_name = brand.get("name", "")
    places_id  = config.get("google_places_id") or ""

    if not places_id:
        places_id = _resolve_places_id(brand_name, api_key)
        if places_id:
            _save_places_id(brand_id, places_id)
        else:
            return []

    return _fetch_reviews(brand_id, places_id, api_key)


def _resolve_places_id(brand_name: str, api_key: str) -> str:
    try:
        resp = httpx.post(
            _SEARCH_URL,
            headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": "places.id"},
            json={"textQuery": brand_name, "maxResultCount": 1},
            timeout=10,
        )
        if resp.status_code == 200:
            places = resp.json().get("places", [])
            if places:
                return places[0].get("id", "")
    except Exception as e:
        log.warning("Google Places text search failed for %s: %s", brand_name, e)
    return ""


def _fetch_reviews(brand_id: str, places_id: str, api_key: str) -> list[dict]:
    url = f"{_PLACES_BASE}/places/{places_id}"
    try:
        resp = httpx.get(
            url,
            headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": _DETAIL_FIELD},
            timeout=10,
        )
        if resp.status_code != 200:
            log.warning("Google Place Details returned %d for %s", resp.status_code, places_id)
            return []
        data = resp.json()
    except Exception as e:
        log.warning("Google Place Details fetch failed for %s: %s", places_id, e)
        return []

    reviews = data.get("reviews") or []
    articles: list[dict] = []

    for review in reviews[:_MAX_REVIEWS]:
        text_obj   = review.get("text") or {}
        body_text  = text_obj.get("text") or ""
        if not body_text:
            continue

        author     = (review.get("authorAttribution") or {}).get("displayName") or "Anonymous"
        rating     = int(review.get("rating") or 0)
        publish_ts = review.get("publishTime") or datetime.now(timezone.utc).isoformat()
        title      = body_text[:120]

        raw_key = f"{brand_id}:{author}:{publish_ts}"
        content_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        articles.append({
            "brand_id":         brand_id,
            "title":            title,
            "url":              f"https://maps.google.com/maps/place/?q=place_id:{places_id}",
            "content_hash":     content_hash,
            "language":         "en",
            "source_type":      "google_review",
            "source_platform":  "review",
            "portal_id":        _PORTAL_ID,
            "portal_name":      _PORTAL_NAME,
            "source_credibility": _CREDIBILITY,
            "published_at":     publish_ts,
            "body":             body_text,
            "author":           author,
            "reach_metadata": {
                "rating": rating,
                "author": author,
                "relative_time": review.get("relativePublishTimeDescription") or "",
                "places_id": places_id,
            },
        })

    return articles


def _save_places_id(brand_id: str, places_id: str) -> None:
    try:
        db = get_db()
        db.table("brand_configs").update(
            {"google_places_id": places_id}
        ).eq("brand_id", brand_id).execute()
    except Exception as e:
        log.warning("Could not save places_id for brand %s: %s", brand_id[:8], e)
```

- [ ] **Step 4: Run tests**

```
cd backend && python -m pytest tests/test_google_reviews.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/ingestion/google_reviews_collector.py backend/tests/test_google_reviews.py
git commit -m "feat: google_reviews_collector — Places API v1 + content_hash + graceful no-op"
```

---

### Task 4: Add `google_review` source context to NLP handlers

**Files:**
- Modify: `backend/app/nlp/gemini_handler.py`
- Modify: `backend/app/nlp/groq_handler.py`

**Interfaces:**
- Produces: `_SOURCE_CONTEXT["google_review"]` defined in both handlers so `analyse_article()` gives it a proper prompt context instead of falling back to the news context

- [ ] **Step 1: Add to `gemini_handler.py`**

In `backend/app/nlp/gemini_handler.py`, in the `_SOURCE_CONTEXT` dict, add an entry after `"reddit_comment"`:

```python
    "google_review": (
        "This is a Google Business review. Star rating (1–5) is a strong explicit signal. "
        "Review text tends to be first-person experience — extract brand sentiment from the "
        "customer's stated satisfaction or complaint. states_mentioned will usually be empty. "
        "Confidence should reflect length and specificity of the review text."
    ),
```

- [ ] **Step 2: Add to `groq_handler.py`**

In `backend/app/nlp/groq_handler.py`, in the `_SOURCE_CONTEXT` dict, add the same entry after `"reddit_comment"`:

```python
    "google_review": (
        "Google Business review — star rating is a strong signal. "
        "First-person customer experience text; states_mentioned usually empty; "
        "confidence reflects review length and specificity."
    ),
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/nlp/gemini_handler.py backend/app/nlp/groq_handler.py
git commit -m "feat: google_review source context in Gemini + Groq NLP handlers"
```

---

### Task 5: Wire into `orchestrator.py`

**Files:**
- Modify: `backend/app/pipeline/orchestrator.py`

**Interfaces:**
- Consumes: `collect_google_reviews_for_brand(brand, config)` from `app.ingestion.google_reviews_collector`
- Produces: Google reviews collected when `config.get("google_reviews_enabled")` and `config.get("google_places_id")` are set

- [ ] **Step 1: Add the Google reviews block to `orchestrator.py`**

In `backend/app/pipeline/orchestrator.py`, after the existing Reddit block (lines ~84–97), add:

```python
        # Google Business reviews — sub-cap (5 reviews per run, Places API v1).
        # Only runs when brand_config.google_reviews_enabled = True and google_places_id is set.
        if config.get("google_reviews_enabled", False):
            try:
                from app.ingestion.google_reviews_collector import collect_google_reviews_for_brand
                gr_raw = collect_google_reviews_for_brand(brand, config)
                gr_new = filter_new_articles(gr_raw, brand_id)
                gr_new = [a for a in gr_new
                          if not is_rejected(brand_id, a.get("url", ""), a.get("title", ""))]
                new_articles.extend(gr_new)
                stats["collected"] += len(gr_raw)
            except Exception as e:
                log.error("Google reviews failed for brand %s: %s", brand_id[:8], e)
                stats["errors"] += 1
```

- [ ] **Step 2: Verify the app starts cleanly**

```
cd backend && uvicorn app.main:app --reload
```

Expected: starts without import errors

- [ ] **Step 3: Commit**

```bash
git add backend/app/pipeline/orchestrator.py
git commit -m "feat: Google reviews ingestion block in run_brand_pipeline"
```

---

### Task 6: Backend config endpoint — expose google fields

**Files:**
- Modify: `backend/app/tenants/router.py`

**Interfaces:**
- Consumes: existing `BrandConfigUpdate` Pydantic model and `GET/PUT /brands/{id}/config` endpoints
- Produces: `google_places_id` and `google_reviews_enabled` fields added to `BrandConfigUpdate` so the Channel Settings page can read and write them

- [ ] **Step 1: Add google fields to `BrandConfigUpdate`**

In `backend/app/tenants/router.py`, in the `BrandConfigUpdate` model, add:

```python
class BrandConfigUpdate(BaseModel):
    keywords: list[str] | None = None
    languages: list[str] | None = None
    states: list[str] | None = None
    competitors: list[str] | None = None
    portal_ids: list[str] | None = None
    youtube_enabled: bool | None = None
    youtube_channel_ids: list[str] | None = None
    reddit_enabled: bool | None = None
    reddit_subreddits: list[str] | None = None
    google_reviews_enabled: bool | None = None   # new
    google_places_id: str | None = None          # new
```

- [ ] **Step 2: Verify the PUT config endpoint already handles new fields**

Search for the `PUT /brands/{id}/config` handler in `tenants/router.py`. It should already use `payload.dict(exclude_none=True)` or similar to update only provided fields. If so, no further change is needed — the new fields will be passed through automatically.

If it explicitly lists fields, add `google_reviews_enabled` and `google_places_id` to the update dict.

- [ ] **Step 3: Commit**

```bash
git add backend/app/tenants/router.py
git commit -m "feat: google_reviews_enabled + google_places_id in BrandConfigUpdate"
```

---

### Task 7: Frontend — Google Business section in Channel Settings

**Files:**
- Modify: `frontend/src/pages/BrandConfig.tsx`

**Interfaces:**
- Consumes: `GET /brands/{brandId}/config` — returns config object now including `google_reviews_enabled` and `google_places_id`
- Produces: A new "Google Business Reviews" section in `BrandConfig.tsx` with a toggle switch and a place ID input

- [ ] **Step 1: Read `BrandConfig.tsx` to understand its structure**

Open `frontend/src/pages/BrandConfig.tsx`. It already has sections for YouTube and Reddit. Find the pattern for how each section renders its toggle + input fields.

- [ ] **Step 2: Add Google Business section**

After the Reddit section (or before the Save button), add:

```tsx
{/* Google Business Reviews */}
<div className="border border-gray-200 rounded-lg p-4">
  <div className="flex items-center justify-between mb-3">
    <div>
      <h3 className="text-sm font-medium text-gray-800">Google Business Reviews</h3>
      <p className="text-xs text-gray-500 mt-0.5">
        Pulls up to 5 recent reviews per pipeline run via Google Places API.
        Requires <code className="bg-gray-100 px-1 rounded text-[10px]">GOOGLE_PLACES_API_KEY</code> env var on the server.
      </p>
    </div>
    <button
      type="button"
      onClick={() => setConfig(c => ({ ...c, google_reviews_enabled: !c.google_reviews_enabled }))}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
        config.google_reviews_enabled ? "bg-indigo-600" : "bg-gray-200"
      }`}
    >
      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
        config.google_reviews_enabled ? "translate-x-4" : "translate-x-0.5"
      }`} />
    </button>
  </div>

  {config.google_reviews_enabled && (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1">
        Google Place ID
        <a
          href="https://developers.google.com/maps/documentation/places/web-service/place-id"
          target="_blank"
          rel="noopener noreferrer"
          className="ml-1 text-indigo-500 hover:underline"
        >
          (how to find yours)
        </a>
      </label>
      <input
        type="text"
        value={config.google_places_id || ""}
        onChange={e => setConfig(c => ({ ...c, google_places_id: e.target.value }))}
        placeholder="ChIJ..."
        className="w-full text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      />
      <p className="text-[10px] text-gray-400 mt-1">
        Leave empty to let MediaSense auto-resolve via brand name on first run.
      </p>
    </div>
  )}
</div>
```

The state shape for `config` should already include `google_reviews_enabled: boolean` and `google_places_id: string` — add them to the initial state if not present (follow the existing pattern for `reddit_enabled`/`reddit_subreddits`).

- [ ] **Step 3: Verify TypeScript compiles**

```
cd frontend && npx tsc --noEmit
```

Expected: no type errors

- [ ] **Step 4: Visual check**

Start dev server:
```
cd frontend && npm run dev
```

Go to any brand → Channel Settings. Verify:
- "Google Business Reviews" section appears below Reddit
- Toggle enables/disables the Place ID input
- Entering a place ID and saving sends the correct PUT request (check browser devtools)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/BrandConfig.tsx
git commit -m "feat: Google Business Reviews section in Channel Settings"
```

---

### Task 8: Final smoke test

- [ ] **Step 1: Add GOOGLE_PLACES_API_KEY to Railway env (optional)**

If you have a Google Cloud project with Places API enabled:
```
GOOGLE_PLACES_API_KEY=<your-key>
```

Add it via Railway dashboard → Variables. If no key, the collector will silently return `[]` — that's correct behavior.

- [ ] **Step 2: Enable google reviews for a test brand and run pipeline**

Via Supabase SQL:
```sql
UPDATE brand_configs
SET google_reviews_enabled = true, google_places_id = 'ChIJ...'
WHERE brand_id = '<your-test-brand-uuid>';
```

Trigger pipeline:
```
POST /pipeline/trigger   Authorization: Bearer <master_admin_token>
```

- [ ] **Step 3: Verify reviews appear as google_review articles**

```sql
SELECT title, source_type, portal_id, reach_metadata
FROM articles
WHERE brand_id = '<test-brand-uuid>' AND source_type = 'google_review'
ORDER BY collected_at DESC LIMIT 5;
```

Expected: rows with `source_type='google_review'` and `portal_id='google_business'`.

- [ ] **Step 4: Verify reviews appear in Mention Explorer**

In the frontend Mention Explorer for the test brand, look for the `google_review` source_type. The existing source_type filter dropdown should list "Google Review" (add it there if it currently only lists news/YT/Reddit options).

**Note:** if the source_type dropdown doesn't include `google_review`, find where the dropdown options are hardcoded in `MentionsList.tsx` or `Overview.tsx` and add: `{ value: "google_review", label: "Google Reviews" }`.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: agent D complete — Google Business review connector end-to-end"
```
