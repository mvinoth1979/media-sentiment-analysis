# MediaSense — Roadmap Items 3–10 Design Spec

> **Date:** 2026-06-21
> **Status:** Approved — ready for implementation
> **Predecessor work:** Items 1 (structured issue taxonomy) and 2 (YouTube creator/audience sentiment split) are already shipped.
> **Implementation strategy:** 5 parallel worktree agents, pre-assigned migration numbers to avoid collisions.

---

## 0. Tech Stack Reference

Backend: FastAPI · Supabase (PostgreSQL via supabase-py) · Redis (Upstash) · APScheduler · Gemini (primary NLP) + Groq (fallback)
Frontend: React 19 · TypeScript · Tailwind CSS 4 · Recharts · TanStack Query · Axios
Deployment: Railway (backend) · Vercel (frontend) · Supabase (DB/auth)

All items must follow existing patterns: Supabase client via `get_db()`, auth via `require_brand_role(*READ_ROLES)`, migrations as numbered SQL files in `backend/migrations/`.

---

## 1. Agent Grouping & File Ownership

Each agent operates in an isolated git worktree. Pre-assigned migration numbers prevent collisions.

| Agent | Items | Owned files | Migration |
|---|---|---|---|
| A | 3 + 7 | `alerts.py`, new `virality_detector.py` | 017 |
| B | 5 + 8 | `dashboard/router.py`, `dashboard/schemas.py`, new `ReviewQueue.tsx` | 018 |
| C | 4 + 10 | `portals.py`, frontend `TopHeadlines.tsx`, `CompetitorShareOfVoice.tsx` | none |
| D | 6 | new `google_reviews_collector.py`, `tenants/router.py`, `orchestrator.py` (additive block) | 019 |
| E | 9 | `nlp/schemas.py`, `gemini_handler.py`, `groq_handler.py`, `storage/postgres.py`, frontend YT badges | 020 |

**Post-merge note:** Only Agent D touches `orchestrator.py` (adds a Google reviews block alongside the Reddit block — purely additive, no lines deleted). No other agent modifies it, so no merge conflict expected.

---

## 2. Item 3 — Rolling Baseline Virality (Agent A)

### Goal
Detect when a YouTube video is going viral and fire a structured alert before the PR team hears about it from someone else.

### Data model
New table `video_metrics_history` (migration 017):
```sql
CREATE TABLE video_metrics_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    brand_id UUID NOT NULL,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    view_count BIGINT DEFAULT 0,
    comment_count INT DEFAULT 0,
    negative_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (article_id, snapshot_date)
);
```

### Logic — `backend/app/pipeline/virality_detector.py` (new file)
```
detect_virality(brand_id) -> list[Viral­Alert]:
  1. Fetch all youtube_video articles for brand from last 30 days (from articles table)
  2. For each video, query video_metrics_history for last 7 days
  3. Compute 7-day rolling avg for: view_count, comment_count, negative_count
  4. Snapshot today's values from article reach_metadata
  5. Compare today vs avg:
     - view_count > 3× avg → metric_triggered["views"] = True
     - comment_count > 3× avg → metric_triggered["comments"] = True
     - negative_count > 3× avg → metric_triggered["negative"] = True
  6. Count triggered metrics → flag level:
     - 1 triggered → "emerging_issue"
     - 2 triggered → "reputation_risk"
     - 3 triggered → "crisis_alert"
  7. Upsert today's snapshot into video_metrics_history
  8. Return list of videos that triggered any flag
```

### Alert integration — `alerts.py`
Add `virality_spike` to `_ALERT_META`. In `check_and_fire_alerts`, add a call to `_check_virality(brand_id, threshold)` where threshold is an integer (minimum flag level: 1=emerging, 2=risk, 3=crisis).

New `_check_virality` function in `alerts.py`:
- Imports and calls `detect_virality(brand_id)` from `virality_detector.py` — this both snapshots today's metrics AND returns violating videos.
- Filters returned videos by threshold (flag_level ≥ threshold).
- Returns `(flag_level_float, video_title)` for the highest-flagged video, else `None`.
- Naturally a no-op if the brand has no `youtube_video` articles (YouTube disabled).

**No orchestrator touch needed.** `check_and_fire_alerts` is already called at the end of every pipeline run; adding `virality_spike` to its alert-type switch is sufficient. Snapshot + analysis happen inside `_check_virality` in one pass.

---

## 3. Item 7 — Review Clustering Alert (Agent A)

### Goal
Surface emerging issue clusters before they become PR crises: 3+ negative mentions of the same issue within 14 days warrants a proactive alert.

### Logic — added to `alerts.py`
New `_check_review_cluster(brand_id, threshold)`:
```
cutoff = now - 14 days
rows = articles WHERE brand_id=? AND sentiment_label='negative'
       AND collected_at >= cutoff AND issue_category IS NOT NULL
group by issue_category → count
for each category where count >= threshold:
    return (count, category_name)
```

### Alert type
Add `review_cluster` to `_ALERT_META`:
- Subject: "Review Cluster Alert"
- Detail: "3+ negative mentions of [category] in the last 14 days"

### Trigger
In `check_and_fire_alerts`, add:
```python
elif alert_type == "review_cluster":
    result = _check_review_cluster(brand_id, int(threshold))
    if result:
        current_value, extra_context = result
```

Threshold default: 3 (configurable via `alert_configs.threshold`).

---

## 4. Item 5 — Human Review Queue (Agent B)

### Goal
High-stakes NLP classifications (crisis / regulatory, low confidence) should not flow directly into leadership dashboards without a human check.

### Data model — migration 018
```sql
CREATE TABLE human_review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID NOT NULL,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,           -- e.g. "low_confidence:0.28:Crisis & Controversy"
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    reviewer_id UUID REFERENCES auth.users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_hrq_brand_status ON human_review_queue(brand_id, status);
```

### Queue population
In `storage/postgres.py`, extend `save_article` to check: if `nlp["confidence"] < 0.5` AND `nlp["issue_category"]` in `("Crisis & Controversy", "Regulatory & Compliance")`, insert a row into `human_review_queue`.

### Backend endpoints — `dashboard/router.py`
```
GET  /dashboard/review-queue/{brand_id}
     → list[ReviewQueueItem]  (pending items, newest first, limit 50)

PATCH /dashboard/review-queue/{item_id}
     body: { "status": "approved" | "rejected", "reviewer_id": "<uid>" }
     → ReviewQueueItem (updated)
```

Auth: both endpoints require `WRITE_ROLES` minimum.

### Schemas — `dashboard/schemas.py`
```python
class ReviewQueueItem(BaseModel):
    id: str
    brand_id: str
    article_id: str
    article_title: str        # joined from articles
    issue_category: str
    confidence: float
    sentiment_label: str
    reason: str
    status: str
    created_at: str
    reviewed_at: str | None

class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    pending_count: int
```

### Frontend — `ReviewQueue.tsx` (new page)
- Route: `/brand/:brandId/review-queue`
- Sidebar entry: "Review Queue" with a red badge showing pending count (admin-only, same guard as Channel Settings)
- Table layout: article title · issue category · confidence % · sentiment badge · reason · Approve / Reject buttons
- On approve/reject: optimistic update + `PATCH` call + invalidate query

---

## 5. Item 8 — Per-video Brand Risk Score (Agent B)

### Goal
Surface `Brand Risk Score` (as defined in the YouTube Sentiment Framework) per video so analysts can prioritize which videos need attention.

### Formula (already implemented in `perception.py`, now surfaced per-video)
```
Brand Risk Score = sentiment(−1 to +1) × log_reach(0–1) × engagement(0–1) × recency_decay
```
Where:
- `sentiment`: article's `sentiment_score` field (already −1 to +1)
- `log_reach`: `log10(view_count + 1) / log10(10_000_001)` (capped at 10M views)
- `engagement`: `(likes + comments) / max(views, 1)`, capped at 0.10 → 1.0
- `recency_decay`: from `_recency_weight()` in `perception.py`

Score is signed: negative sentiment → negative risk score. Sort descending by absolute value to show highest-impact videos first.

### Backend endpoint — `dashboard/router.py`
```
GET /dashboard/brand-risk-scores/{brand_id}
    → BrandRiskScoresResponse
```
Fetches last 30 days of `youtube_video` articles for the brand, computes score per video, returns top 10 by `abs(score)`.

### Schemas
```python
class VideoRiskItem(BaseModel):
    article_id: str
    title: str
    url: str
    portal_id: str
    view_count: int
    like_count: int
    comment_count: int
    sentiment_label: str
    sentiment_score: float
    brand_risk_score: float   # signed, −1.0 to +1.0
    published_at: str | None
    reach_tier: str           # "viral" | "high" | "mid" | "low"

class BrandRiskScoresResponse(BaseModel):
    items: list[VideoRiskItem]
    brand_id: str
```

### Frontend — `BrandRiskScores.tsx` (new component)
- Displayed in the YouTube detail panel (already accessible via click-to-detail from Overview)
- Table: thumbnail placeholder (▶ icon) · title (linked) · view count · risk score bar (red = negative risk, green = positive) · sentiment badge
- `reach_tier` badge: Viral (>1M views) · High (100K–1M) · Mid (10K–100K) · Low (<10K)

---

## 6. Item 4 — Source Authority Tiers (Agent C)

### Goal
Make the formal tier classification (Tier 1–4) visible to analysts so they can interpret headlines in context (a Tier 1 negative story carries far more weight than a Tier 4 one).

### Tier mapping (derived from existing `credibility` float in `portals.py`)
```
Tier 1 — National flagship: credibility ≥ 0.88
Tier 2 — Strong regional / major metro: 0.78–0.87
Tier 3 — Regional / mid-tier: 0.65–0.77
Tier 4 — Community / niche: < 0.65
```
Wire service portals (gnews-generated) use `source_tier = 0, source_tier_label = "Wire"`.

### Implementation
1. Add `source_tier: int` and `source_tier_label: str` to the `Portal` TypedDict in `portals.py`, populated using the mapping above.
2. In `dashboard/router.py`'s headlines endpoint, the `HeadlineItem` already has `source_tier` and `source_tier_label` fields — wire the values from the portal lookup (currently returns 0/"Unknown").
3. Frontend `TopHeadlines.tsx`: add a small tier pill next to the portal name — `T1` (indigo) · `T2` (blue) · `T3` (slate) · `T4` (gray) · `Wire` (amber).

---

## 7. Item 10 — SoV Caveat Disclosure (Agent C)

### Goal
Prevent misinterpretation of the Competitor Share of Voice chart as a total-market view when it is YouTube + news only.

### Implementation — `CompetitorShareOfVoice.tsx`
1. Add an ℹ️ icon button next to the "Competitor Share of Voice" heading. On hover/click, show a tooltip: *"Based on YouTube and news portal coverage only. Twitter/X, Instagram, and Facebook are not yet monitored."*
2. Add a small grey footnote below the donut (visible without interaction): *"YouTube & news coverage only — social media channels excluded."*

No backend changes required.

---

## 8. Item 6 — Google Business Review Connector (Agent D)

### Goal
Ingest Google Business reviews as a first-class data source alongside news and YouTube, giving brand teams their customer-facing review signal.

### Data model — migration 019
```sql
ALTER TABLE brand_configs
    ADD COLUMN IF NOT EXISTS google_places_id TEXT,
    ADD COLUMN IF NOT EXISTS google_reviews_enabled BOOLEAN NOT NULL DEFAULT FALSE;
```

### Collector — `backend/app/ingestion/google_reviews_collector.py` (new)
Uses Google Places API v1. Requires `GOOGLE_PLACES_API_KEY` env var (graceful no-op if absent).

Per run:
- If `google_places_id` is already stored in brand config → skip Text Search, go directly to Place Details.
- If `google_places_id` is empty → call Text Search for `{brand_name}` to resolve it, save it back to `brand_configs`, then proceed.
- Place Details request: `fields=name,reviews,rating`
- Returns up to 5 most recent reviews
- Maps each review to the standard article dict:
  - `source_type = "google_review"`
  - `source_platform = "review"`
  - `portal_id = "google_business"`
  - `portal_name = "Google Business"`
  - `source_credibility = 0.70`
  - `content_hash` = SHA256 of `(brand_id + review_author + review_time)`
  - `reach_metadata = {"rating": 4, "author": "...", "relative_time": "..."}`
  - `title` = first 120 chars of review text
  - `body` = full review text

### Orchestrator touch
In `run_brand_pipeline`, alongside the Reddit block:
```python
if config.get("google_reviews_enabled", False) and config.get("google_places_id"):
    try:
        from app.ingestion.google_reviews_collector import collect_google_reviews_for_brand
        gr_raw = collect_google_reviews_for_brand(brand, config)
        gr_new = filter_new_articles(gr_raw, brand_id)
        new_articles.extend(gr_new)
        stats["collected"] += len(gr_raw)
    except Exception as e:
        log.error("Google reviews failed for brand %s: %s", brand_id[:8], e)
```

### Channel Settings page
Add a "Google Business Reviews" section to `BrandConfig.tsx`:
- Toggle: `google_reviews_enabled`
- Text input: `google_places_id` (with a link to Google Maps search to help users find their Place ID)

### NLP
Google reviews pass through the existing NLP pipeline unchanged — they're short text, similar in character to Reddit comments, so the `reddit_comment` social-text prompt path applies (or a new `google_review` path sharing the same prompt). `issue_category` classification runs as usual.

---

## 9. Item 9 — YouTube Creator Type Classification (Agent E)

### Goal
Classify the creator of each YouTube video so analysts can weight a tech journalist's negative review differently from a random customer complaint.

### Schema — `nlp/schemas.py`
Add to `NLPResult`:
```python
creator_type: str = "unknown"  # only set for source_type == "youtube_video"
```
Add to `to_dict()`:
```python
"creator_type": self.creator_type,
```

### NLP prompt addition — `gemini_handler.py` and `groq_handler.py`
Inside the `youtube_video` prompt path (already branched on `source_type`), add one additional field to the JSON response schema:

```
"creator_type": one of journalist | reviewer | influencer | customer | industry_expert | activist | competitor_affiliate | unknown
```

Classification guidance in the prompt:
- journalist: bylined news/media channel, reports factually
- reviewer: tech/product review channel
- influencer: lifestyle/entertainment creator with brand deals
- customer: individual sharing a personal experience
- industry_expert: analyst, consultant, subject matter expert
- activist: advocacy/campaign account
- competitor_affiliate: channel affiliated with a competing brand
- unknown: cannot determine from title/description

Zero extra API cost — added to the existing JSON extraction call.

### Database — migration 020
```sql
ALTER TABLE articles ADD COLUMN IF NOT EXISTS creator_type VARCHAR(50);
```

### Storage — `postgres.py`
`save_article` already passes all `nlp` fields through `{**article, **nlp_dict}` to Supabase upsert. Since `to_dict()` now includes `creator_type`, no changes needed to `save_article` itself — Supabase will pick it up automatically after the migration adds the column.

### Frontend
In `MentionsList.tsx` (Mention Explorer), for articles where `source_type === "youtube_video"` and `creator_type` is not "unknown", add a small grey pill after the portal badge: `journalist` · `reviewer` · `influencer` etc. Same treatment in the YouTube detail panel.

---

## 10. Merge Plan

After all 5 agents complete, merge in this order to minimise conflicts:

1. Agent E (NLP only — no shared files with others)
2. Agent C (frontend + portals.py — no backend overlap)
3. Agent A (alerts.py + new file — review orchestrator.py addition)
4. Agent D (new collector + orchestrator.py addition — merge with Agent A's orchestrator touch)
5. Agent B (dashboard router + schemas — largest set of additions, merge last for full picture)

For `orchestrator.py`: keep Agent A's `detect_virality` call inside the YouTube block; keep Agent D's Google reviews block in the same position as the Reddit block. Merge is additive — no lines are deleted by either agent.

---

## 11. Acceptance Criteria

| Item | Done when |
|---|---|
| 3 | `video_metrics_history` table exists; daily snapshots write on pipeline run; `virality_spike` alert fires in test when view_count is 3× baseline |
| 4 | `TopHeadlines` shows T1/T2/T3/T4/Wire tier pill next to each headline's portal name |
| 5 | `ReviewQueue` page lists pending items; Approve/Reject buttons update DB; articles with confidence<0.5 + Crisis/Regulatory category auto-enqueue |
| 6 | `google_reviews_enabled` toggle + `google_places_id` field visible in Channel Settings; reviews appear in Mention Explorer with `source_type=google_review`; graceful no-op when `GOOGLE_PLACES_API_KEY` is absent |
| 7 | `review_cluster` alert type works via `alert_configs`; fires when 3+ negative articles share `issue_category` within 14 days |
| 8 | `GET /dashboard/brand-risk-scores/{brand_id}` returns ranked videos; `BrandRiskScores` component visible in YT detail panel |
| 9 | `creator_type` column exists in DB; populated for `youtube_video` articles after migration; badge visible in Mention Explorer for YT videos |
| 10 | SoV donut has ℹ️ tooltip + footnote clarifying YouTube+news-only scope |
