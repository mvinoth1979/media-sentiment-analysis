# Eval Framework

Evals measure whether the NLP pipeline produces *correct* outputs, not just whether the code runs. They complement unit tests which only check structural behaviour.

---

## Two Tiers

| Tier | Marker | When to run | Cost |
|---|---|---|---|
| **Unit evals** | none (runs in CI) | Every push | Zero (mocked LLM) |
| **Live evals** | `@pytest.mark.eval` + `@pytest.mark.skip` | Manually in staging | Real API tokens |

---

## Files

### `tests/evals/test_nlp_quality.py`
Golden dataset tests for the core NLP functions.

**Golden datasets defined:**

| Name | Size | Purpose |
|---|---|---|
| `GOLDEN_SENTIMENT` | 5 items | Positive/negative/neutral English articles |
| `GOLDEN_ISSUE_CATEGORY` | 7 items | Issue category classification accuracy |
| `GOLDEN_STAR_SENTIMENT` | 10 items | Star rating → sentiment score mapping |

**Test classes:**

| Class | What it tests |
|---|---|
| `TestIssueClassificationAccuracy` | `classify_issue_category` against golden set — deterministic, no LLM |
| `TestStarSentimentMapping` | `sentiment_from_star_rating` across full 1–5 scale + edge cases |
| `TestNLPPipelineContract` | `analyse_article` with mocked LLM; verifies circuit breaker, Indic routing, star bypass |
| `TestNLPResultSchema` | `NLPResult` Pydantic schema: field bounds, label validation |
| `TestLiveNLPAccuracy` | `@pytest.mark.skip` — real Gemini/Groq calls, ≥80% accuracy required |

### `tests/evals/test_ai_summary.py`
AI Executive Summary endpoint tests.

**Test classes:**

| Class | What it tests |
|---|---|
| `TestAISummarySchema` | 4 required fields, `actions` is list, `generated_at` is ISO timestamp |
| `TestAISummaryErrorHandling` | No articles → graceful empty response; all providers fail → 503; settings import works |
| `TestLiveAISummaryAccuracy` | `@pytest.mark.skip` — real LLM call, validates non-empty output |

---

## Golden Dataset Design Principles

1. **Human-verified** — each expected output has been manually confirmed correct
2. **Domain-representative** — covers Indian media contexts (SEBI, GST, FSSAI, regional brands)
3. **Edge-case coverage** — at least one item per sentiment polarity, at least one ambiguous case
4. **Category names match code** — category strings must exactly match `_ISSUE_KWORDS` keys in `code_extractors.py`

### Current category names (as of 2026-06)
```
financial_performance, regulatory_compliance, product_quality,
leadership_governance, crisis_controversy, awards_recognition,
csr_sustainability, policy_government, competitive_landscape,
customer_experience, brand_advocacy, market_opportunity
```

**Do not use:** `regulatory_legal`, `crisis_management`, `product_recall` — these were old names that no longer exist in the keyword dict.

---

## Running Live Evals

```bash
# Requires GEMINI_API_KEY (and optionally GROQ_API_KEY) in environment
cd backend
python -m pytest tests/evals/ -m eval --no-header -v --no-skip

# Run a single eval class
python -m pytest tests/evals/test_nlp_quality.py::TestLiveNLPAccuracy -v --no-skip
```

---

## Accuracy Thresholds

| Metric | Minimum | How measured |
|---|---|---|
| Sentiment polarity (positive/negative/neutral) | ≥ 80% on `GOLDEN_SENTIMENT` | `test_golden_sentiment_accuracy_above_80_percent` |
| Issue category classification | ≥ 70% on `GOLDEN_ISSUE_CATEGORY` | `test_issue_category_golden_set` (parametrized) |
| Star rating mapping | 100% (deterministic) | `test_star_rating_golden_set` |
| AI summary schema | 100% (structural) | `TestAISummarySchema` |

---

## Adding Eval Cases

1. Add a tuple to the appropriate `GOLDEN_*` list in `test_nlp_quality.py`
2. Tuple format: `(text, expected_label_or_category, min_confidence_or_flag)`
3. Run the test locally first to verify the expected value is actually what the function returns
4. For live evals, add a method to `TestLiveNLPAccuracy` with the `@pytest.mark.eval` decorator

**Do not** add items to the golden set without verifying them first — a wrong expected value creates a false failure that's hard to diagnose later.

---

## NLP Pipeline Contract (mocked, CI-safe)

These are structural guarantees, tested without real API calls:

| Contract | Test method |
|---|---|
| Circuit breaker open → `analyse_article` returns `None` | `test_circuit_breaker_open_returns_none` |
| Article < 8 words → `analyse_article` returns `None` | `test_short_article_below_8_words_returns_none` |
| `google_review` with star rating → no LLM call (Tier 0) | `test_star_rating_google_review_bypasses_llm` |
| Indic language (`ta`) → `_call_gemini` called with `paid=True` | `test_indic_language_routes_to_gemini_paid` |

---

## Known Limitations

- **No Tamil/Hindi golden set for live evals yet** — only English golden items. Add Indic-language items when sufficient pipeline throughput is available.
- **Star rating bypass** applies only to `google_review`, `trustpilot_review`, and similar review source types with `reach_metadata.star_rating`. Forum posts with star ratings are not yet handled.
- **`classify_issue_category` confidence** tops out at 0.88 regardless of how many keywords match — this is by design (cap prevents overconfidence on keyword-heavy articles).
