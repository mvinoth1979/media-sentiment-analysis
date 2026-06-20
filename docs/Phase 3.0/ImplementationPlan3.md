# Phase 3 Implementation Plan — Charts Row Revamp
## Framework-Informed, BrandSense-Preserving

**Revision note:** This version integrates a critical comparison of two enterprise sentiment frameworks — the **YouTube Sentiment Monitoring Framework (Unified Enterprise)** and the **Brand Sentiment Monitoring Framework (News, RSS, Reviews & Beyond)** — against the existing MediaSense implementation. Every Phase 3 component has been updated to incorporate applicable improvements. All framework gaps that are out of Phase 3 scope are catalogued in Section 3 for future phases.

---

## 1. Tech Stack Reference

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Frontend framework | React | 19.2.6 | |
| Language | TypeScript | 6.0.2 | strict mode |
| Build | Vite | 8.x | `VITE_API_URL` env var |
| Styling | Tailwind CSS | 4.3.1 | dark theme, `gray-900` cards |
| Charts | Recharts | 3.8.1 | `LineChart`, `BarChart`, `PieChart` in use |
| HTTP | Axios | 1.18 | instance in `frontend/src/lib/api.ts`, JWT injected via interceptor |
| Server state | TanStack Query | 5.101 | `useQuery`, `keepPreviousData`, `useMutation` |
| Auth | Supabase JS | 2.108 | magic-link + JWT, RBAC via `user_roles` table |
| India map | react-simple-maps | 3.0.0 | `IndiaStateMap.tsx` — tile grid |
| Backend | FastAPI | latest | routers in `backend/app/` |
| Primary DB | Supabase (PostgreSQL) | — | `supabase-py`, `get_db()` in `postgres.py` |
| Time-series | InfluxDB | Cloud/OSS | `influxdb_client`, Flux query language |
| NLP | Gemini (primary) + Groq (fallback) | — | circuit breaker, multi-language |
| Pipeline | APScheduler + async queue | — | hourly, dead-letter retry |
| Email | Resend | — | alerts + magic-link invites |
| Deployment | Railway (backend) + Vercel (frontend) | — | |

**No new npm or pip packages required for Phase 3.**

---

## 2. Critical Framework Comparison vs. MediaSense

### 2.1 YouTube Framework — Gap Analysis

| Framework Requirement | MediaSense Status | Phase 3 Action | Future Phase |
|---|---|---|---|
| **Three-pillar structure**: Owned / Earned / Public | Missing — all YouTube treated as one flat pool | Distinguish in Headlines panel (F05 YouTube KPI stays) | Phase 8 sidebar split |
| **Influence Score** — log-normalized reach × engagement × sentiment × recency decay | Partial — `reach_score` and `source_credibility` exist; no per-video composite score | Surface `reach_metadata` in Headlines card; note formula gap | Phase 4 NLP/score update |
| **Creator vs. Audience Sentiment** — reported separately per video | Missing — `youtube_video` and `youtube_comment` stored as unlinked separate articles | Trending tab in Headlines groups by source_type; visual cue added | Phase 6 data-model link |
| **Virality detection** — 3× rolling 7-day baseline triggers | Missing — only manual threshold alerts | Trending tab applies recency + high-reach filter; "High Reach" badge | Phase 8 auto-alert engine |
| **Comment quality filtering** — ignore noise ("Nice", emojis) | Missing — all comments analysed equally | Out of Phase 3; flag for ingestion update | Phase 7 NLP pre-filter |
| **Confidence gate** — human review before Crisis Alert | Missing — alerts fire automatically | Plan for review queue; not in Phase 3 | Phase 8 |
| **Creator classification** — Journalist/Reviewer/Influencer/etc. | Missing | Out of Phase 3 | Phase 6 |
| **5-point sentiment scale** (−2 to +2) | Missing — 3-label + 0–1 score | **Map existing score to 5-level intensity label in Headlines and Trend chart** (see Section 5.7) | Full reclassification Phase 7 |
| **Audit trail** — model version, confidence, reviewer | Partial — `model_used` stored; no confidence score, no reviewer field | Out of Phase 3 | Phase 9 |
| **Regional language accuracy disclosure** | Partial — 6 languages supported; no per-language confidence reported | Out of Phase 3 | Phase 9 |
| **Brand name detection** — misspellings, abbreviations, executives | Partial — keyword list per brand; no fuzzy match | Out of Phase 3 | Phase 6 |

### 2.2 Web Sentiment Framework — Gap Analysis

| Framework Requirement | MediaSense Status | Phase 3 Action | Future Phase |
|---|---|---|---|
| **Source Authority Tier matrix** (Tier 1–4 + Wire) | Partial — flat `source_credibility` 0–1; no tier label | **Derive Tier 1–4 from credibility in Headlines badge and Donut tooltip** (see Section 5.7) | Formalise tiers in portals.py Phase 4 |
| **Headline vs. Body sentiment** — analysed separately | Missing — one score per article | Out of Phase 3; requires NLP schema change | Phase 7 |
| **Quote extraction & attribution** — NER-attributed quotes | Missing — `entities[]` exists but no quote attribution | Out of Phase 3 | Phase 7 |
| **Editorial tone vs. factual negativity** | Missing | Out of Phase 3 | Phase 7 |
| **Syndication deduplication** — wire service as one story | Partial — content-hash dedup; doesn't detect near-duplicate reprints | Add `syndication_count` indicator in Headlines (Section 5.5) | Phase 6 |
| **Journalist / beat tracking** — repeat-critic flag | Missing — `author_info.display_name` stored; no tracking | **Add repeat-author flag to `/headlines` endpoint** (see Section 5.5) | Full journalist CRM Phase 8 |
| **Regulatory source escalation** | Missing | Out of Phase 3 | Phase 8 |
| **5-point news sentiment scale** | Missing — 3-label | **Map to 5-level intensity label (same as YouTube)** (see Section 5.7) | Full reclassification Phase 7 |
| **Review platform monitoring** (MouthShut, JustDial, Trustpilot, Google Business) | Missing | Out of Phase 3 (Phase 5) | Phase 5 |
| **Star rating vs. text divergence** | Missing — no review sites yet | Out of Phase 3 | Phase 5 |
| **Review clustering detection** (3+ reviews, same issue, 14 days) | Missing | Out of Phase 3 | Phase 5 |
| **Google search rank tracking** | Missing | Out of Phase 3 | Phase 8 |
| **Blog/long-form web monitoring** | Missing | Out of Phase 3 | Phase 8 |
| **Confidence gate / human review queue** | Missing | Out of Phase 3 | Phase 8 |
| **Audit trail + data provenance** | Partial — `model_used` stored | Out of Phase 3 | Phase 9 |
| **Regional language source list per state** | Partial — 6 languages; sources not tagged by state/region | Out of Phase 3 | Phase 4 |

### 2.3 Framework Improvements Directly Applicable to Phase 3

Of all framework requirements, the following can be implemented in Phase 3 within the chart row components **without NLP pipeline changes or data model migrations**:

| Improvement | Source | Where Applied in Phase 3 | Implementation Effort |
|---|---|---|---|
| **5-level sentiment intensity label** derived from existing 0–1 score + 3-label | Both frameworks | Top Headlines card badges; Trend chart tooltip | Low — pure frontend mapping function |
| **Source Authority Tier badge** derived from existing `source_credibility` | Web framework §1.4 | Top Headlines card; Donut legend tooltip | Low — threshold mapping function |
| **Repeat-author flag** on negative headlines | Web framework §1.7 | Top Headlines — backend computes, frontend renders | Medium — one extra query in `/headlines` endpoint |
| **Creator vs. Audience visual separation** on Trending tab | YouTube framework §3 | Top Headlines Trending tab groups by source_type | Low — frontend grouping |
| **High-Reach / Virality badge** on YouTube items | YouTube framework §4 | Top Headlines Trending tab — view_count threshold | Low — frontend conditional render |
| **Authority-weighted Donut tooltip** | Web framework §1.4 | MentionsBySourceDonut — tooltip shows avg tier | Low — backend adds `avg_credibility` per category |
| **Tier label in Donut legend** | Web framework §1.4 | Donut legend rows show credibility tier label | Low — frontend label function |
| **Sentiment intensity in Trend tooltip** | Both frameworks | Trend chart tooltip shows intensity breakdown | Low — frontend formatter |

---

## 3. Feature Preservation Decision Matrix (All 68 BrandSense Features)

Every existing BrandSense feature maps to one disposition:
- **KEEP AS-IS** — unchanged, same location
- **KEEP + REPOSITION** — same behaviour, moved
- **ENHANCED** — same purpose, upgraded presentation
- **OUT OF SCOPE** — deferred (phase noted)

| Feature | Disposition | Phase 3 Action |
|---|---|---|
| F01 Brand header + last updated | KEEP AS-IS | Top of Overview, untouched |
| F02 Pipeline status banner | KEEP AS-IS | Below header, untouched |
| F03 Perception Score KPI | KEEP + REPOSITION | Stays as KPI card; display label may evolve in Phase 2 |
| F04 Total Mentions KPI | KEEP AS-IS | Unchanged |
| F05 YouTube Mentions KPI | KEEP AS-IS | Unchanged; YouTube framework notes owned/earned split for Phase 6 |
| F06 Sentiment Pie/Donut | KEEP AS-IS | Stays alongside KPI row |
| **F07 Trend chart** | **ENHANCED** | **Rewritten: 3 lines + intensity tooltips + source-tier toggle** |
| **F08 Annotation system** | **KEEP AS-IS** | **Preserved in full through SentimentTrendChart rewrite — see Section 6.3** |
| F09 Top Sources list | KEEP + REPOSITION | Moves below new 3-panel row; gains tier labels |
| F10 India State Map | KEEP AS-IS | Below sources, unchanged |
| F11 State drill-through | KEEP AS-IS | URL param unchanged |
| F12 Mention Explorer | KEEP AS-IS | All 19 sub-features intact |
| F13 Topics tag cloud | KEEP AS-IS | Below Mention Explorer |
| F14 Keywords tag cloud | KEEP AS-IS | Below Mention Explorer |
| F15 Email alerts config | KEEP AS-IS | Admin-gated, stays (moves to Settings in Phase 8) |
| F16–F34 All Mention Explorer filters | KEEP AS-IS | `initialSentiment` prop added; nothing else changes |
| F35–F40 Sources/Topics tabs | KEEP AS-IS | No changes |
| F41–F45 Brand management | KEEP AS-IS | No changes |
| F46–F48 User management | KEEP AS-IS | No changes |
| F49–F53 Auth + RBAC | KEEP AS-IS | No changes |
| F54–F68 All backend operational | KEEP AS-IS | No pipeline, NLP, or storage changes in Phase 3 |

**Phase 3 net-new additions** (nothing replaced, nothing removed):

| Addition | Framework Source |
|---|---|
| Multi-line Sentiment Trend (Positive/Neutral/Negative) | New — addresses single-line limitation |
| Sentiment intensity 5-level mapping in chart tooltip | Both frameworks |
| Source Authority tier toggle on Trend chart | Web framework §1.4 |
| Mentions by Source Donut with tier tooltip | Web framework §1.4 |
| Top Headlines Panel (3 tabs) | Reference dashboard + both frameworks |
| Sentiment intensity badge on Headlines | Both frameworks §§ |
| Source Tier badge on Headlines | Web framework §1.4 |
| Repeat-author flag on negative Headlines | Web framework §1.7 |
| Creator vs. Audience grouping on Trending tab | YouTube framework §3 |
| High-Reach / virality badge on YouTube Headlines | YouTube framework §4 |

---

## 4. Scope Boundaries

**In scope for Phase 3:**
- InfluxDB: new `query_sentiment_counts_trend()` functions
- New `/dashboard/trends/{brand_id}/sentiment` endpoint
- New `/dashboard/source-categories/{brand_id}` endpoint with avg_credibility per category
- New `/dashboard/headlines/{brand_id}` endpoint with repeat-author enrichment
- `portals.py`: `category` field + `get_portal_category()` + `get_portal_tier()` helper
- `SentimentTrendChart.tsx` — 3-line rewrite, annotation preserved, tier-filter toggle, intensity tooltip
- New `MentionsBySourceDonut.tsx` with tier labels in legend
- New `TopHeadlines.tsx` with intensity badges, tier badges, repeat-author flag, creator/audience grouping, high-reach badge
- `Overview.tsx` second-row layout update + `initialSentiment` prop plumbing
- `MentionsList.tsx` — add `initialSentiment` prop only
- New `frontend/src/lib/utils.ts` — `formatCount`, `sentimentIntensity`, `credibilityToTier`

**Explicitly out of Phase 3:**
- Headline vs. body NLP separation (Phase 7)
- Quote extraction and attribution (Phase 7)
- Editorial tone classification (Phase 7)
- Full 5-point rescoring in NLP (Phase 7 — Phase 3 maps existing score to labels, no rescore)
- Journalist CRM / beat tracking database (Phase 8)
- Syndication chain deduplication (Phase 6)
- Creator classification (Journalist/Influencer/etc.) (Phase 6)
- Comment quality pre-filter in ingestion (Phase 7)
- Confidence gate / human review queue (Phase 8)
- Review site collection (Phase 5)
- Blog/long-form monitoring (Phase 8)
- Google search rank tracking (Phase 8)
- Competitor benchmarking SOV (Phase 7)
- Audit trail data model (Phase 9)
- Sidebar navigation shell (Phase 1)
- Global DateRangeContext (Phase 9 — Phase 3 components accept optional props)
- Compare mode toggle (Phase 9)
- KPI 5-card layout (Phase 2)

---

## 5. Backend Changes

### 5.1 Portal Category + Tier Classification (`backend/app/ingestion/portals.py`)

**Two additions:** `category` field on every portal dict, and two new helper functions — `get_portal_category()` and `get_portal_tier()`.

**Source Authority Tier matrix** (derived from Web Framework §1.4, mapped to existing credibility scores):

| Tier | Label | Credibility Range | Examples | Weight |
|---|---|---|---|---|
| 1 | Tier 1 — National | ≥ 0.87 | The Hindu, Economic Times, NDTV, Hindustan Times, Mint | 3× |
| 2 | Tier 2 — Regional / Major Vernacular | 0.78–0.86 | Deccan Herald, Deccan Chronicle, Ananda Bazar, Prajavani, Vikatan | 2× |
| 3 | Tier 3 — Trade / Specialist | 0.68–0.77 | Polimer News, Oneindia Tamil, News18, Kannadaprabha | 1.5× |
| 4 | Tier 4 — Hyperlocal / Community | < 0.68 | Hari Bhoomi, Nakkheeran, community portals | 1× |

Note: These thresholds approximate the manual Tier 1–4 classification using the credibility scores already in `portals.py`. A future Phase 4 task will add an explicit `tier` field to formalize this.

**New functions to add at bottom of `portals.py`:**

```python
PORTAL_CATEGORY_PREFIXES: dict[str, str] = {
    "youtube_": "youtube",
}

CATEGORY_LABELS = {
    "news":        "News & RSS",
    "youtube":     "YouTube",
    "blog":        "Blogs & Portals",
    "review_site": "Review Sites",
    "social":      "Social & Forums",
}

CATEGORY_COLORS = {
    "news":        "#6366f1",
    "youtube":     "#ef4444",
    "blog":        "#f59e0b",
    "review_site": "#22c55e",
    "social":      "#a855f7",
}

def get_portal_category(portal_id: str) -> str:
    """Maps a portal_id to its source category."""
    for prefix, cat in PORTAL_CATEGORY_PREFIXES.items():
        if portal_id.startswith(prefix):
            return cat
    portal = get_portal(portal_id)
    if portal:
        return portal.get("category", "news")
    return "news"

def get_portal_tier(portal_id: str) -> int:
    """
    Derives Source Authority Tier (1–4) from existing credibility score.
    Tier 1: national/major outlets (credibility ≥ 0.87)
    Tier 2: regional/major vernacular (0.78–0.86)
    Tier 3: trade/specialist (0.68–0.77)
    Tier 4: hyperlocal/community (< 0.68)
    YouTube sources return tier 0 (different authority concept).
    """
    if portal_id.startswith("youtube_"):
        return 0
    portal = get_portal(portal_id)
    if not portal:
        return 4
    cred = portal.get("credibility", 0.5)
    if cred >= 0.87:
        return 1
    if cred >= 0.78:
        return 2
    if cred >= 0.68:
        return 3
    return 4

TIER_LABELS = {0: "YouTube", 1: "Tier 1", 2: "Tier 2", 3: "Tier 3", 4: "Tier 4"}
```

**Portal dict update — add `"category": "news"` to all 40+ news RSS entries:**

```python
# Before:
{"id": "the_hindu", "name": "The Hindu", "language": "en", "credibility": 0.92,
 "rss_url": "https://..."}

# After:
{"id": "the_hindu", "name": "The Hindu", "language": "en", "credibility": 0.92,
 "category": "news", "rss_url": "https://..."}
```

---

### 5.2 New InfluxDB Functions (`backend/app/storage/influxdb.py`)

The existing `query_sentiment_trend()` (perception score, single-line) is **not modified**.

**Context:** `positive_count`, `negative_count`, `neutral_count` are already written per pipeline run via `write_sentiment_point()`. The Flux `pivot()` function collapses three field-rows per timestamp into one wide row in a single round-trip.

```python
def query_sentiment_counts_trend(brand_id: str, days: int = 30) -> list[dict]:
    """
    Returns daily aggregated positive/neutral/negative counts.
    Uses pivot() to collapse 3 field-rows per timestamp — single Flux round-trip.
    Result: [{time: ISO-str, positive: int, negative: int, neutral: int}]
    """
    flux = f'''
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: -{days}d)
  |> filter(fn: (r) => r._measurement == "brand_sentiment")
  |> filter(fn: (r) => r.brand_id == "{brand_id}")
  |> filter(fn: (r) => r._field == "positive_count" or
                        r._field == "negative_count" or
                        r._field == "neutral_count")
  |> aggregateWindow(every: 1d, fn: sum, createEmpty: false)
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> yield(name: "daily")
'''
    try:
        with _client() as c:
            tables = c.query_api().query(flux, org=settings.influxdb_org)
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time":     record.get_time().isoformat(),
                        "positive": int(record.values.get("positive_count") or 0),
                        "negative": int(record.values.get("negative_count") or 0),
                        "neutral":  int(record.values.get("neutral_count")  or 0),
                    })
            return sorted(results, key=lambda r: r["time"])
    except Exception:
        return []


def query_sentiment_counts_trend_range(
    brand_id: str,
    date_from: str,
    date_to: str,
    window: str = "1d",
) -> list[dict]:
    """
    Explicit date-range variant. window: Flux duration string e.g. "1d", "1h".
    date_from / date_to: ISO-8601 strings.
    """
    flux = f'''
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: {date_from}, stop: {date_to})
  |> filter(fn: (r) => r._measurement == "brand_sentiment")
  |> filter(fn: (r) => r.brand_id == "{brand_id}")
  |> filter(fn: (r) => r._field == "positive_count" or
                        r._field == "negative_count" or
                        r._field == "neutral_count")
  |> aggregateWindow(every: {window}, fn: sum, createEmpty: false)
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> yield(name: "range")
'''
    try:
        with _client() as c:
            tables = c.query_api().query(flux, org=settings.influxdb_org)
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time":     record.get_time().isoformat(),
                        "positive": int(record.values.get("positive_count") or 0),
                        "negative": int(record.values.get("negative_count") or 0),
                        "neutral":  int(record.values.get("neutral_count")  or 0),
                    })
            return sorted(results, key=lambda r: r["time"])
    except Exception:
        return []
```

---

### 5.3 New Endpoint: Sentiment Trend (`backend/app/dashboard/router.py`)

**Route:** `GET /dashboard/trends/{brand_id}/sentiment`

Does **not** replace the existing annotations endpoint at `/dashboard/trends/{brand_id}/annotations`.

**Query params:**

| Param | Type | Default |
|---|---|---|
| `days` | int | 30 (ignored if `date_from` set) |
| `date_from` | str \| None | None |
| `date_to` | str \| None | None |
| `tier_filter` | int \| None | None — if set (1 or 2), only articles from portals at that tier or above are counted. Enables "Tier 1 only" toggle on the chart. |

**Window selection:** span ≤ 14 days → `"1h"` granularity; longer → `"1d"`.

**`tier_filter` note:** When `tier_filter=1`, the InfluxDB query cannot filter by tier (InfluxDB doesn't know portal tiers). Instead, the endpoint must count articles from Supabase filtered by portal credibility ≥ 0.87, then return that as a separate `points_tier1` array alongside the unfiltered `points`. The frontend decides which series to display.

**Response schema:**
```python
class SentimentTrendPoint(BaseModel):
    time: str
    positive: int
    negative: int
    neutral: int

class SentimentTrendResponse(BaseModel):
    points: list[SentimentTrendPoint]          # all sources
    points_tier1: list[SentimentTrendPoint]    # Tier 1 + 2 only (credibility >= 0.78)
    window: str                                 # "1d" or "1h"
```

**`points_tier1` computation:** From Supabase `articles` table, group articles by day where `source_credibility >= 0.78`, aggregate positive/negative/neutral counts per day. This is a Python-side aggregation of `get_articles()` results — no new DB query needed.

**Router implementation:**

```python
@router.get("/trends/{brand_id}/sentiment", response_model=SentimentTrendResponse)
def get_sentiment_trend(
    brand_id: str,
    days: int = Query(30, ge=1, le=365),
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    from app.storage.influxdb import (
        query_sentiment_counts_trend,
        query_sentiment_counts_trend_range,
    )
    effective_to = date_to or datetime.now(timezone.utc).isoformat()
    span_days = _days_between(date_from, effective_to) if date_from else days
    window = "1h" if span_days <= 14 else "1d"

    if date_from:
        raw = query_sentiment_counts_trend_range(brand_id, date_from, effective_to, window)
    else:
        raw = query_sentiment_counts_trend(brand_id, days)

    # Tier 1+2 series: aggregate from Supabase articles (credibility >= 0.78)
    tier_articles = get_articles(
        brand_id, limit=2000,
        date_from=date_from,
        date_to=date_to if date_to else None,
    )
    tier12_articles = [a for a in tier_articles if (a.get("source_credibility") or 0) >= 0.78]
    points_tier1 = _aggregate_by_day(tier12_articles, window)

    return SentimentTrendResponse(
        points=[SentimentTrendPoint(**p) for p in raw],
        points_tier1=[SentimentTrendPoint(**p) for p in points_tier1],
        window=window,
    )


def _aggregate_by_day(articles: list[dict], window: str) -> list[dict]:
    """Aggregates article list into {time, positive, negative, neutral} per day."""
    from collections import defaultdict
    buckets: dict[str, dict] = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for a in articles:
        ts = a.get("collected_at") or a.get("published_at") or ""
        if not ts:
            continue
        day = ts[:10]  # YYYY-MM-DD
        label = a.get("sentiment_label", "neutral")
        buckets[day][label] += 1
    return [
        {"time": f"{day}T00:00:00+00:00", **counts}
        for day, counts in sorted(buckets.items())
    ]


def _days_between(iso_from: str, iso_to: str) -> int:
    a = datetime.fromisoformat(iso_from.replace("Z", "+00:00"))
    b = datetime.fromisoformat(iso_to.replace("Z", "+00:00"))
    return abs((b - a).days)
```

---

### 5.4 New Endpoint: Source Categories (`backend/app/dashboard/router.py`)

**Route:** `GET /dashboard/source-categories/{brand_id}`

**Query params:** `date_from`, `date_to` (optional ISO-8601)

**Auth:** `require_brand_role(*READ_ROLES)`

**Framework addition:** Each category now includes `avg_credibility` and `tier_distribution` (count per tier) so the frontend Donut tooltip can show authority context.

**Response schema:**
```python
class SourceCategoryPoint(BaseModel):
    category: str
    label: str
    color: str
    count: int
    positive: int
    negative: int
    neutral: int
    pct: float
    avg_credibility: float          # NEW: average credibility of portals in this category
    tier_distribution: dict[str, int]  # NEW: {"tier1": N, "tier2": N, "tier3": N, "tier4": N}

class SourceCategoriesResponse(BaseModel):
    categories: list[SourceCategoryPoint]
    total: int
```

**Implementation:**

```python
@router.get("/source-categories/{brand_id}", response_model=SourceCategoriesResponse)
def get_source_categories(
    brand_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    from app.ingestion.portals import (
        get_portal_category, get_portal_tier,
        CATEGORY_LABELS, CATEGORY_COLORS
    )
    articles = get_articles(brand_id, limit=2000, date_from=date_from, date_to=date_to)
    cat_map: dict[str, dict] = {}
    for a in articles:
        pid = a.get("portal_id", "")
        cat = get_portal_category(pid)
        tier = get_portal_tier(pid)
        if cat not in cat_map:
            cat_map[cat] = {
                "category": cat, "label": CATEGORY_LABELS.get(cat, cat),
                "color": CATEGORY_COLORS.get(cat, "#6b7280"),
                "count": 0, "positive": 0, "negative": 0, "neutral": 0,
                "_cred_sum": 0.0,
                "_tier_dist": {"tier1": 0, "tier2": 0, "tier3": 0, "tier4": 0, "youtube": 0},
            }
        cat_map[cat]["count"] += 1
        cat_map[cat]["_cred_sum"] += a.get("source_credibility") or 0.5
        cat_map[cat][a.get("sentiment_label", "neutral")] += 1
        tier_key = f"tier{tier}" if tier > 0 else "youtube"
        cat_map[cat]["_tier_dist"][tier_key] = cat_map[cat]["_tier_dist"].get(tier_key, 0) + 1

    total = sum(v["count"] for v in cat_map.values())
    result = []
    for entry in sorted(cat_map.values(), key=lambda x: x["count"], reverse=True):
        count = entry["count"]
        result.append(SourceCategoryPoint(
            category=entry["category"], label=entry["label"], color=entry["color"],
            count=count, positive=entry["positive"],
            negative=entry["negative"], neutral=entry["neutral"],
            pct=round(count / total * 100, 1) if total else 0,
            avg_credibility=round(entry["_cred_sum"] / count, 2) if count else 0.0,
            tier_distribution=entry["_tier_dist"],
        ))
    return SourceCategoriesResponse(categories=result, total=total)
```

---

### 5.5 New Endpoint: Top Headlines (`backend/app/dashboard/router.py`)

**Route:** `GET /dashboard/headlines/{brand_id}`

**Framework additions beyond original plan:**
1. **`source_tier`** field on each item — derived from `get_portal_tier()`
2. **`sentiment_intensity`** field — 5-level label mapped from existing score (no NLP change)
3. **`repeat_author`** flag — True if this author appears in ≥ 2 negative articles within 30 days
4. **`reach_tier`** for YouTube — "High" / "Medium" / "Low" based on view_count thresholds
5. **`source_type`** passed through — enables frontend to group Creator vs. Audience on Trending tab

**Query params:**

| Param | Type | Default | Notes |
|---|---|---|---|
| `tab` | str | `"positive"` | `"positive"`, `"negative"`, `"trending"` |
| `limit` | int | 5 | max 10 |
| `date_from` | str \| None | None | |
| `date_to` | str \| None | None | |

**Sentiment intensity mapping function** (both frameworks prescribe −2 to +2 scale; we map our existing 0–1 score + 3-label):

```python
def _sentiment_intensity(label: str, score: float) -> str:
    """
    Maps existing sentiment_label + sentiment_score to a 5-level intensity label.
    Does NOT rescore — uses existing NLP output.
    Framework: Strongly Positive / Mildly Positive / Neutral / Mildly Negative / Strongly Negative
    """
    if label == "positive":
        return "Strongly Positive" if score >= 0.75 else "Mildly Positive"
    if label == "negative":
        return "Strongly Negative" if score <= 0.25 else "Mildly Negative"
    return "Neutral"
```

**Repeat-author detection:**

```python
def _get_repeat_negative_authors(brand_id: str, days: int = 30) -> set[str]:
    """
    Returns set of author display names who appear in >= 2 negative articles
    within the last `days` days. Used to flag repeat critics (Web Framework §1.7).
    """
    from datetime import datetime, timedelta, timezone
    from collections import Counter
    date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    articles = get_articles(brand_id, limit=500, sentiment="negative", date_from=date_from)
    author_counts = Counter(
        a.get("author") for a in articles
        if a.get("author") and not a["author"].startswith("youtube_")
    )
    return {author for author, count in author_counts.items() if count >= 2}
```

**YouTube reach tier** (YouTube Framework §1 — Influence Score without full log-norm formula):

```python
def _youtube_reach_tier(view_count: int) -> str:
    """
    Approximates the virality reach tier from the YouTube framework §4.
    Full log-normalized Brand Risk Score is a Phase 6 enhancement.
    """
    if view_count >= 500_000:
        return "High"
    if view_count >= 50_000:
        return "Medium"
    return "Low"
```

**Response schema:**

```python
class HeadlineItem(BaseModel):
    id: str
    title: str
    url: str
    portal_id: str
    portal_name: str
    portal_category: str       # "news", "youtube", etc.
    source_tier: int           # 0=YouTube, 1–4 per tier matrix
    source_tier_label: str     # "Tier 1", "Tier 2", etc. / "YouTube"
    published_at: str | None
    collected_at: str | None
    sentiment_label: str       # "positive" / "negative" / "neutral"
    sentiment_score: float     # 0–1, existing NLP output
    sentiment_intensity: str   # "Strongly Positive" … "Strongly Negative"
    source_credibility: float
    language: str
    source_type: str           # "news", "youtube_video", "youtube_comment"
    repeat_author: bool        # True if author has >= 2 negative articles in 30 days
    reach_tier: str | None     # "High"/"Medium"/"Low" — YouTube only, None for news
    author_name: str | None    # display_name from author_info

class HeadlinesResponse(BaseModel):
    tab: str
    items: list[HeadlineItem]
```

**Full endpoint:**

```python
@router.get("/headlines/{brand_id}", response_model=HeadlinesResponse)
def get_headlines(
    brand_id: str,
    tab: str = Query("positive", pattern="^(positive|negative|trending)$"),
    limit: int = Query(5, ge=1, le=10),
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    from app.ingestion.portals import get_portal, get_portal_category, get_portal_tier, TIER_LABELS
    sentiment_filter = None if tab == "trending" else tab

    articles = get_articles(
        brand_id, limit=limit * 6,
        sentiment=sentiment_filter,
        date_from=date_from, date_to=date_to,
    )

    if tab == "positive":
        articles = sorted(articles, key=lambda a: (
            a.get("sentiment_score") or 0, a.get("source_credibility") or 0
        ), reverse=True)
    elif tab == "negative":
        articles = sorted(articles, key=lambda a: (a.get("sentiment_score") or 0))
    elif tab == "trending":
        # collected_at DESC already from get_articles; filter low-credibility noise
        articles = [a for a in articles if (a.get("source_credibility") or 0) >= 0.70]

    repeat_authors = _get_repeat_negative_authors(brand_id) if tab == "negative" else set()

    items = []
    for a in articles[:limit]:
        pid = a.get("portal_id", "")
        portal = get_portal(pid)
        tier = get_portal_tier(pid)
        label = a.get("sentiment_label", "neutral")
        score = a.get("sentiment_score") or 0.5
        reach_meta = a.get("reach_metadata") or {}
        view_count = int(reach_meta.get("view_count") or 0)
        author = a.get("author")

        items.append(HeadlineItem(
            id=a.get("id", ""),
            title=a.get("title", ""),
            url=a.get("url", ""),
            portal_id=pid,
            portal_name=portal["name"] if portal else pid.replace("_", " ").title(),
            portal_category=get_portal_category(pid),
            source_tier=tier,
            source_tier_label=TIER_LABELS.get(tier, "Tier 4"),
            published_at=a.get("published_at"),
            collected_at=a.get("collected_at"),
            sentiment_label=label,
            sentiment_score=score,
            sentiment_intensity=_sentiment_intensity(label, score),
            source_credibility=a.get("source_credibility") or 0.5,
            language=a.get("language", "en"),
            source_type=a.get("source_type") or "news",
            repeat_author=bool(author and author in repeat_authors),
            reach_tier=_youtube_reach_tier(view_count) if pid.startswith("youtube_") and view_count > 0 else None,
            author_name=author,
        ))
    return HeadlinesResponse(tab=tab, items=items)
```

---

### 5.6 Schema Additions (`backend/app/dashboard/schemas.py`)

Add at the bottom. All existing 14 models unchanged.

```python
# --- Phase 3: Sentiment Trend (multi-line + Tier 1 overlay) ---
class SentimentTrendPoint(BaseModel):
    time: str
    positive: int
    negative: int
    neutral: int

class SentimentTrendResponse(BaseModel):
    points: list[SentimentTrendPoint]
    points_tier1: list[SentimentTrendPoint]
    window: str  # "1d" or "1h"

# --- Phase 3: Source Categories Donut ---
class SourceCategoryPoint(BaseModel):
    category: str
    label: str
    color: str
    count: int
    positive: int
    negative: int
    neutral: int
    pct: float
    avg_credibility: float
    tier_distribution: dict

class SourceCategoriesResponse(BaseModel):
    categories: list[SourceCategoryPoint]
    total: int

# --- Phase 3: Top Headlines (framework-enhanced) ---
class HeadlineItem(BaseModel):
    id: str
    title: str
    url: str
    portal_id: str
    portal_name: str
    portal_category: str
    source_tier: int
    source_tier_label: str
    published_at: str | None = None
    collected_at: str | None = None
    sentiment_label: str
    sentiment_score: float
    sentiment_intensity: str
    source_credibility: float
    language: str
    source_type: str
    repeat_author: bool = False
    reach_tier: str | None = None
    author_name: str | None = None

class HeadlinesResponse(BaseModel):
    tab: str
    items: list[HeadlineItem]
```

---

### 5.7 Shared Utility Functions (`backend/app/dashboard/router.py` — module-level)

```python
# Module-level helpers — no import changes needed

def _sentiment_intensity(label: str, score: float) -> str:
    if label == "positive":
        return "Strongly Positive" if score >= 0.75 else "Mildly Positive"
    if label == "negative":
        return "Strongly Negative" if score <= 0.25 else "Mildly Negative"
    return "Neutral"

def _youtube_reach_tier(view_count: int) -> str:
    if view_count >= 500_000: return "High"
    if view_count >= 50_000:  return "Medium"
    return "Low"

def _get_repeat_negative_authors(brand_id: str, days: int = 30) -> set[str]:
    from datetime import timedelta
    date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    articles = get_articles(brand_id, limit=500, sentiment="negative", date_from=date_from)
    from collections import Counter
    counts = Counter(
        a.get("author") for a in articles
        if a.get("author") and not a.get("author", "").startswith("youtube_")
    )
    return {auth for auth, n in counts.items() if n >= 2}

def _aggregate_by_day(articles: list[dict], window: str) -> list[dict]:
    from collections import defaultdict
    buckets: dict[str, dict] = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for a in articles:
        ts = a.get("collected_at") or a.get("published_at") or ""
        if not ts:
            continue
        day = ts[:10]
        buckets[day][a.get("sentiment_label", "neutral")] += 1
    return [
        {"time": f"{day}T00:00:00+00:00", **counts}
        for day, counts in sorted(buckets.items())
    ]
```

---

## 6. Frontend Changes

### 6.1 New Shared Utility File (`frontend/src/lib/utils.ts`)

Create this file. It provides reusable functions used across all three new components, replacing local definitions in `MentionsList.tsx`.

```typescript
export function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return String(n);
}

/**
 * Maps existing 3-label + 0–1 score to a 5-level intensity label.
 * Framework requirement: both YouTube §2 and Web §1.3 prescribe −2 to +2 granularity.
 * This mapping avoids NLP rescore — uses existing output.
 */
export function sentimentIntensity(label: string, score: number): {
  text: string;
  color: string;
  bg: string;
} {
  if (label === "positive") {
    return score >= 0.75
      ? { text: "Strongly Positive", color: "text-emerald-400", bg: "bg-emerald-900/40" }
      : { text: "Mildly Positive",   color: "text-green-400",   bg: "bg-green-900/30"   };
  }
  if (label === "negative") {
    return score <= 0.25
      ? { text: "Strongly Negative", color: "text-red-400",    bg: "bg-red-900/50"      }
      : { text: "Mildly Negative",   color: "text-orange-400", bg: "bg-orange-900/30"   };
  }
  return { text: "Neutral", color: "text-yellow-400", bg: "bg-yellow-900/30" };
}

/**
 * Maps source_tier integer (0–4) to a display badge.
 * Web Framework §1.4: Source Authority Tier matrix.
 */
export function tierBadge(tier: number): { label: string; color: string; bg: string } {
  switch (tier) {
    case 1:  return { label: "Tier 1", color: "text-violet-300", bg: "bg-violet-900/40" };
    case 2:  return { label: "Tier 2", color: "text-blue-300",   bg: "bg-blue-900/30"   };
    case 3:  return { label: "Tier 3", color: "text-gray-300",   bg: "bg-gray-800"      };
    case 4:  return { label: "Tier 4", color: "text-gray-500",   bg: "bg-gray-900"      };
    default: return { label: "YouTube",color: "text-red-400",    bg: "bg-red-900/30"    };
  }
}

/**
 * Maps reach_tier string to a badge style.
 * YouTube Framework §4: Virality / Influence Score.
 */
export function reachBadge(tier: string): { label: string; color: string } {
  switch (tier) {
    case "High":   return { label: "High Reach",   color: "text-orange-400" };
    case "Medium": return { label: "Medium Reach", color: "text-yellow-400" };
    default:       return { label: "Low Reach",    color: "text-gray-500"   };
  }
}
```

Update `MentionsList.tsx` to import `formatCount` from `"../../lib/utils"` and remove the local definition.

---

### 6.2 New TypeScript Types (`frontend/src/lib/types.ts`)

Add at the bottom. All existing 12 interfaces unchanged.

```typescript
// --- Phase 3: Sentiment Trend (multi-line + Tier 1 overlay) ---
export interface SentimentTrendPoint {
  time: string;
  positive: number;
  negative: number;
  neutral: number;
}

export interface SentimentTrendData {
  points: SentimentTrendPoint[];
  points_tier1: SentimentTrendPoint[];
  window: "1d" | "1h";
}

// --- Phase 3: Source Categories Donut ---
export interface SourceCategoryPoint {
  category: string;
  label: string;
  color: string;
  count: number;
  positive: number;
  negative: number;
  neutral: number;
  pct: number;
  avg_credibility: number;
  tier_distribution: Record<string, number>;
}

export interface SourceCategoriesData {
  categories: SourceCategoryPoint[];
  total: number;
}

// --- Phase 3: Top Headlines (framework-enhanced) ---
export interface HeadlineItem {
  id: string;
  title: string;
  url: string;
  portal_id: string;
  portal_name: string;
  portal_category: string;
  source_tier: number;
  source_tier_label: string;
  published_at: string | null;
  collected_at: string | null;
  sentiment_label: "positive" | "negative" | "neutral";
  sentiment_score: number;
  sentiment_intensity: string;
  source_credibility: number;
  language: string;
  source_type: string;
  repeat_author: boolean;
  reach_tier: string | null;
  author_name: string | null;
}

export interface HeadlinesData {
  tab: string;
  items: HeadlineItem[];
}
```

---

### 6.3 New API Functions (`frontend/src/lib/api.ts`)

Add at the bottom. All existing 14 exports unchanged.

```typescript
export const fetchSentimentTrend = (
  brandId: string,
  params?: { days?: number; date_from?: string; date_to?: string }
) =>
  api
    .get<import("./types").SentimentTrendData>(
      `/dashboard/trends/${brandId}/sentiment`,
      { params }
    )
    .then(r => r.data);

export const fetchSourceCategories = (
  brandId: string,
  params?: { date_from?: string; date_to?: string }
) =>
  api
    .get<import("./types").SourceCategoriesData>(
      `/dashboard/source-categories/${brandId}`,
      { params }
    )
    .then(r => r.data);

export const fetchHeadlines = (
  brandId: string,
  tab: "positive" | "negative" | "trending",
  params?: { limit?: number; date_from?: string; date_to?: string }
) =>
  api
    .get<import("./types").HeadlinesData>(
      `/dashboard/headlines/${brandId}`,
      { params: { tab, ...params } }
    )
    .then(r => r.data);
```

---

### 6.4 Rewritten: `SentimentTrendChart.tsx`

**F08 Annotation system is fully preserved.** All annotation `useQuery`, `useMutation`, form, and `ReferenceLine` logic carries over verbatim.

**New capabilities added:**
- 3 lines (Positive / Neutral / Negative) replacing the single Perception Score line
- Optional Tier 1+2 overlay (dashed lines) — toggle button in card header
- Intensity tooltip (shows Strongly Positive / Mildly Positive etc. for the dominant sentiment on each day)

**New interface:**
```typescript
interface Props {
  brandId: string;
  dateFrom?: string;   // Phase 9 DateRangeContext stub
  dateTo?: string;
  compareFrom?: string;  // Phase 9 compare stub
  compareTo?: string;
}
```

**Internal state:**
```typescript
const [showTier1, setShowTier1] = useState(false);
```

**Data fetching:**
```typescript
const { data: trendData, isLoading: trendLoading } = useQuery({
  queryKey: ["sentiment-trend", brandId, dateFrom, dateTo],
  queryFn: () => fetchSentimentTrend(brandId, { date_from: dateFrom, date_to: dateTo, days: 30 }),
  staleTime: 5 * 60_000,
});
```

**Annotation fetching (unchanged):**
```typescript
const { data: annotations = [] } = useQuery<Annotation[]>({
  queryKey: ["annotations", brandId],
  queryFn: () => fetchAnnotations(brandId),
  staleTime: 60_000,
});
```

**Data formatting:**
```typescript
function formatChartData(
  points: SentimentTrendPoint[],
  window: "1d" | "1h"
): Array<{ date: string; positive: number; negative: number; neutral: number; _iso: string }> {
  return points.map(p => ({
    date: window === "1d"
      ? new Date(p.time).toLocaleDateString("en-IN", { day: "numeric", month: "short" })
      : new Date(p.time).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    positive: p.positive,
    negative: p.negative,
    neutral:  p.neutral,
    _iso: p.time.slice(0, 10),  // for annotation date matching
  }));
}
```

**Tooltip formatter with intensity context:**
```typescript
// Custom tooltip shows: count + dominant intensity for the day
function SentimentTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const pos = payload.find(p => p.dataKey === "positive")?.value ?? 0;
  const neg = payload.find(p => p.dataKey === "negative")?.value ?? 0;
  const neu = payload.find(p => p.dataKey === "neutral")?.value ?? 0;
  const total = pos + neg + neu;
  const dominantScore = total > 0 ? pos / total : 0.5;
  const dominant = pos >= neg && pos >= neu ? "positive"
                 : neg >= pos && neg >= neu ? "negative" : "neutral";
  const { text } = sentimentIntensity(dominant, dominantScore);
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-xl">
      <div className="text-gray-400 mb-1">{label}</div>
      <div className="text-indigo-300 text-[10px] mb-1.5 font-medium">{text}</div>
      <div className="text-green-400">+{pos} positive</div>
      <div className="text-red-400">−{neg} negative</div>
      <div className="text-yellow-400">~{neu} neutral</div>
    </div>
  );
}
```

**Card header with Tier 1 toggle:**
```tsx
<div className="flex items-center justify-between mb-3">
  <div className="text-sm font-semibold text-gray-200">
    Sentiment Trend — {dateFrom ? `${dateFrom.slice(0,10)} to ${(dateTo ?? "now").slice(0,10)}` : "Last 30 Days"}
  </div>
  <div className="flex items-center gap-2">
    <button
      onClick={() => setShowTier1(s => !s)}
      className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
        showTier1
          ? "bg-violet-900/40 border-violet-600 text-violet-300"
          : "border-gray-700 text-gray-500 hover:border-gray-500"
      }`}
      title="Show Tier 1+2 sources only (national + major regional portals)"
    >
      Tier 1+2 only
    </button>
    <button onClick={() => setShowForm(s => !s)} className="text-xs text-indigo-400 hover:text-indigo-300">
      {showForm ? "Cancel" : "+ Annotate"}
    </button>
  </div>
</div>
```

**Recharts structure (3 solid lines + optional 3 dashed Tier 1 overlay):**
```tsx
<ResponsiveContainer width="100%" height={220}>
  <LineChart data={chartData} margin={{ top: 5, right: 16, bottom: 0, left: 0 }}>
    <XAxis dataKey="date" tick={{ fill: "#6b7280", fontSize: 11 }} />
    <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} allowDecimals={false} />
    <Tooltip content={<SentimentTooltip />} />
    <Legend iconSize={8} wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />

    {/* Solid lines — all sources */}
    <Line type="monotone" dataKey="positive" stroke="#22c55e" strokeWidth={2} dot={false} name="Positive" />
    <Line type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2} dot={false} name="Negative" />
    <Line type="monotone" dataKey="neutral"  stroke="#eab308" strokeWidth={2} dot={false} name="Neutral"  />

    {/* Dashed overlay — Tier 1+2 only — only rendered when showTier1=true */}
    {showTier1 && tier1Data.length > 0 && <>
      <Line type="monotone" data={tier1Data} dataKey="positive" stroke="#22c55e" strokeWidth={1}
            strokeDasharray="4 2" dot={false} name="Positive (T1+2)" legendType="none" />
      <Line type="monotone" data={tier1Data} dataKey="negative" stroke="#ef4444" strokeWidth={1}
            strokeDasharray="4 2" dot={false} name="Negative (T1+2)" legendType="none" />
      <Line type="monotone" data={tier1Data} dataKey="neutral"  stroke="#eab308" strokeWidth={1}
            strokeDasharray="4 2" dot={false} name="Neutral (T1+2)"  legendType="none" />
    </>}

    {/* F08 annotation ReferenceLine — preserved exactly */}
    {annotations
      .filter(a => chartDates.has(a.date))
      .map(a => (
        <ReferenceLine key={a.id} x={formattedDateOf(a.date, chartData)} stroke="#f59e0b" strokeDasharray="3 3">
          <Label value={a.label} position="insideTopLeft" fill="#f59e0b" fontSize={10} />
        </ReferenceLine>
      ))}
  </LineChart>
</ResponsiveContainer>
```

**Tier 1 data prep:**
```typescript
const tier1Data = trendData?.points_tier1
  ? formatChartData(trendData.points_tier1, trendData.window)
  : [];
```

**Annotation date resolution helper:**
```typescript
function formattedDateOf(
  isoDate: string,
  chartData: Array<{ date: string; _iso: string }>
): string {
  return chartData.find(d => d._iso === isoDate)?.date ?? isoDate;
}
const chartDates = new Set(chartData.map(d => d._iso));
```

---

### 6.5 New Component: `MentionsBySourceDonut.tsx`

**File:** `frontend/src/components/charts/MentionsBySourceDonut.tsx`

**Framework enhancement:** Each Donut tooltip shows the authority tier distribution for the category, surfacing the Web Framework §1.4 Source Authority Tier concept visually.

**Interface:**
```typescript
interface Props {
  brandId: string;
  dateFrom?: string;
  dateTo?: string;
}
```

**Donut — same `innerRadius` pattern as `SentimentPieChart.tsx`.**

**Tooltip with tier breakdown:**
```typescript
function SourceTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const cat = payload[0].payload as SourceCategoryPoint;
  const td = cat.tier_distribution;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-xl min-w-[160px]">
      <div className="font-semibold text-gray-100 mb-1">{cat.label}</div>
      <div className="text-gray-400 mb-1.5">{formatCount(cat.count)} mentions ({cat.pct}%)</div>
      <div className="text-[10px] text-gray-500 space-y-0.5">
        {td.tier1 > 0 && <div className="text-violet-400">Tier 1 (national): {td.tier1}</div>}
        {td.tier2 > 0 && <div className="text-blue-400">Tier 2 (regional): {td.tier2}</div>}
        {td.tier3 > 0 && <div className="text-gray-400">Tier 3 (trade): {td.tier3}</div>}
        {td.tier4 > 0 && <div className="text-gray-500">Tier 4 (community): {td.tier4}</div>}
        {td.youtube > 0 && <div className="text-red-400">YouTube: {td.youtube}</div>}
      </div>
      <div className="mt-1.5 text-[10px] text-gray-600">
        Avg credibility: {cat.avg_credibility.toFixed(2)}
      </div>
    </div>
  );
}
```

**Legend rows** — each row shows: colour dot + label + count (formatted) + pct + tier label:
```tsx
{cat.avg_credibility >= 0.87 && (
  <span className={`text-[9px] px-1 rounded ${tierBadge(1).bg} ${tierBadge(1).color}`}>Tier 1</span>
)}
```

**Centre label** — total count over the donut hole (same absolute-positioning technique as `SentimentPieChart.tsx`).

**Empty / loading states** — same skeleton pattern (`h-[180px] bg-gray-800/50 animate-pulse rounded-lg`).

---

### 6.6 New Component: `TopHeadlines.tsx`

**File:** `frontend/src/components/TopHeadlines.tsx`

**Framework enhancements over original plan:**
1. Sentiment intensity badge (replaces plain positive/negative/neutral pill)
2. Source Tier badge per headline
3. Repeat-author warning icon on negative headlines
4. Creator vs. Audience grouping on Trending tab
5. High-Reach badge on YouTube items

**Interface:**
```typescript
type HeadlineTab = "positive" | "negative" | "trending";

interface Props {
  brandId: string;
  dateFrom?: string;
  dateTo?: string;
  onViewAll?: (tab: HeadlineTab) => void;
}
```

**Reused existing components:** `SentimentBadge` (F31), `YouTubeIcon` (F29), credibility badge CSS pattern (F33). All imported, not reimplemented.

**Sentiment intensity badge** (replaces plain `SentimentBadge` on headline cards):
```tsx
function IntensityBadge({ item }: { item: HeadlineItem }) {
  const intensity = sentimentIntensity(item.sentiment_label, item.sentiment_score);
  return (
    <span className={`text-[9px] px-1.5 py-0.5 rounded border ${intensity.bg} ${intensity.color} border-current/30`}>
      {item.sentiment_intensity}
    </span>
  );
}
```

**Source Tier badge:**
```tsx
function TierBadge({ tier }: { tier: number }) {
  const tb = tierBadge(tier);
  return (
    <span className={`text-[9px] px-1 rounded ${tb.bg} ${tb.color}`}>
      {tb.label}
    </span>
  );
}
```

**Repeat-author warning:**
```tsx
{item.repeat_author && (
  <span
    title={`${item.author_name ?? "This author"} has published multiple negative articles about this brand`}
    className="text-[9px] text-orange-400 border border-orange-800/50 px-1 rounded"
  >
    ⚠ Repeat critic
  </span>
)}
```

**High-Reach badge (YouTube Framework §4):**
```tsx
{item.reach_tier && item.reach_tier !== "Low" && (
  <span className={`text-[9px] font-medium ${reachBadge(item.reach_tier).color}`}>
    {reachBadge(item.reach_tier).label}
  </span>
)}
```

**Creator vs. Audience grouping on Trending tab:**
When `activeTab === "trending"` and the items list contains both `youtube_video` and `youtube_comment`, render them in two sub-groups with a divider:
```tsx
{activeTab === "trending" && hasYoutube && (
  <>
    <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
      Creator (Videos)
    </div>
    {videoItems.map(item => <HeadlineCard key={item.id} item={item} />)}
    {commentItems.length > 0 && (
      <>
        <div className="text-[10px] text-gray-600 uppercase tracking-wider mt-2 mb-1">
          Audience (Comments)
        </div>
        {commentItems.map(item => <HeadlineCard key={item.id} item={item} />)}
      </>
    )}
  </>
)}
```

**Full headline card layout:**
```
┌─────────────────────────────────────────────────────┐
│  [YT icon/Avatar]  Linked title text (2 lines)      │
│                    [Intensity badge] [Tier badge]    │
│                    Source · Credibility · Date       │
│                    [High Reach] [⚠ Repeat critic]   │
└─────────────────────────────────────────────────────┘
```

**Loading** — 5 skeleton rows. **Empty** — contextual message per tab.

---

### 6.7 Updates to `Overview.tsx`

Only the second-row layout changes. F01–F15 all preserved in their current positions.

**New state + ref:**
```typescript
const [mentionsSentimentFilter, setMentionsSentimentFilter] = useState("");
const mentionsRef = useRef<HTMLDivElement>(null);
```

**New second-row grid:**
```tsx
<div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
  <div className="xl:col-span-2 flex flex-col gap-4">
    <SentimentTrendChart brandId={brandId} />
    <MentionsBySourceDonut brandId={brandId} />
  </div>
  <TopHeadlines
    brandId={brandId}
    onViewAll={(tab) => {
      mentionsRef.current?.scrollIntoView({ behavior: "smooth" });
      setMentionsSentimentFilter(tab === "trending" ? "" : tab);
    }}
  />
</div>
```

**Top Sources card** (F09) — move below this grid, as a standalone card above `IndiaStateMap`.

**MentionsList wrapper with `initialSentiment`:**
```tsx
<div ref={mentionsRef}>
  <MentionsList
    brandId={brandId}
    brandName={brandName}
    portals={data.top_sources.map(s => s.portal_id)}
    topics={data.top_topics}
    states={data.state_breakdown.map(s => s.state)}
    selectable
    syncUrl
    initialSentiment={mentionsSentimentFilter}
  />
</div>
```

**`initialSentiment` in `MentionsList.tsx`:**
```typescript
// Prop addition:
initialSentiment?: string;

// State init (add to existing):
const [sentiment, setSentiment] = useState(
  () => syncUrl ? readParam("sentiment") : (initialSentiment ?? "")
);

// useEffect to react to external changes from Headlines "View All":
useEffect(() => {
  if (initialSentiment !== undefined) {
    setSentiment(initialSentiment);
    setPage(0);
  }
}, [initialSentiment]);
```

**Remove** `data={data.trend}` from `SentimentTrendChart` call. Keep all other existing Overview content.

---

## 7. File Change Summary

### Backend — modify:

| File | Change | Features touched |
|---|---|---|
| `backend/app/ingestion/portals.py` | Add `category` to all portal dicts; add `get_portal_category()`, `get_portal_tier()`, `TIER_LABELS`, `CATEGORY_LABELS`, `CATEGORY_COLORS` | F58, F64 — data addition only |
| `backend/app/storage/influxdb.py` | Add `query_sentiment_counts_trend()` + `_range()` | F63 — existing write functions untouched |
| `backend/app/dashboard/schemas.py` | Add 6 new Pydantic models | Existing 14 unchanged |
| `backend/app/dashboard/router.py` | Add 3 new endpoints + 4 helper functions | 10 existing endpoints untouched |

### Frontend — modify:

| File | Change | Features touched |
|---|---|---|
| `frontend/src/lib/types.ts` | Add 6 new interfaces | Existing 12 unchanged |
| `frontend/src/lib/api.ts` | Add 3 new fetch functions | Existing 14 unchanged |
| `frontend/src/components/charts/SentimentTrendChart.tsx` | Full rewrite — 3 lines + tier toggle + intensity tooltip; **annotations (F08) preserved** | F07 enhanced, F08 kept |
| `frontend/src/pages/Overview.tsx` | New second-row grid; add `mentionsSentimentFilter` state + `mentionsRef`; remove `data={data.trend}` | F01–F15 all preserved |
| `frontend/src/components/mentions/MentionsList.tsx` | Add `initialSentiment` prop + `useEffect`; import `formatCount` from utils | F16–F34 untouched |

### Frontend — create:

| File | Description | Reuses |
|---|---|---|
| `frontend/src/lib/utils.ts` | `formatCount`, `sentimentIntensity`, `tierBadge`, `reachBadge` | Extracted from MentionsList |
| `frontend/src/components/charts/MentionsBySourceDonut.tsx` | Source category donut + tier tooltip | `SentimentPieChart` pattern |
| `frontend/src/components/TopHeadlines.tsx` | Headlines panel — 3 tabs, framework badges | `SentimentBadge`, `YouTubeIcon`, credibility pattern |

**No database schema changes.** InfluxDB already has the fields. Supabase articles table unchanged.

---

## 8. API Contract Summary

```
GET /dashboard/trends/{brand_id}/sentiment
  Query:    days=30 | date_from=ISO&date_to=ISO
  Auth:     brand read role
  Response: {
    points:       [{time, positive, negative, neutral}],
    points_tier1: [{time, positive, negative, neutral}],   // Tier 1+2 only
    window:       "1d" | "1h"
  }

GET /dashboard/source-categories/{brand_id}
  Query:    date_from?, date_to?
  Auth:     brand read role
  Response: {
    categories: [{category, label, color, count, positive, negative, neutral,
                  pct, avg_credibility, tier_distribution}],
    total: int
  }

GET /dashboard/headlines/{brand_id}
  Query:    tab="positive"|"negative"|"trending", limit=5, date_from?, date_to?
  Auth:     brand read role
  Response: {
    tab: string,
    items: [{id, title, url, portal_id, portal_name, portal_category,
             source_tier, source_tier_label, published_at, collected_at,
             sentiment_label, sentiment_score, sentiment_intensity,
             source_credibility, language, source_type,
             repeat_author, reach_tier, author_name}]
  }
```

---

## 9. Implementation Order

```
Step 1  portals.py         — category field + get_portal_category() + get_portal_tier()
Step 2  influxdb.py        — query_sentiment_counts_trend() functions
Step 3  schemas.py         — 6 new Pydantic models
Step 4  router.py          — 4 helper functions + 3 new endpoints
         ↓ deploy to Railway; smoke-test 3 endpoints with curl (Section 10A)
Step 5  utils.ts           — formatCount, sentimentIntensity, tierBadge, reachBadge
Step 6  types.ts           — 6 new interfaces
Step 7  api.ts             — 3 new fetch functions
Step 8  SentimentTrendChart.tsx — rewrite (deps: 5–7; test annotations survive)
Step 9  MentionsBySourceDonut.tsx — new (deps: 5–7)
Step 10 TopHeadlines.tsx   — new (deps: 5–7; reuses SentimentBadge, YouTubeIcon)
Step 11 MentionsList.tsx   — add initialSentiment prop; import formatCount from Step 5
Step 12 Overview.tsx       — wire all three, update layout, add state + ref
         ↓ visual QA against full checklist (Section 10B)
```

---

## 10. Testing

### 10A — Backend smoke tests

```bash
TOKEN="<JWT from browser DevTools>"
BASE="https://<railway-url>"
BRAND="<brand_id>"

# Sentiment trend — verify points AND points_tier1 returned
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/dashboard/trends/$BRAND/sentiment?days=30" \
  | jq '{window, all_count: (.points | length), tier1_count: (.points_tier1 | length)}'

# Source categories — verify pcts sum ~100 and tier_distribution present
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/dashboard/source-categories/$BRAND" \
  | jq '[.categories[].pct] | add, .categories[0].tier_distribution'

# Headlines positive — all sentiment_label must be "positive", check intensity
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/dashboard/headlines/$BRAND?tab=positive&limit=5" \
  | jq '[.items[] | {label: .sentiment_label, intensity: .sentiment_intensity, tier: .source_tier_label}]'

# Headlines negative — check repeat_author detection
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/dashboard/headlines/$BRAND?tab=negative&limit=5" \
  | jq '[.items[] | {title: .title[:40], repeat: .repeat_author, intensity: .sentiment_intensity}]'

# Headlines trending — check reach_tier on YouTube items
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/dashboard/headlines/$BRAND?tab=trending&limit=5" \
  | jq '[.items[] | select(.portal_category == "youtube") | {title: .title[:40], reach_tier}]'
```

### 10B — Visual QA checklist

**Sentiment Trend Chart:**
- [ ] Three coloured lines: green (Positive), red (Negative), yellow (Neutral)
- [ ] "Tier 1+2 only" toggle button visible in card header
- [ ] Toggling adds dashed overlay lines for Tier 1+2 filtered data
- [ ] Tooltip shows count per sentiment + intensity label (e.g., "Strongly Negative")
- [ ] X-axis: day labels ("1 Jun", "8 Jun") for 30-day view
- [ ] F08 annotation "+" button still present and functional
- [ ] Annotations still render as amber dashed ReferenceLine with labels
- [ ] Annotation chips list still appears below chart
- [ ] Skeleton shown during load; no layout shift

**Mentions by Source Donut:**
- [ ] Centre shows total count ("24.7K")
- [ ] Legend: colour dot + label + formatted count + pct + tier badge
- [ ] Hover tooltip shows tier distribution breakdown (Tier 1: N, Tier 2: N, etc.)
- [ ] YouTube slice appears in red; avg_credibility shows 0 or N/A tier label
- [ ] Percentages sum ~100%
- [ ] Empty state message shown gracefully

**Top Headlines Panel:**
- [ ] "Top Positive" default tab; tab bar visible
- [ ] Tab switching uses `keepPreviousData` — no flash to empty
- [ ] Each headline card shows: avatar, title (linked), intensity badge, tier badge, source, date
- [ ] "Top Positive" → badges show "Strongly Positive" or "Mildly Positive" (not just "positive")
- [ ] "Top Negative" → badges show "Strongly Negative" or "Mildly Negative"
- [ ] Repeat-author warning "⚠ Repeat critic" visible on negative headlines where applicable
- [ ] YouTube headlines show YouTube icon avatar
- [ ] YouTube items with high view count show "High Reach" badge
- [ ] "Trending" tab — YouTube video items grouped under "Creator (Videos)" sub-header
- [ ] "Trending" tab — YouTube comment items grouped under "Audience (Comments)" sub-header
- [ ] "View All" on any tab scrolls to Mention Explorer
- [ ] "View All" on "Top Positive" → Positive filter pill selected in Explorer
- [ ] "View All" on "Trending" → no sentiment filter applied
- [ ] 5 skeleton rows shown during tab switch
- [ ] All titles open in new tab

**Overview layout preservation:**
- [ ] F01 Brand header + last updated — at top, unchanged
- [ ] F02 Pipeline running banner — visible when running
- [ ] F03 Perception Score KPI — present
- [ ] F04 Total Mentions KPI — present
- [ ] F05 YouTube KPI (if data) — present
- [ ] F06 Sentiment Pie chart — in first row, unchanged
- [ ] F09 Top Sources list — below new 3-panel row (repositioned)
- [ ] F10 India State Map — below Top Sources, unchanged
- [ ] F11 State click → Mention Explorer filter — works
- [ ] F12–F34 Mention Explorer all filters — fully functional
- [ ] F13 Topics + F14 Keywords tag clouds — below Mention Explorer
- [ ] F15 Email alerts (admin) — visible at bottom for admin users

---

## 11. Framework Gaps — Tracked for Future Phases

All framework requirements that cannot be addressed in Phase 3 without NLP pipeline or data model changes:

| Requirement | Framework | Proposed Phase | Notes |
|---|---|---|---|
| Headline vs. body sentiment — analysed separately | Web §1.3 | Phase 7 | Requires storing 2 scores per article |
| Quote extraction and attribution | Web §1.3 | Phase 7 | NER upgrade needed |
| Editorial tone classification | Web §1.3 | Phase 7 | New NLP classification |
| Full 5-point (−2 to +2) rescoring in NLP | Both | Phase 7 | Phase 3 maps existing; full rescore in Phase 7 |
| Syndication chain deduplication (wire service) | Web §1.4 | Phase 6 | Needs article clustering by content similarity |
| Formal `tier` field in portals.py | Web §1.4 | Phase 4 | Phase 3 derives from credibility; Phase 4 formalises |
| Creator classification (Journalist/Influencer/etc.) | YouTube §7 | Phase 6 | New data field on YouTube articles |
| Owned vs. Earned vs. Public pillar split | YouTube §Pillars | Phase 8 | Sidebar destination pages (Phase 1+8) |
| Comment quality pre-filter (ignore low-info comments) | YouTube §5 | Phase 7 | Ingestion-level change |
| Confidence gate / human review queue | Both | Phase 8 | Requires new review workflow |
| Full Brand Risk Score (log-norm reach × engagement × decay) | YouTube §1 | Phase 6 | Phase 3 shows reach_tier as proxy |
| Journalist CRM / beat tracking database | Web §1.7 | Phase 8 | Phase 3 does repeat-author flag; Phase 8 adds full CRM |
| Regulatory source escalation | Web §1.7 | Phase 8 | Requires source metadata tagging |
| Review platform monitoring | Web Part 2 | Phase 5 | MouthShut, JustDial, Trustpilot, Google Business |
| Star rating vs. text divergence | Web §2.3 | Phase 5 | With review site data |
| Review clustering (3+ same issue, 14 days) | Web §2.6 | Phase 5 | With review site data |
| Blog / long-form web monitoring | Web Part 3 | Phase 8 | |
| Google search rank tracking | Web §2.4 | Phase 8 | External API required |
| Competitor benchmarking SOV | YouTube §6 | Phase 7 | Competitor data model |
| Audit trail + data provenance | Both | Phase 9 | Schema additions |
| Per-language accuracy disclosure | Both | Phase 9 | Reporting layer |
