# Edge Cases Catalogue

Each row is a discovered edge case, the module it lives in, and how the test handles it.

---

## Deduplication (`app/ingestion/deduplication.py`)

| Edge case | Behaviour | Test |
|---|---|---|
| Empty article list | Returns early without any DB call | `test_filter_new_articles_skips_db_on_empty_list` |
| Article dict missing `content_hash` | Raises `KeyError` — caller's responsibility to provide the field | `test_filter_new_articles_missing_content_hash_raises` |
| Supabase connection timeout | Exception propagates — not silently swallowed | `test_filter_new_articles_db_error_propagates` |
| All articles already seen | Returns empty list | `test_all_seen_articles_returns_empty` |
| `mark_article_seen` upsert conflict | Uses `on_conflict` parameter so duplicate hash doesn't raise | `test_mark_article_seen_uses_on_conflict` |

---

## Sentiment → Perception Score (`app/pipeline/perception.py`)

| Edge case | Behaviour | Test |
|---|---|---|
| `sentiment_score = None` (key exists, value is null) | `.get()` returns `None` not `0.0`; fixed with `or 0.0` | `test_none_sentiment_score_defaults_to_zero` |
| `source_credibility = 0, reach_score = 0` | Weight computes to a very low value; handled by the `total_weight == 0` guard returning 50.0 | `test_zero_total_weight_returns_baseline` |
| Extreme sentiment scores (±1.0) with max credibility | Score stays within 0–100 | `test_score_always_bounded_between_0_and_100` |
| 1000-article batch | No crash, no ZeroDivisionError | `test_many_articles_does_not_crash` |
| Article missing `source_credibility` / `reach_score` | Falls back to defaults (`0.5`, `0`) | `test_missing_credibility_and_reach_default_gracefully` |

---

## Issue Category Classification (`app/nlp/code_extractors.py`)

| Edge case | Behaviour | Test |
|---|---|---|
| Empty string | Returns `("other", 0.25)` | `test_empty_string_returns_other` |
| No matching keywords | Returns `("other", 0.25)` | `test_no_keywords_returns_other_low_confidence` |
| Single keyword → 0.60 confidence | Minimum detection threshold | `test_single_keyword_match_gives_0_60` |
| Three keywords → 0.88 confidence | High-confidence detection | `test_three_keywords_gives_high_confidence_0_88` |
| Two-way tie between categories | Returns 0.45 (lowest confidence) | `test_tie_between_categories_returns_0_45` |
| Uppercase text | Function lowercases internally before matching | `test_uppercase_text_normalised` |
| Hyphenated multiword | "quarterly-results" does NOT match "quarterly results" | `test_hyphenated_multiword_keyword_not_matched` |
| Confidence always 0–1 | Tested across 4 extreme texts | `test_confidence_always_between_0_and_1` |

---

## Star Rating → Sentiment (`app/nlp/code_extractors.py`)

| Edge case | Behaviour | Test |
|---|---|---|
| `rating = None` | Returns `(0.0, "neutral")` | `test_none_returns_neutral` |
| `rating = 0` | Clamped to 1 → `(-0.90, "negative")` | `test_zero_clamped_to_1_star` |
| `rating = 6` (above max) | Clamped to 5 → `(0.90, "positive")` | `test_above_5_clamped_to_5_star` |
| `rating = -3` (negative) | Clamped to 1 → `(-0.90, "negative")` | `test_negative_number_clamped_to_1_star` |
| `rating = "4"` (string) | Parsed as float correctly | `test_rating_as_string_works` |
| `rating = "five"` (non-numeric) | Returns neutral gracefully | `test_non_numeric_string_returns_neutral` |
| `rating = 4.7` (float) | Rounds to 5 → positive | `test_float_rating_rounds_correctly` |

---

## Circuit Breaker (`app/nlp/circuit_breaker.py`)

| Edge case | Behaviour | Test |
|---|---|---|
| Initial state | Breaker is closed (`is_open() = False`) | `test_initially_closed` |
| After `trip()` | Breaker opens for 60s | `test_trip_opens_breaker` |
| Double `trip()` | Idempotent — cooldown does not reset | `test_double_trip_is_idempotent` |
| Auto-close after cooldown | `is_open()` returns False once `_open_until` has passed | `test_auto_closes_after_cooldown` |
| Concurrent `trip()` from multiple threads | No race condition; all threads see consistent state | `test_concurrent_trip_is_thread_safe` |

---

## NLP Tier Selection (`app/nlp/api_router.py`)

| Edge case | Behaviour | Test |
|---|---|---|
| `source_type = "google_review"` with star rating | Tier 0 — no LLM call | `test_star_rating_review_selects_tier0` |
| English news article, `gemini_free_api_key` set | Tier 2 (Gemini Free) | `test_english_news_selects_tier2` |
| English social (`reddit_post`) | Tier 1 (Groq) | `test_social_source_selects_tier1` |
| Indic language (`ta`, `hi`, `gu`, `bn`, `kn`) | Tier 3 (Gemini Paid) | `test_indic_languages_select_tier3` |
| No API keys configured | Tier 0 (code-only) | `test_no_api_keys_selects_tier0` |
| `source_type = "youtube_comment"` | Tier 1 (social) | `test_youtube_comment_selects_tier1` |

---

## Rejection Store (`app/ingestion/rejection_store.py`)

| Edge case | Behaviour | Test |
|---|---|---|
| Empty candidate title | `is_rejected()` returns False (no overlap possible) | `test_empty_candidate_not_rejected` |
| Stored `title_words = None` | Treated as empty set — not rejected | `test_none_stored_words_not_rejected` |
| URL-exact match | Always rejected regardless of title overlap | `test_url_match_always_rejected` |
| Title overlap at threshold | `>= 0.6` → rejected | (threshold test via `SIMILARITY_THRESHOLD`) |
| Stopword filtering | Stopwords stripped from extracted words | `test_extract_words_removes_stopwords` |
| Minimum word length | Words < 3 characters excluded | `test_extract_words_min_3_chars` |

---

## Syndication Deduplication (`app/ingestion/deduplication.py` — `filter_syndicated`)

| Edge case | Behaviour | Test |
|---|---|---|
| Empty input | Returns empty list without DB calls | `test_filter_syndicated_empty_input` |
| Article with no `story_hash` | Passes through — not considered syndicated | `test_no_story_hash_passes_through` |
| Within-batch duplicate (same `story_hash`) | Second occurrence filtered | `test_within_batch_dedup_filters_duplicate` |
| DB `id = None` | Skip DB update — no crash | `test_null_id_skips_db_update` |
| DB `syndication_count = None` | Treated as 1 → incremented to 2 | `test_null_syndication_count_treated_as_1` |

---

## Alert System (`app/storage/alerts.py`)

| Edge case | Behaviour | Test |
|---|---|---|
| No `RESEND_API_KEY` | Returns immediately, no DB fetch | `test_returns_immediately_when_no_resend_key` |
| Alert within 4h cooldown | Suppressed — email not sent | `test_alert_suppressed_within_4h_cooldown` |
| Alert after 5h | Fires — email sent | `test_alert_fires_after_4h_cooldown` |
| `enabled = False` | Skipped entirely | `test_disabled_config_does_not_fire` |
| Malformed `last_triggered_at` | Raises `ValueError` — not silently ignored | `test_malformed_last_triggered_date_raises` |
| DB load failure (e.g., connection down) | Graceful — no email, no crash | `test_config_load_failure_is_graceful` |
| Syndication sub-check returns `None` | Alert not fired | `test_syndication_spike_does_not_fire_when_sub_check_none` |
