# Agent E — YouTube Creator Type Classification

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Classify the creator of each YouTube video into one of 7 types (journalist, reviewer, influencer, customer, industry_expert, activist, competitor_affiliate, unknown) using the existing Gemini/Groq NLP call, store the result, and display it as a badge in the Mention Explorer (Item 9).

**Architecture:** `creator_type` is added as a new field to `NLPResult` and parsed from the existing `youtube_video` Gemini/Groq JSON response — no extra API calls. The DB column is added via migration 020. `save_article()` stores it automatically because it already does `{**article, **nlp_dict}` merge. The frontend adds a small pill badge in `MentionsList.tsx` for YouTube video rows.

**Tech Stack:** Python 3.12 · Gemini 2.0 Flash (primary) · Groq Llama (fallback) · Supabase · React 19 · TypeScript · Tailwind CSS 4

## Global Constraints

- `creator_type` is ONLY classified for `source_type == "youtube_video"` — skip for comments, news, Reddit, Google reviews
- Zero extra API cost: `creator_type` is one more field in the existing JSON schema returned by each `youtube_video` NLP call
- Valid values: `"journalist" | "reviewer" | "influencer" | "customer" | "industry_expert" | "activist" | "competitor_affiliate" | "unknown"`
- Default: `"unknown"` — used when classification is uncertain or source_type is not youtube_video
- Migration naming: `020_creator_type.sql`
- `save_article()` in `postgres.py` does NOT need to change — it already merges all nlp dict fields; Supabase upsert will pick up the new column after migration

---

### Task 1: DB Migration — `creator_type` column

**Files:**
- Create: `backend/migrations/020_creator_type.sql`

**Interfaces:**
- Produces: `creator_type VARCHAR(50)` column on `articles`, nullable (existing rows get NULL, treated as "unknown")

- [ ] **Step 1: Write the migration**

```sql
-- backend/migrations/020_creator_type.sql
-- Adds creator type classification for YouTube video articles.
-- Only populated for source_type = 'youtube_video'.
-- Valid values: journalist | reviewer | influencer | customer | industry_expert | activist | competitor_affiliate | unknown

ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS creator_type VARCHAR(50);
```

- [ ] **Step 2: Run the migration in Supabase**

Go to Supabase dashboard → SQL Editor → paste and run. Verify `creator_type` column appears on the `articles` table (nullable, VARCHAR 50).

---

### Task 2: Extend `NLPResult` schema

**Files:**
- Modify: `backend/app/nlp/schemas.py`
- Test: `backend/tests/test_nlp_schemas.py` (extend existing file)

**Interfaces:**
- Produces: `NLPResult.creator_type: str = "unknown"` field; `to_dict()` returns `"creator_type": self.creator_type`

- [ ] **Step 1: Write failing test**

Add to `backend/tests/test_nlp_schemas.py`:

```python
# Add to existing test_nlp_schemas.py

from app.nlp.schemas import NLPResult

def test_creator_type_defaults_to_unknown():
    result = NLPResult(
        sentiment_score=0.5,
        sentiment_label="positive",
    )
    assert result.creator_type == "unknown"

def test_creator_type_in_to_dict():
    result = NLPResult(
        sentiment_score=0.5,
        sentiment_label="positive",
        creator_type="reviewer",
    )
    d = result.to_dict()
    assert d["creator_type"] == "reviewer"

def test_creator_type_unknown_when_not_yt_video():
    result = NLPResult(
        sentiment_score=-0.3,
        sentiment_label="negative",
        source_type="youtube_comment",
    )
    assert result.creator_type == "unknown"
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && python -m pytest tests/test_nlp_schemas.py::test_creator_type_defaults_to_unknown -v
```

Expected: `AttributeError` — `NLPResult` has no attribute `creator_type`

- [ ] **Step 3: Add `creator_type` to `NLPResult` in `schemas.py`**

In `backend/app/nlp/schemas.py`, add the field after `issue_category`:

```python
    # YouTube creator type classification (youtube_video only; "unknown" for all others)
    creator_type: str = "unknown"
```

Add to `to_dict()` return value:

```python
            "creator_type": self.creator_type,
```

- [ ] **Step 4: Run tests**

```
cd backend && python -m pytest tests/test_nlp_schemas.py -v
```

Expected: all tests pass including the 3 new ones

- [ ] **Step 5: Commit**

```bash
git add backend/app/nlp/schemas.py backend/tests/test_nlp_schemas.py
git commit -m "feat: creator_type field on NLPResult (default: unknown)"
```

---

### Task 3: Gemini handler — classify creator type for YouTube videos

**Files:**
- Modify: `backend/app/nlp/gemini_handler.py`
- Test: `backend/tests/test_gemini_handler.py` (extend existing file)

**Interfaces:**
- Consumes: existing `analyse_with_gemini()` function; `_PROMPT_COMBINED` template (used for youtube_video)
- Produces: `NLPResult.creator_type` populated from Gemini response JSON when `source_type == "youtube_video"`

- [ ] **Step 1: Add `_VALID_CREATOR_TYPES` and `_parse_creator_type` to `gemini_handler.py`**

Add after `_VALID_CATEGORIES` in `backend/app/nlp/gemini_handler.py`:

```python
_VALID_CREATOR_TYPES = {
    "journalist", "reviewer", "influencer", "customer",
    "industry_expert", "activist", "competitor_affiliate", "unknown",
}


def _parse_creator_type(ct: str) -> str:
    normalized = ct.lower().strip().replace(" ", "_")
    return normalized if normalized in _VALID_CREATOR_TYPES else "unknown"
```

- [ ] **Step 2: Add `creator_type` to `_PROMPT_COMBINED`**

In `backend/app/nlp/gemini_handler.py`, modify `_PROMPT_COMBINED` to add the `creator_type` field. Find the JSON schema block inside the prompt and add:

```
  "creator_type": <for youtube_video only: "journalist" | "reviewer" | "influencer" | "customer" | "industry_expert" | "activist" | "competitor_affiliate" | "unknown". Use "unknown" for news and comments.>,
```

The field sits after `"issue_category"` in the JSON schema. The full updated schema block in the prompt looks like:

```python
_PROMPT_COMBINED = """Analyse the sentiment of the following text for the brand/product mentions it contains.

Source context: {source_context}

Return ONLY valid JSON with this exact schema:
{{
  "sentiment_score": <float from -1.0 (very negative) to +1.0 (very positive)>,
  "sentiment_label": <"positive" | "negative" | "neutral">,
  "entities": [<named entities: brands, people, locations, products>],
  "topics": [<topics from: product_quality, pricing, customer_service, leadership, campaign, legal, expansion, financial, other>],
  "keywords": [<up to 8 significant keywords>],
  "states_mentioned": [<Indian states or UTs explicitly named or clearly implied by a city/region in the text. Use only full official state names from this list: {states}. Empty list if none found.>],
  "issue_category": <one of: "financial_performance"|"regulatory_compliance"|"product_quality"|"leadership_governance"|"crisis_controversy"|"awards_recognition"|"csr_sustainability"|"policy_government"|"competitive_landscape"|"customer_experience"|"brand_advocacy"|"market_opportunity"|"other">,
  "creator_type": <for youtube_video source: "journalist"|"reviewer"|"influencer"|"customer"|"industry_expert"|"activist"|"competitor_affiliate"|"unknown". Use "unknown" for all non-video sources.>,
  "confidence": <float 0.0 to 1.0>
}}

Language: {language}
Text:
{text}"""
```

- [ ] **Step 3: Parse `creator_type` in `analyse_with_gemini`**

In the `NLPResult(...)` constructor call within `analyse_with_gemini`, add:

```python
                issue_category=_parse_category(data.get("issue_category", "other")),
                creator_type=_parse_creator_type(data.get("creator_type", "unknown")) if source_type == "youtube_video" else "unknown",
```

(Replace the existing `issue_category=` line and add the new `creator_type=` line right after it.)

- [ ] **Step 4: Write test for creator type parsing**

Add to `backend/tests/test_gemini_handler.py`:

```python
# Add to existing test_gemini_handler.py
from app.nlp.gemini_handler import _parse_creator_type

def test_parse_creator_type_valid():
    assert _parse_creator_type("reviewer") == "reviewer"
    assert _parse_creator_type("Industry Expert") == "industry_expert"

def test_parse_creator_type_invalid_returns_unknown():
    assert _parse_creator_type("celebrity") == "unknown"
    assert _parse_creator_type("") == "unknown"
```

- [ ] **Step 5: Run tests**

```
cd backend && python -m pytest tests/test_gemini_handler.py -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/nlp/gemini_handler.py backend/tests/test_gemini_handler.py
git commit -m "feat: creator_type in Gemini NLP — youtube_video prompt + parsing"
```

---

### Task 4: Groq handler — same `creator_type` addition

**Files:**
- Modify: `backend/app/nlp/groq_handler.py`
- Test: `backend/tests/test_groq_handler.py` (extend)

**Interfaces:**
- Consumes: existing `analyse_with_groq()` function; `_PROMPT` template (Groq uses a single combined prompt, not separate news/combined paths)
- Produces: `NLPResult.creator_type` populated from Groq JSON when `source_type == "youtube_video"`

- [ ] **Step 1: Read the groq handler to find where to add**

Open `backend/app/nlp/groq_handler.py`. Find:
1. Where `_VALID_CATEGORIES` is defined — add `_VALID_CREATOR_TYPES` and `_parse_creator_type` directly after it (identical to the Gemini version)
2. The `_PROMPT` or prompt template — add `"creator_type"` to the JSON schema exactly as done in Task 3 Step 2
3. The `NLPResult(...)` constructor in `analyse_with_groq()` — add `creator_type=` exactly as in Task 3 Step 3

- [ ] **Step 2: Add `_VALID_CREATOR_TYPES` and `_parse_creator_type` to `groq_handler.py`**

After `_VALID_CATEGORIES`:

```python
_VALID_CREATOR_TYPES = {
    "journalist", "reviewer", "influencer", "customer",
    "industry_expert", "activist", "competitor_affiliate", "unknown",
}


def _parse_creator_type(ct: str) -> str:
    normalized = ct.lower().strip().replace(" ", "_")
    return normalized if normalized in _VALID_CREATOR_TYPES else "unknown"
```

- [ ] **Step 3: Update the Groq prompt template**

Find the JSON schema in the Groq prompt string and add `"creator_type"` after `"issue_category"` — identical wording to the Gemini version.

- [ ] **Step 4: Update the `NLPResult` constructor in `analyse_with_groq`**

Add `creator_type=_parse_creator_type(...) if source_type == "youtube_video" else "unknown"` alongside the other parsed fields.

- [ ] **Step 5: Write test**

Add to `backend/tests/test_groq_handler.py`:

```python
from app.nlp.groq_handler import _parse_creator_type

def test_groq_parse_creator_type_valid():
    assert _parse_creator_type("journalist") == "journalist"

def test_groq_parse_creator_type_invalid():
    assert _parse_creator_type("random") == "unknown"
```

- [ ] **Step 6: Run tests**

```
cd backend && python -m pytest tests/test_groq_handler.py -v
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/nlp/groq_handler.py backend/tests/test_groq_handler.py
git commit -m "feat: creator_type in Groq NLP handler — matching Gemini implementation"
```

---

### Task 5: Frontend — creator type badge in Mention Explorer

**Files:**
- Modify: `frontend/src/components/mentions/MentionsList.tsx`

**Interfaces:**
- Consumes: `ArticleItem.creator_type: string` (already returned by `/dashboard/mentions/{brand_id}` via `_article_to_item()`)

**Note:** `_article_to_item()` in `router.py` uses `a.get("creator_type") or None` — add this mapping if it's not already present. Also expose `creator_type` on `ArticleItem` schema in `schemas.py` if not yet there.

- [ ] **Step 1: Add `creator_type` to `ArticleItem` schema (if missing)**

In `backend/app/dashboard/schemas.py`, in `ArticleItem`, add:

```python
    creator_type: str | None = None
```

(after `issue_category`)

- [ ] **Step 2: Expose `creator_type` in `_article_to_item`**

In `backend/app/dashboard/router.py`, in `_article_to_item()`, add:

```python
        creator_type=a.get("creator_type") or None,
```

(after `issue_category=a.get("issue_category") or "other"`)

- [ ] **Step 3: Add `creator_type` to the frontend `ArticleItem` type**

Find the TypeScript type definition for `ArticleItem` in `frontend/src/lib/types.ts` (or wherever it's defined). Add:

```typescript
creator_type?: string | null;
```

- [ ] **Step 4: Add creator type badge to `MentionsList.tsx`**

In `frontend/src/components/mentions/MentionsList.tsx`, find where the article row metadata badges are rendered (sentiment badge, source_type badge, divergence badge, etc.). After the `source_type` badge, add:

```tsx
{item.source_type === "youtube_video" && item.creator_type && item.creator_type !== "unknown" && (
  <span className="text-[9px] px-1.5 py-0.5 bg-purple-50 text-purple-700 rounded capitalize">
    {item.creator_type.replace(/_/g, " ")}
  </span>
)}
```

The badge only renders for YouTube video articles whose `creator_type` is known (not "unknown").

- [ ] **Step 5: Verify TypeScript compiles**

```
cd frontend && npx tsc --noEmit
```

Expected: no type errors

- [ ] **Step 6: Visual check**

Start the dev server:
```
cd frontend && npm run dev
```

Go to Mention Explorer → filter by Source Type = "YT Videos". Look for rows that have a purple `reviewer` / `journalist` / `influencer` badge next to the source type. (Requires articles with `creator_type` populated in the DB — run the pipeline after deploying the backend changes.)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/mentions/MentionsList.tsx frontend/src/lib/types.ts
git add backend/app/dashboard/schemas.py backend/app/dashboard/router.py
git commit -m "feat: creator_type badge in Mention Explorer for YT video articles"
```

---

### Task 6: End-to-end smoke test

- [ ] **Step 1: Run all backend tests**

```
cd backend && python -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: all pre-existing tests pass; new tests for schemas, gemini, groq pass.

- [ ] **Step 2: Trigger a pipeline run and check creator_type in DB**

```sql
SELECT title, source_type, creator_type
FROM articles
WHERE source_type = 'youtube_video'
  AND creator_type IS NOT NULL
ORDER BY collected_at DESC
LIMIT 10;
```

Expected: rows with `creator_type` values like `reviewer`, `journalist`, `influencer`, `unknown`.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: agent E complete — YouTube creator type classification end-to-end"
```
