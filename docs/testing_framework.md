# Testing Framework

## Overview

Two-tier approach: unit tests (fast, CI-safe) and live evals (real APIs, staging-only).

```
backend/tests/
├── conftest.py                      # shared fixtures, app overrides
├── evals/
│   ├── __init__.py
│   ├── test_nlp_quality.py          # golden-dataset evals (NLP accuracy)
│   └── test_ai_summary.py           # AI summary schema + error handling
├── test_alerts_extended.py          # all 6 alert types + cooldown
├── test_circuit_breaker.py          # thread-safe circuit breaker
├── test_code_extractors.py          # classify_issue_category, star→sentiment
├── test_deduplication.py            # filter_new_articles, mark_article_seen
├── test_nlp_tier_selection.py       # NLP tier routing (Tier 0–3)
├── test_orchestrator.py             # pipeline orchestration
├── test_perception.py               # calculate_perception_score
├── test_rejection_store.py          # is_rejected, save_rejections
├── test_scheduler.py                # pipeline scheduling
├── test_syndication_dedup.py        # filter_syndicated
├── test_tenants.py                  # RBAC + tenant isolation
├── test_virality_detector.py        # virality flags + alert sub-checks
└── test_worker.py                   # queue worker
```

---

## Running Tests

```bash
# All unit tests (CI-safe — no real API calls)
cd backend
python -m pytest tests/ --ignore=tests/evals -q

# New tests only (fast feedback loop)
python -m pytest tests/test_code_extractors.py tests/test_circuit_breaker.py \
    tests/test_nlp_tier_selection.py tests/test_rejection_store.py \
    tests/test_syndication_dedup.py tests/test_alerts_extended.py -q

# Full suite including evals (staging only, needs API keys)
python -m pytest tests/ -m "not eval" -q                  # unit only
python -m pytest tests/evals/ --no-header -v               # live evals
```

---

## pytest.ini (key settings)

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

`asyncio_mode = auto` means all async test functions run without `@pytest.mark.asyncio`. Do not add that decorator.

---

## Fixtures (`conftest.py`)

| Fixture | Scope | Purpose |
|---|---|---|
| `override_settings` | `function` (autouse) | Resets `app.core.config.settings` to safe defaults before every test |
| `reset_dependency_overrides` | `function` (autouse) | Clears FastAPI `app.dependency_overrides` after every test |
| `test_client` | `function` | `TestClient(app)` with dependency overrides already applied |

---

## Mocking Patterns

### Supabase chain mock
```python
mock_db = MagicMock()
mock_db.table.return_value.select.return_value.eq.return_value \
    .execute.return_value.data = [{"content_hash": "abc"}]

with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
    result = filter_new_articles(articles, "brand-1")
```

**Critical:** `.get("key", default)` only returns `default` when the key is **absent**. If the key exists with `None`, `.get()` returns `None`. Use `or default` for nullable fields.

### Settings mock
```python
with patch("app.nlp.api_router.settings") as mock_s:
    mock_s.gemini_free_api_key = "key"
    mock_s.groq_api_key = ""
    tier = select_tier(article)
```

### Circuit breaker reset
```python
@pytest.fixture(autouse=True)
def reset_circuit():
    import app.nlp.circuit_breaker as cb
    cb._open_until = 0.0
    yield
    cb._open_until = 0.0
```

The circuit breaker is a **module-level singleton with a threading.Lock**. Its `_open_until` float must be reset between tests or state bleeds across test cases.

### LLM mock (pipeline-level)
```python
with patch("app.nlp.router._call_gemini", return_value=(mock_result, False)) as mock_g, \
     patch("app.nlp.router.detect_language", return_value=("en", 0.98)):
    result = analyse_article(article)
mock_g.assert_called_once()
```

---

## Module Coverage Map

| Module | Test file | Coverage notes |
|---|---|---|
| `app/ingestion/deduplication.py` | `test_deduplication.py` | `filter_new_articles`, `mark_article_seen`, edge cases |
| `app/ingestion/rejection_store.py` | `test_rejection_store.py` | `_extract_words`, `is_rejected`, `save_rejections` |
| `app/ingestion/deduplication.py` (syndication) | `test_syndication_dedup.py` | `filter_syndicated` |
| `app/nlp/code_extractors.py` | `test_code_extractors.py` | All pure functions; no mocks |
| `app/nlp/circuit_breaker.py` | `test_circuit_breaker.py` | Thread-safety tested |
| `app/nlp/api_router.py` (tier selection) | `test_nlp_tier_selection.py` | All 4 tiers across source types |
| `app/pipeline/perception.py` | `test_perception.py` | Score range, None handling, large batch |
| `app/storage/alerts.py` | `test_alerts_extended.py` | All 6 alert types, cooldown, disabled |
| `app/pipeline/orchestrator.py` | `test_orchestrator.py` | Pipeline flow (pre-existing) |
| `app/storage/virality.py` | `test_virality_detector.py` | Virality flags (pre-existing) |
| `app/tenants/` | `test_tenants.py` | RBAC isolation (pre-existing) |
| Dashboard API endpoints | (integration tests via TestClient) | In test_orchestrator.py |

---

## Adding New Tests

1. **File naming:** `tests/test_<module_name>.py`
2. **Class grouping:** One class per function under test (`class TestFilterSyndicated:`)
3. **No magic mocks:** Always reconstruct the full Supabase chain rather than patching at a high level — the chain is `table().select().eq().execute().data`
4. **Reset singletons:** If the module uses a module-level singleton (circuit breaker, settings), add an autouse fixture to reset it
5. **Eval tests:** Wrap live API tests in `@pytest.mark.eval` + `@pytest.mark.skip(reason="live eval")`. They run only when explicitly invoked.

---

## CI Integration

In Railway/GitHub Actions CI, the following environment variables must be present for the unit tests to pass (they're mocked, but settings import may fail without them):

```
SUPABASE_URL=http://localhost:54321  # any non-empty value
SUPABASE_SERVICE_KEY=test-key
JWT_SECRET=test-secret
```

Live evals additionally require `GEMINI_API_KEY` and/or `GROQ_API_KEY`.
