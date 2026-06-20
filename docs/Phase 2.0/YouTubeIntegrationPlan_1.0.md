# YouTube Integration Plan — MediaSense Phase 2.0
**Version:** 1.0  
**Date:** 2026-06-17  
**Status:** Pre-implementation (approved for development)  
**Scope:** YouTube Data API v3 — videos, comments, channel uploads; flowing into the existing NLP + sentiment pipeline  

---

## 1. Why YouTube First

YouTube is the most brand-relevant social platform for the Indian market that can be accessed without platform approval or a credit card:

| Signal | Why It Matters for Brand Monitoring |
|--------|-------------------------------------|
| Video titles / descriptions | Direct brand mentions from journalists, reviewers, creators |
| Comments | Public opinion at scale — often thousands of data points per video |
| Channel uploads | Brand's own channel — track how their narrative performs |
| Reach (view/like counts) | Weight sentiment by actual audience exposure, not just raw mention count |
| Language | YouTube India is heavily Hinglish, Tamil, Hindi — matches our existing NLP stack |

**Competitive gap closed:** News-only monitoring misses 60–70% of brand mentions. Adding YouTube (comments on brand-related videos) bridges this gap without requiring any paid API agreements.

**Free quota:** YouTube Data API v3 gives 10,000 units/day at zero cost — enough to monitor 12 brands comfortably.

---

## 2. What YouTube Content We Will Collect

### 2a. Content Types

| Type | What | Example | Sentiment Signal |
|------|------|---------|-----------------|
| **Search results** | Videos mentioning the brand keyword in title or description | "Reliance Jio new plan review 2025" | Strong — reviewer opinion in title/body |
| **Video comments** | Top 20 comments on each matched video | "Jio has been terrible lately 😤" | Strongest public sentiment signal |
| **Channel uploads** | Videos from the brand's own official YouTube channel | CIPET's official channel upload | Tracks brand's own content performance |

### 2b. What We Will NOT Collect (Phase 2.0)
- Live streams (transient, no persistent comment thread)
- Subscriber counts or channel analytics (requires OAuth, not just API key)
- Playlists
- YouTube Shorts (different engagement pattern — Phase 2.1)
- Community posts (different API endpoint — Phase 2.2)

---

## 3. YouTube Data API v3 — Quota Deep Dive

### 3a. Unit Cost Per Operation

| API Method | Units per call | Returns |
|------------|---------------|---------|
| `search.list` | **100 units** | Up to 50 video results |
| `videos.list` | **1 unit** | Full metadata for 1 video |
| `commentThreads.list` | **1 unit** | Up to 100 comments |
| `channels.list` | **1 unit** | Channel metadata |
| YouTube RSS feed | **0 units** | Up to 15 latest uploads for a channel |

### 3b. Daily Quota Budget (10,000 units/day, 12 brands)

| Operation | Calls/day | Units/call | Total units | Yield |
|-----------|-----------|------------|-------------|-------|
| Keyword search (1 per brand) | 12 | 100 | 1,200 | 10 videos × 12 brands = 120 videos |
| Video metadata enrichment | 120 | 1 | 120 | View counts, duration, publish date |
| Comment threads (top 10 videos per brand) | 120 | 1 | 120 | 100 comments each = 12,000 comments |
| Channel RSS (free) | unlimited | 0 | 0 | 15 uploads/channel per run |
| **Total** | | | **~1,440 units** | **Leaves 8,560 units buffer** |

**Key insight:** Using the **hybrid approach** (API for search + comments, RSS for channel uploads) consumes only ~14% of daily quota. This leaves enormous headroom to expand to 50+ brands or add a second daily collection cycle.

### 3c. Quota Safety Rules
- **Hard cap per brand:** 200 units/day (circuit breaker resets at midnight UTC)
- **Search frequency:** 1 cycle per day (aligns with existing hourly scheduler — trigger once per 24h for YouTube)
- **Comment sampling:** Top 10 matched videos only (not all 50 search results)
- **Backoff:** If `quotaExceeded` (HTTP 403 code 429) → stop immediately, log, skip remaining brands; retry next UTC day

---

## 4. How YouTube Content Flows Into the Existing Pipeline

### 4a. Architecture: New Collector, Same Pipeline

The design principle is **minimal surgery to the existing pipeline**. YouTube articles enter the same `articles` table, pass through the same NLP router, and appear in the same dashboard components. Only the collection step is new.

```
Existing flow:
  scheduler.py → orchestrator.py → rss_collector.py → NLP → save_article()

New flow (Phase 2.0):
  scheduler.py → orchestrator.py → rss_collector.py  ─┐
                                 → youtube_collector.py ┘→ NLP → save_article()
```

The orchestrator calls both collectors, merges results into `all_articles`, and the rest of the pipeline is unchanged.

### 4b. Data Shape Comparison

| Field | News article | YouTube video | YouTube comment |
|-------|-------------|--------------|----------------|
| `content_hash` | sha256(portal_id::url) | sha256("youtube_video::video_id") | sha256("youtube_comment::comment_id") |
| `portal_id` | "the_hindu" | "youtube_search" | "youtube_comment" |
| `portal_name` | "The Hindu" | "YouTube" | "YouTube Comments" |
| `url` | article URL | `https://youtube.com/watch?v=VIDEO_ID` | `https://youtube.com/watch?v=VIDEO_ID&lc=COMMENT_ID` |
| `title` | article headline | video title | first 120 chars of comment |
| `body` | article body | video description | full comment text |
| `author` | journalist name | channel name | commenter handle |
| `published_at` | article publish date | video publish date | comment publish date |
| `language` | detected by langdetect | detected by langdetect | detected by langdetect |
| `source_credibility` | portal credibility (0–1) | channel tier score (0–1) | fixed 0.5 (public comment) |
| `source_type` *(new)* | "news" | "youtube_video" | "youtube_comment" |
| `external_id` *(new)* | null | YouTube video_id | YouTube comment_id |
| `reach_score` | 0 (existing default) | view_count (normalized) | like_count on comment |

### 4c. New Schema Columns (Migration 012)

```sql
-- Migration 012_youtube_source_type.sql
ALTER TABLE articles ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'news'
    CHECK (source_type IN ('news', 'youtube_video', 'youtube_comment'));
ALTER TABLE articles ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS reach_metadata JSONB DEFAULT '{}';

CREATE INDEX idx_articles_source_type ON articles(brand_id, source_type);
CREATE INDEX idx_articles_external_id ON articles(external_id) WHERE external_id IS NOT NULL;
```

`reach_metadata` stores the raw YouTube numbers for display:
```json
{
  "view_count": 1500000,
  "like_count": 42300,
  "comment_count": 8700,
  "channel_subscriber_count": 250000,
  "video_duration_seconds": 843
}
```

---

## 5. YouTube Collector Module Design

### 5a. New File: `backend/app/ingestion/youtube_collector.py`

**Three functions, one config:**

```python
def get_channel_rss_videos(channel_id: str, brand_id: str) -> list[dict]:
    """
    Free: YouTube channel RSS feed (no API quota).
    Returns up to 15 latest uploads from a channel.
    URL pattern: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
    Parsed using the same feedparser already in rss_collector.py.
    """

def search_brand_videos(keywords: list[str], language: str,
                        brand_id: str, max_results: int = 10) -> list[dict]:
    """
    100 units per call. Searches YouTube for videos matching brand keywords.
    Returns video metadata: id, title, description, channel, published_at, thumbnails.
    Sets source_type = 'youtube_video'.
    """

def get_video_comments(video_id: str, brand_id: str,
                       max_comments: int = 20) -> list[dict]:
    """
    1 unit per call. Fetches top comments for a video (sorted by relevance).
    Each comment becomes a separate article with source_type = 'youtube_comment'.
    Only called for videos that passed keyword match.
    """
```

### 5b. Keyword Matching Strategy for YouTube

YouTube search already filters by keywords (it's the search query). But for comments, we need to decide: collect ALL comments, or only comments that mention brand keywords?

**Decision: Collect ALL top comments from matched videos.**

Rationale: If a video is about the brand (video title matched), then comments are inherently about brand context even if individual comments don't name the brand. Filtering comments would discard valuable opinions ("This is great!" on a Jio review video = positive Jio sentiment).

For channel upload RSS, we apply keyword matching to the video title and description (same as RSS collector today).

### 5c. Channel Credibility Scoring

Unlike verified news portals with known credibility scores, YouTube channels vary wildly. Use a tiered heuristic:

| Channel tier | Criteria | `source_credibility` |
|-------------|---------|----------------------|
| Verified brand channel | `is_verified=True` from API | 0.90 |
| Large creator (>1M subs) | subscriber_count > 1,000,000 | 0.75 |
| Mid creator (100K–1M subs) | subscriber_count > 100,000 | 0.65 |
| Small creator (<100K subs) | default | 0.50 |
| Comment (any source) | fixed — public opinion, unverified | 0.45 |

This feeds directly into the existing `perception_score` calculation (which already weights by `source_credibility`).

---

## 6. NLP Adaptation for Short-Form Social Text

### 6a. The Problem

Current NLP prompts are tuned for news prose:
- Long sentences with clear subject-verb-object structure
- Formal language (journalist writes "Reliance posted a ₹15,000 crore quarterly profit")
- No emoji, minimal slang

YouTube content is different:
- Comments: "jio is the WORST 😤😤😤 i want my money back"
- Video titles: "Reliance JIO SCAM?? Must Watch Before You Buy!!"
- Mixed scripts: "Jio ka plan bahut bekar hai bhai 😂" (Hinglish)

### 6b. Changes to NLP Prompts

Add a `source_type` parameter to `analyse_article()` and pass it to the LLM prompt:

**Modified prompt structure (Gemini/Groq):**

```
You are analyzing [social media content / news article] for brand sentiment.

Source type: {source_type}  ← NEW
Language: {language}

{source_type-specific instruction}:
- If 'youtube_comment': This is a short social media comment. Emojis carry strong sentiment 
  signals. Slang is valid. Mixed languages (Hinglish, Tanglish) are intentional. 
  Focus on the emotional tone.
- If 'youtube_video': This is a video title and description. The title often uses 
  clickbait phrasing — weigh the description more than the title for true sentiment.
- If 'news': Standard news article. Use journalistic framing to assess sentiment.

Text to analyze:
{text}
```

### 6c. Short-Text Handling

YouTube comments can be very short (< 10 words). The LLM still runs, but we set a `min_confidence_threshold`:
- Comments < 5 words with confidence < 0.5 → label as `neutral` (avoid noise)
- Very short positive/negative emojis only → still process (emoji carries clear signal)

### 6d. Language Detection for Code-Switched Text

Hinglish ("jio ka plan bahut bekar hai") will be detected as `hi` by langdetect. This is correct — route it through the Hindi NLP path. The existing `skip_keyword_filter=True` pattern handles this.

**New edge case:** English script but Hindi/Tamil words (transliterated). langdetect will detect this as `en` but the content is code-switched. The existing LLM prompt already handles code-switching gracefully — no special handling needed.

---

## 7. Orchestrator Integration

### 7a. Modified `run_brand_pipeline()` in `orchestrator.py`

```python
# After existing portal collection:
portals = get_gnews_portals(keywords, languages) + get_portals_for_languages(languages)
for portal in portals:
    articles = collect_portal(portal, keywords, brand_id)
    all_articles.extend(articles)

# NEW: YouTube collection (only if brand config has youtube_enabled=True)
if config.get("youtube_enabled", False):
    youtube_articles = collect_youtube(brand, config)  # new function
    all_articles.extend(youtube_articles)
```

### 7b. New `collect_youtube()` helper

```python
def collect_youtube(brand: dict, config: dict) -> list[dict]:
    """
    Orchestrates all YouTube collection for one brand.
    Respects quota budget. Returns articles in same format as news collector.
    """
    results = []
    keywords = config.get("keywords", [])
    channel_ids = config.get("youtube_channel_ids", [])  # brand's own channels

    # 1. Free: channel RSS for brand's own channels
    for channel_id in channel_ids:
        results.extend(get_channel_rss_videos(channel_id, brand["id"]))

    # 2. Paid quota: search for brand mentions across all of YouTube
    videos = search_brand_videos(keywords, "en", brand["id"], max_results=10)
    results.extend(videos)

    # 3. Comments on top matched videos (1 unit each)
    for video in videos[:10]:
        comments = get_video_comments(video["external_id"], brand["id"], max_comments=20)
        results.extend(comments)

    return results
```

### 7c. Per-language Cap for YouTube

The existing cap of **20 articles per language** per run will be shared between news and YouTube. To avoid YouTube drowning out news (which has higher credibility weights), a **separate sub-cap** will apply:

| Content type | Cap per pipeline run |
|-------------|---------------------|
| News articles (existing) | 20 per language |
| YouTube videos | 10 per brand per run |
| YouTube comments | 50 per brand per run (comments are short, cheap NLP) |

### 7d. `brand_configs` Schema Extension

Add two new fields to `brand_configs` table:

```sql
-- In migration 012:
ALTER TABLE brand_configs ADD COLUMN IF NOT EXISTS youtube_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE brand_configs ADD COLUMN IF NOT EXISTS youtube_channel_ids TEXT[] DEFAULT '{}';
```

`youtube_enabled = FALSE` by default — opt-in per brand. Enable via Brand Setup Wizard (Phase 2.0 UI step).

---

## 8. Quota Management Module

### 8a. New File: `backend/app/ingestion/youtube_quota.py`

YouTube API quota resets daily at midnight Pacific Time (UTC-7/UTC-8). We track units consumed per day using an in-memory counter (sufficient for a single-instance Railway deployment).

```python
class YouTubeQuotaManager:
    daily_limit: int = 10_000
    safety_margin: int = 500       # never use last 500 units
    search_cost: int = 100
    other_cost: int = 1

    def can_search(self) -> bool: ...
    def record_search(self): ...
    def can_fetch(self) -> bool: ...
    def record_fetch(self): ...
    def reset_if_new_day(self): ...   # called at start of each pipeline run
```

**Error handling:** If YouTube returns `HTTP 403 + reason: quotaExceeded`, immediately:
1. Open a circuit breaker (same pattern as NLP circuit breaker)
2. Skip all remaining YouTube collection for this run
3. Log: "YouTube quota exhausted — skipping remaining brands until UTC midnight"
4. The existing DLQ does NOT apply here (quota errors are transient, not content errors)

---

## 9. Frontend Changes

### 9a. Source Breakdown — YouTube Row

`SourceBreakdown.tsx` already renders a table of portal names with sentiment bars. YouTube will appear automatically once articles have `portal_id = "youtube_search"` or `"youtube_comment"`. No code change needed for basic display.

**Enhancement:** Add YouTube icon (SVG) next to portal name for `portal_id` values starting with `youtube_`. One-line conditional in the source table cell.

### 9b. Mentions List — Source Type Filter

`MentionsList.tsx` currently has a language filter dropdown. Add a second filter: **Source Type**:

```
[All Sources ▾]   [All Languages ▾]
  → News
  → YouTube Videos
  → YouTube Comments
```

Map to `source_type` column in the backend `/dashboard/mentions/{brand_id}` endpoint (already accepts filter params — just add `source_type` as a new query param).

### 9c. Article Card — YouTube Context

When displaying a YouTube article in `MentionsList`, show:
- YouTube icon badge (red ▶)
- For videos: view count ("1.2M views")
- For comments: like count on the comment
- Clickable URL opens YouTube directly

These values come from `reach_metadata` JSONB column.

### 9d. KPI Panel — New Metric

Add a **"YouTube Mentions"** count to the KPI summary panel (alongside existing Articles Collected, Positive %, Negative %). This is a simple count of `source_type IN ('youtube_video', 'youtube_comment')` filtered by date range.

---

## 10. Step-by-Step Implementation Guide

### Phase 2.0-A: Foundation (Days 1–2)

**Day 1 — API Setup & Schema**

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → your project
2. APIs & Services → Enable **YouTube Data API v3**
3. Credentials → Create API Key → restrict to YouTube Data API v3 only
4. Add to Railway: `YOUTUBE_API_KEY=AIzaSy...`
5. Add to local `.env`: `YOUTUBE_API_KEY=AIzaSy...`
6. Add `youtube_api_key: str = ""` to `backend/app/config.py`
7. Write and run `supabase/migrations/012_youtube_source_type.sql` (see §4c above)
8. Run migration in Supabase SQL Editor

**Day 2 — YouTube Collector Module**

1. Install: `pip install google-api-python-client` → add to `backend/requirements.txt`
2. Create `backend/app/ingestion/youtube_collector.py` with three functions (§5a)
3. Create `backend/app/ingestion/youtube_quota.py` (§8a)
4. Manual test in Python REPL: `search_brand_videos(["Reliance Jio"], "en", "test-brand-id")`
5. Verify quota usage: check Google Cloud Console → YouTube Data API → Quotas

### Phase 2.0-B: Pipeline Integration (Days 3–4)

**Day 3 — Orchestrator Wiring**

1. Add `collect_youtube()` helper to `orchestrator.py` (§7b)
2. Add YouTube collection call to `run_brand_pipeline()` inside the `try` block (§7a)
3. Modify `analyse_article()` signature to accept `source_type` parameter (§6b)
4. Update Gemini prompt in `gemini_handler.py` to include source-type instruction
5. Update Groq prompt in `groq_handler.py` similarly
6. Test by enabling `youtube_enabled=True` for one brand (via Supabase SQL)

**Day 4 — NLP Tuning & Dedup**

1. Add `source_type` field to `NLPResult` dataclass in `schemas.py` (pass-through only)
2. Verify deduplication works: `content_hash = sha256("youtube_video::" + video_id)` — unique per brand per video
3. Test with a brand that has high YouTube presence (e.g., Reliance Jio)
4. Trigger manual pipeline run: `POST /pipeline/trigger` (master_admin JWT)
5. Query `SELECT source_type, count(*) FROM articles GROUP BY source_type` to verify

### Phase 2.0-C: Frontend Display (Days 5–6)

**Day 5 — Backend API Changes**

1. Add `source_type` filter param to `GET /dashboard/mentions/{brand_id}` in `router.py`
2. Add `reach_metadata` to the article response schema
3. Update `get_kpi_summary()` in `schemas.py` to include YouTube mention count
4. Deploy backend to Railway (auto-deploys via GitHub push)

**Day 6 — Frontend Changes**

1. Add `source_type` filter dropdown to `MentionsList.tsx` (next to language dropdown)
2. Add YouTube icon + view count display in article card (conditional on `source_type`)
3. Add YouTube icon in `SourceBreakdown.tsx` for YouTube portal rows
4. Add "YouTube Mentions" KPI card in `Overview.tsx`
5. Deploy to Vercel (auto-deploys via GitHub push)

### Phase 2.0-D: Brand Config UI (Day 7)

1. Add YouTube toggle to Brand Setup Wizard (`BrandSetup.tsx`)
   - Checkbox: "Monitor YouTube" 
   - Conditional field: "YouTube Channel ID (optional)" — brand can enter their official channel ID
2. Wire to `POST /tenants/brands` and `PATCH /tenants/brands/{brand_id}` endpoints
3. Add `youtube_enabled` and `youtube_channel_ids` to `brand_configs` DB schema (already in migration 012)

---

## 11. Data Flow Diagram (End-to-End)

```
YouTube Data API v3
        │
        ├─► search.list(brand keywords)
        │         │
        │         └─► 10 matched videos (100 units per search)
        │                   │
        │                   ├─► videos.list(video_ids) → view_count, etc. (1 unit each)
        │                   │
        │                   └─► commentThreads.list(video_id) → top 20 comments (1 unit each)
        │
        └─► [FREE] YouTube RSS feed (channel uploads)
                  Parsed by feedparser (already a dependency)

All collected items → same article dict shape as news

orchestrator.py: all_articles = news_articles + youtube_articles
        │
        ├─► filter_new_articles() — dedup by content_hash (sha256 includes "youtube_video::" prefix)
        │
        ├─► NLP router → analyse_article(article, source_type)
        │         │
        │         ├─► Gemini (social-aware prompt)
        │         └─► Groq (fallback, social-aware prompt)
        │
        ├─► save_article() → articles table (new columns: source_type, external_id, reach_metadata)
        │
        ├─► calculate_perception_score() — unchanged; source_credibility weights YouTube lower
        │
        └─► write_sentiment_point() + check_and_fire_alerts() — unchanged

Dashboard:
  MentionsList → [source_type filter] → shows news + YouTube in unified feed
  SourceBreakdown → youtube_search / youtube_comment rows appear automatically
  KPI panel → "YouTube Mentions" count (new)
```

---

## 12. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| YouTube API quota exhausted unexpectedly | Medium | Blocks all YouTube collection that day | Hard circuit breaker at 9,500 units; skip remaining brands gracefully |
| Comments are spam / irrelevant | High | Noise in sentiment data | Source credibility 0.45 for comments reduces their weight in perception score |
| Hinglish comments misclassified | Medium | Wrong sentiment label | LLM handles code-switching; manual review for first 2 weeks |
| Video description is just hashtags | Low | Empty NLP input | Min body length check: if `len(body) < 20`, skip NLP, set neutral |
| YouTube changes RSS feed format | Low | Channel monitoring breaks | Feedparser handles most variants; fallback to API if RSS fails |
| Brand has no YouTube presence | Common | Zero YouTube articles collected | Expected behavior — just no YouTube rows; no error |
| API key leaked via Railway logs | Low | Quota abuse | Key restricted to YouTube Data API only in GCP; rotate if detected |

---

## 13. Testing Checklist

### 13a. Unit Tests
- [ ] `search_brand_videos()` returns correctly shaped dicts
- [ ] `get_video_comments()` returns correct content_hash using "youtube_comment::" prefix
- [ ] `get_channel_rss_videos()` parses YouTube RSS format correctly
- [ ] `YouTubeQuotaManager.can_search()` returns False when units exhausted
- [ ] Duplicate video across two pipeline runs is deduped (same content_hash)

### 13b. Integration Tests
- [ ] Run pipeline for one brand with `youtube_enabled=True` → articles appear in DB with `source_type='youtube_video'`
- [ ] Comments appear with `source_type='youtube_comment'`
- [ ] NLP runs on a short comment ("great product!") → returns valid `NLPResult`
- [ ] `GET /dashboard/mentions/{brand_id}?source_type=youtube_comment` returns only comments
- [ ] `GET /dashboard/kpi/{brand_id}` includes `youtube_mention_count` field

### 13c. Quota Safety
- [ ] Simulated quota exhaustion (mock API returning 403) → circuit breaker opens, remaining brands skipped, no Python exception propagated
- [ ] Next pipeline run after cooldown → circuit breaker closed, collection resumes

---

## 14. Open Questions (Resolved Before Implementation)

| Question | Decision |
|----------|----------|
| Should we collect Shorts? | No — Phase 2.1. Different engagement pattern. |
| Collect comments from ALL 50 search results or just top 10? | Top 10 only. Cost control. |
| What's the `source_credibility` for a comment from an unverified small account? | 0.45 (below news floor of 0.65) |
| Should YouTube mentions appear in alerts (perception_score_below, negative_pct_above)? | Yes — same alert system, same thresholds. |
| Two search cycles per day (morning + evening) or one? | Start with one per day. Revisit when brands > 30. |
| Should we store YouTube thumbnails? | No — only URLs in `reach_metadata`. No binary storage. |

---

## 15. Dependencies & Prerequisites

| Requirement | Status | Notes |
|------------|--------|-------|
| Google Cloud Project | ✅ Exists | Used for Google News API already |
| YouTube Data API v3 enabled | ⬜ Pending | Enable in Cloud Console |
| `YOUTUBE_API_KEY` in Railway | ⬜ Pending | Create after enabling API |
| `google-api-python-client` pip package | ⬜ Pending | Add to requirements.txt |
| Migration 012 applied | ⬜ Pending | Run in Supabase SQL Editor |
| `youtube_enabled` flag per brand | ⬜ Pending | Default FALSE; opt-in |

---

## 16. Success Criteria

Phase 2.0 YouTube integration is complete when:

1. At least one brand has `youtube_enabled=TRUE` and YouTube articles appear in the `articles` table after a pipeline run
2. YouTube videos and comments display in the Mentions Explorer alongside news articles
3. The Source Breakdown shows YouTube as a distinct source with its own sentiment bars
4. The `source_type` filter in Mentions Explorer filters correctly
5. Quota consumption stays below 3,000 units/day for 12 brands
6. No new pipeline errors caused by YouTube collection (YouTube errors are isolated and non-fatal)
7. Alerts fire correctly when YouTube-inclusive sentiment drops below threshold

---

## 17. What Comes After YouTube (Phase 2.1+)

| Platform | API Access | Complexity | Planned Phase |
|----------|-----------|------------|---------------|
| Reddit | Free (Reddit API, 100 req/min) | Low — simple JSON API | 2.1 |
| Twitter/X | Paid ($100/month Basic tier minimum) | High — approval + cost | 3.0 |
| Instagram | Meta Graph API (approved business account required) | High — OAuth + approval | 3.0 |
| LinkedIn | Partner API (enterprise only) | Very high | 4.0 |

YouTube → Reddit forms the Phase 2 cluster. Both are free, API-based, and require no platform approval. Together they cover: video opinions (YouTube), long-form discussion (Reddit) — the two most research-trusted social signal types for brand monitoring.

---

*Document maintained by: MediaSense core team*  
*Next review: After Phase 2.0-A implementation (Day 2 checkpoint)*
