# New Dashboard Implementation Plan

> **Reference screenshots:** `references/screenshots/New Screen/Overall view 1.jpg`, `2.jpg`, `3.jpg`
> **Created:** 2026-06-22
> **Status:** Ready for implementation — no approval gates

---

## 1. What We Are Building

Three full-viewport screens that scroll vertically with CSS Scroll Snap (parallax-style). The left sidebar is static and unchanged in position. Each screen fills exactly one browser viewport — no overflow, no leakage. Users scroll down through the three screens; the sidebar never moves.

### Screen Map

| Screen | Viewport | Sections |
|--------|----------|----------|
| **Screen 1** | Top | 5 KPI cards · AI Executive Summary + Overall Sentiment Trend · Mentions by Source (5 source cards) |
| **Screen 2** | Middle | Top Issues/Themes · Top Influential Sources · Top Negative Mentions · Reputation Risk Monitor · Geographic Sentiment Heatmap · Top Brand Advocates |
| **Screen 3** | Bottom | News & RSS Mentions drill panel · Review Site Analysis panel · Competitor Comparison (tabbed) |

---

## 2. Architecture Change: Scroll Model

### Current
```
App.tsx
└── <div class="flex h-screen overflow-hidden">
    ├── <Sidebar />                     ← static
    └── <main class="flex-1 overflow-hidden">   ← no scroll, compact single screen
        └── <Overview />                ← 4 fixed rows, h-full
```

### New
```
App.tsx
└── <div class="flex h-screen overflow-hidden">
    ├── <Sidebar />                     ← static (unchanged)
    └── <main class="flex-1 overflow-y-scroll snap-y snap-mandatory scroll-smooth">
        ├── <Screen1 class="snap-start h-screen shrink-0">   ← viewport 1
        ├── <Screen2 class="snap-start h-screen shrink-0">   ← viewport 2
        └── <Screen3 class="snap-start h-screen shrink-0">   ← viewport 3
```

**Tailwind classes for scroll container:** `overflow-y-scroll snap-y snap-mandatory scroll-smooth`
**Tailwind classes for each screen section:** `h-screen w-full shrink-0 snap-start overflow-hidden`

No external libraries needed. CSS Scroll Snap is natively supported in all modern browsers and Tailwind has first-class support.

---

## 3. Sidebar Changes

### Current nav items → New nav items

| Current Label | New Label | Change |
|---------------|-----------|--------|
| Executive Overview | Executive Overview | No change |
| News & RSS | News & RSS | No change |
| YouTube *(links to overview)* | YouTube Analytics | Own page |
| Blogs & Portals | Blogs & Portals | No change |
| Review Sites *(links to overview)* | Review Sites | Own page |
| Social & Forums *(links to sources)* | Social & Forums | Own page |
| Competitors *(links to overview)* | Competitor Intel | Own page |
| Reports *(links to topics)* | Reports | No change |
| Alerts & Risks *(links to overview)* | Alerts Center | Own page |
| Journalists | *(moved to Mentions Monitor)* | Merged |
| Channel Settings | Settings | Rename |
| Review Queue | Review Queue | No change (admin only) |
| User Management | User Management | No change (admin only) |
| — | **Mentions Monitor** | NEW |
| — | **Influencers** | NEW (stub for now) |

### Sidebar structural change
- Remove "Monitoring For" brand label from bottom of sidebar
- Add **Date Range** picker at sidebar bottom: `May 1 – May 31, 2025 ▾` with comparison period line `vs Apr 1 – Apr 30, 2025`
- Subtitle: change "Media Sentiment Dashboard" → "Reputation Intelligence"
- Last Updated stamp moves to footer bar of each screen (Screen 2 bottom)

### File to modify: `frontend/src/components/Sidebar.tsx`
- Update `NAV_ITEMS` array with new labels, IDs, and tab mappings
- Add Date Range display section at bottom (receives `dateLabel` and `comparePeriod` props from App)
- Update subtitle string

---

## 4. Global Top Bar (per screen)

Each screen has its own top bar strip (not a shared header component). The App-level top bar in `App.tsx` is removed; each screen manages its own header row.

**Screen 1 top bar content:**
- Left: "Executive Overview" (h2) + "Real-time reputation intelligence across all digital media" (subtitle)
- Right: Date range picker dropdown (`May 1 – May 31, 2025 ▾`) + Download icon + Save icon + Settings icon + **Filters** button (blue border pill)

**Date range picker dropdown** (replaces current 7d/30d/90d buttons):
- A single dropdown showing the selected range (e.g. "May 1 – May 31, 2025")
- Click opens a calendar or preset panel — presets: Last 7 days, Last 30 days, Last 90 days, Custom range
- Currently `days` state (7/30/90) + `customFrom`/`customTo` in Overview.tsx — keep same state, just change UI control

---

## 5. Screen 1 — Detailed Layout

```
┌─────────────────────────────────────── TOP BAR ────────────────────────────────────────┐
│ Executive Overview    Real-time reputation intelligence...    [Date Range ▾] ⬇ 🔖 ⚙ Filters│
├────────────────────────────────────── KPI ROW ─────────────────────────────────────────┤
│ [Unified Rep Index 72/100] [Total Mentions 48.7K] [Share of Voice donut 32%]           │
│ [Reputation Risk Score Medium 58] [Total Reach 215.6M]                                  │
├──────────────────── AI EXECUTIVE SUMMARY ─────────────────────────┬── SENTIMENT TREND ─┤
│ ✦ AI Executive Summary                                            │ Overall Sentiment  │
│ ┌──────────────┬──────────────┬──────────────────────────────┐   │ Trend chart        │
│ │ What changed?│ Why?         │ What should we do?           │   │ Positive/Neutral/  │
│ │ (body text)  │ (body text)  │ • Bullet 1                   │   │ Negative area chart│
│ │              │              │ • Bullet 2                   │   │ (May 1–31)         │
│ │              │              │ • Bullet 3                   │   │                    │
│ └──────────────┴──────────────┴──────────────────────────────┘   │                    │
│ [View Full Insights →]                                            │                    │
├────────────────────────────── MENTIONS BY SOURCE ──────────────────────── View all →  ─┤
│ [News & RSS 12.6K ↑20.5%] [YouTube 8.9K ↑12.3%] [Blogs 7.3K] [Reviews 13.8K] [Forums 6.1K]│
│  Negative 19% ~~~          Negative 22%            Negative 16%   Rating 3.6/5  Neg 24% │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 KPI Cards Row (5 cards)

Maps to current `Row 1` in Overview.tsx. **Data mapping:**

| New Card | New Metric | Current Source | New Source |
|----------|-----------|----------------|------------|
| Unified Reputation Index | 72/100 + "Good" label + 8.6% trend + sparkline | `kpi.perception_score` | `kpi.perception_score` (divide by 100, add label thresholds) |
| Total Mentions | 48.7K + 15.4% delta + sparkline | `kpi.total` + `kpi.mentions_delta_pct` | Same |
| Share of Voice | Donut chart + 32% label + 3.2% delta | `data.competitor_entities` (SoV exists) | Existing `CompetitorShareOfVoice` data |
| Reputation Risk Score | "Medium" text + 58/100 + 12.1% + sparkline | `kpi.perception_score` inverted | Same (derived: risk = 100 - perception_score) |
| Total Reach | 215.6M + 18.7% delta + sparkline | `data.total_reach` (NEW) | New backend field in overview response |

**Component:** Modify `KPICard` to support:
- `variant="sparkline"` — shows mini line chart below value (currently not implemented)
- `variant="donut"` — shows mini donut chart (Share of Voice card)
- `label="Good" | "Medium" | "High"` — text label below value for risk/reputation cards
- `labelColor` — green for Good, amber for Medium, red for High

**File:** `frontend/src/components/cards/KPICard.tsx`

### 5.2 AI Executive Summary

**NEW component:** `frontend/src/components/AIExecutiveSummary.tsx`

Three-column panel with:
- Left col: "What changed?" — paragraph of text from API
- Middle col: "Why?" — paragraph of text from API
- Right col: "What should we do?" — bulleted list from API
- "✦ AI Executive Summary" header with sparkle icon
- "View Full Insights →" button (links to Reports page)

**New backend endpoint required:** `GET /dashboard/ai-summary/{brand_id}?days=30`

Response shape:
```json
{
  "what_changed": "Negative sentiment increased 18% this month...",
  "why": "A spike in negative coverage from major news portals...",
  "actions": [
    "Address delivery complaints urgently",
    "Respond to high impact negative articles",
    "Leverage positive customer stories"
  ],
  "generated_at": "2025-06-01T10:30:00Z"
}
```

Backend logic: Call Gemini with a prompt summarising the brand's top issues, top negative articles, sentiment delta, and competitor context from the past N days. Cache response for 1 hour (Redis key `ai_summary:{brand_id}:{days}`).

**File:** `backend/app/dashboard/ai_summary.py` (new)
**Route:** `backend/app/main.py` — add `/dashboard/ai-summary/{brand_id}`

### 5.3 Overall Sentiment Trend (right side of AI summary row)

**Existing component:** `SentimentTrendChart` — reuse as-is. No changes needed. Place in right column of the AI Summary + Trend row (roughly 60/40 split).

### 5.4 Mentions by Source Cards

**Current:** `MentionsBySourceDonut` (a donut chart)
**New:** 5 horizontal source cards, each showing: source icon + name + count + delta% + "Negative X%" tag + mini sparkline

**New component:** `frontend/src/components/MentionsBySourceCards.tsx`

5 source categories:
1. News & RSS — icon: newspaper (red)
2. YouTube — icon: play triangle (red)
3. Blogs & Portals — icon: grid (green)
4. Review Sites — icon: star (amber)
5. Forums & Communities — icon: chat (indigo)

**Data from existing:** `fetchOverview()` already returns `kpi.by_source` or it can be derived from `data.top_sources`. If not already aggregated by source_type, add `by_source_type` to the overview response.

**Backend change:** Add `by_source_type` to `get_overview()` response:
```json
"by_source_type": {
  "news": {"count": 12600, "delta_pct": 20.5, "negative_pct": 19, "sparkline": [...]},
  "youtube": {"count": 8900, "delta_pct": 12.3, "negative_pct": 22, "sparkline": [...]},
  "blog": {"count": 7300, "delta_pct": 9.8, "negative_pct": 16, "sparkline": [...]},
  "google_review": {"count": 13800, "delta_pct": 23.6, "avg_rating": 3.6, "sparkline": [...]},
  "reddit_post": {"count": 6100, "delta_pct": 14.2, "negative_pct": 24, "sparkline": [...]}
}
```

**File:** `backend/app/dashboard/overview.py` — extend `get_overview()` to group by `source_type`

---

## 6. Screen 2 — Detailed Layout

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ ┌─── TOP ISSUES / THEMES ──────────┐ ┌── TOP INFLUENTIAL SOURCES ──┐ ┌─ TOP NEGATIVE ─┐ │
│ │ Negative ● Positive ●            │ │ (by Impact Score)           │ │ Mentions       │ │
│ │ 1. Delivery/Logistics  35% ↑6%   │ │ 1. Economic Times    95 Neg │ │ [Card 1]       │ │
│ │ 2. Customer Service    22% ↑4%   │ │ 2. Business Standard 90 Neg │ │ [Card 2]       │ │
│ │ 3. Product Quality     18% ↑3%   │ │ 3. TechCrunch India  78 Neu │ │ [Card 3]       │ │
│ │ 4. Pricing             12% ↓1%   │ │ 4. YouTube–TechGuru  72 Pos │ │ View all →     │ │
│ │ 5. Return/Refund        8% ↑2%   │ │ 5. Customer Review   68 Neg │ │                │ │
│ └──────────────────────────────────┘ │ View all →                  │ └────────────────┘ │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──── REPUTATION RISK MONITOR ──────────────────┐ ┌─ GEO HEATMAP ──┐ ┌─ ADVOCATES ──┐ │
│ │   [Semi-circle gauge 58/100 Medium Risk]      │ │ India map      │ │ TechGuru ✓   │ │
│ │   Risk Level: Low(0-39) Med(40-69) High(70+)  │ │ N:75 Pos       │ │ Anita V. ✓   │ │
│ │   Risk Drivers:                               │ │ S:68 Pos       │ │ Ind. Insid. ✓│ │
│ │   Surge in delivery complaints      High      │ │ E:60 Neu       │ │              │ │
│ │   Negative news from publications   High      │ │ W:45 Neg       │ │              │ │
│ │   Increase in negative reviews      Medium    │ │                │ │              │ │
│ │   Social media backlash             Medium    │ └────────────────┘ └──────────────┘ │
├────────────────────────────────── FOOTER BAR ─────────────────────────────────────────┤
│ All times are in IST │ Data aggregated from 500+ sources... │ Last updated: ... ↺    │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Top Issues / Themes

**Existing component:** `TopIssuesTable` — extend to match new visual.

**Changes needed:**
- Add `Negative ●` / `Positive ●` toggle pills at top right (currently exists as Clusters|Categories toggle)
- Replace compact table rows with horizontal bar + percentage + delta arrow pattern
- Issue category icon badges (colored circles: red for delivery/service, blue for product, amber for pricing)
- Keep existing data: `GET /dashboard/issue-categories/{brand_id}` — already implemented

**File:** `frontend/src/components/TopIssuesTable.tsx`

### 6.2 Top Influential Sources

**NEW component:** `frontend/src/components/TopInfluentialSources.tsx`

Shows top 5 sources ranked by `impact_score` (not just mention count). Each row: rank number + source icon/avatar + source name + impact score badge + sentiment label (Negative/Neutral/Positive).

**New backend endpoint:** `GET /dashboard/top-sources/{brand_id}?days=30`

`impact_score` formula: `reach × |sentiment_score| × source_credibility` — already have all three fields in articles table.

Response:
```json
{
  "sources": [
    {"portal_name": "Economic Times", "impact_score": 95, "sentiment": "negative", "icon_url": null},
    {"portal_name": "Business Standard", "impact_score": 90, "sentiment": "negative", "icon_url": null},
    ...
  ]
}
```

**File:** `backend/app/dashboard/sources.py` — add `get_top_influential_sources()`
**Route:** add to `backend/app/main.py`

### 6.3 Top Negative Mentions (High Impact)

**NEW component:** `frontend/src/components/TopNegativeMentions.tsx`

Shows top 3 high-impact negative articles. Each card: headline (truncated) + source name + date + Impact score badge + "Negative" sentiment tag.

**Data from existing:** `fetchMentions()` endpoint already exists — filter `sentiment=negative`, sort by `reach desc`, take top 3.

No new backend endpoint needed — extend existing `/dashboard/mentions/{brand_id}` call with `?sentiment=negative&sort=reach&limit=3`.

**File:** `frontend/src/components/TopNegativeMentions.tsx`

### 6.4 Reputation Risk Monitor

**NEW component:** `frontend/src/components/ReputationRiskGauge.tsx`

Semi-circular gauge chart showing 0–100 risk score.
- Uses SVG arc path (no chart library needed, or Recharts RadialBarChart)
- Colors: green (0–39 Low), amber (40–69 Medium), red (70–100 High)
- Needle/pointer at current score
- Score text: "58/100" + "Medium Risk" label

**Risk Drivers table** below gauge:
- Pull from existing alert configs + top negative topics
- 4 rows: driver name + severity (High/Medium/Low) color badge
- Drivers derived from: alerts table + `issue_categories` data (top negative category → High if >25%, Medium if >10%)

**Data sources:**
- Score: `kpi.perception_score` inverted (risk = 100 - perception_score)
- Drivers: `GET /dashboard/risk-drivers/{brand_id}` (NEW lightweight endpoint)

**Backend:** `backend/app/dashboard/risk.py`
```python
def get_risk_drivers(brand_id: str, days: int = 30) -> dict:
    # Pull top 4 negative signals: top issue category + alerts + review rating + media volume
    # Return list of {driver: str, severity: "High" | "Medium" | "Low"}
```

### 6.5 Geographic Sentiment Heatmap

**Existing component:** `IndiaStateMap` — reuse. The current choropleth already shows state-level sentiment.

**Visual adjustment needed:** The new design shows 4 regional quadrants (North/South/East/West) with numeric scores, not individual states. Add a `variant="regions"` mode to `IndiaStateMap` that aggregates states into 4 zones with a colored overlay.

**State groupings:**
- North: JK, HP, PB, HR, UK, UP, RJ, DL, CH
- South: TN, KL, AP, TS, KA, GA
- East: WB, OD, JH, BR, AS, NE states
- West: MH, GJ, MP, CG

**File:** `frontend/src/components/charts/IndiaStateMap.tsx`

### 6.6 Top Brand Advocates

**NEW component:** `frontend/src/components/TopBrandAdvocates.tsx`

Shows top 3 positive influencers/sources. Each row: avatar circle + name + type (YouTube/Blogger/etc) + follower count + "Positive" badge.

**New backend endpoint:** `GET /dashboard/top-advocates/{brand_id}?days=30`

Derives from existing data: articles with `sentiment_label = 'positive'` and `source_type IN ('youtube_video', 'blog', 'reddit_post')`, grouped by author/portal, sorted by reach_metadata follower count or reach.

**File:** `backend/app/dashboard/advocates.py`

### 6.7 Screen 2 Footer Bar

Static bottom strip across full width:
- Left: "All times are in IST"
- Center: "Data aggregated from X sources including News, RSS, YouTube, Blogs, Review Sites, Forums & Social Media" (count from `fetchOverview()` portal count)
- Right: "Last updated: {date} {time} ↺" with refresh icon that triggers pipeline

**File:** `frontend/src/components/DashboardFooterBar.tsx` (new, used by Screen 2)

---

## 7. Screen 3 — Detailed Layout

```
┌───────────────────────── LEFT HALF ──────────────────────────┬──────── RIGHT HALF ──────┐
│ ┌── News & RSS Mentions ─────────────────────────────────┐   │ Competitor Comparison     │
│ │ Breadcrumb: Exec Overview › News & RSS Mentions        │   │ Breadcrumb: Exec Ov › CC  │
│ │ [Total 12.6K↑20.5%] [Pos 2.8K(22%)] [Neu 7.4K(59%]  │   │ [SoV] [Sentiment] [Topics]│
│ │ [Neg 2.4K(19%)] [Reach 85.4M↑21%]                    │   │ Last 30 days ▾   Export   │
│ │                                                        │   │                           │
│ │ All Mentions table ▾ Filters  Export                  │   │ Sentiment Comparison       │
│ │ [Headline | Publication | Date | Sentiment | Reach]   │   │ [stacked horizontal bars]  │
│ │ Row 1                                                 │   │ Our Brand  72% □ 7% 21%   │
│ │ Row 2                                                 │   │ Competitor A...            │
│ │ Row 3                                                 │   │ Competitor B...            │
│ │ Row 4                                                 │   │ Competitor C...            │
│ │ Row 5                            ← 1 2 3...50 →      │   │                           │
│ └────────────────────────────────────────────────────────┘   │ Share of Voice donut      │
│                                                              │ [donut 32% Our Brand]     │
│ ┌── Review Site Analysis ────────────────────────────────┐   │                           │
│ │ [Total 13.8K] [Avg 3.6/5] [Pos 5.2K(38%)] [Neg 5.5K]│   ├───────────────────────────┤
│ │ Rating Trend chart | Top Review Themes bar chart      │   │ ┌─ Drill-Down Journey ───┐ │
│ │ View all reviews →                                    │   │ │ Exec → Source → Mention│ │
│ └────────────────────────────────────────────────────────┘   │ │ → Insights & Action    │ │
│                                                              │ └───────────────────────┘ │
└──────────────────────────────────────────────────────────────┴───────────────────────────┘
```

### 7.1 News & RSS Mentions Panel (Screen 3, left top)

**Existing component:** `MentionsList` — repurpose as an embedded panel (not a full-screen detail overlay).

**Changes:**
- Add breadcrumb header: "Executive Overview › News & RSS Mentions"
- Add KPI strip above the table: Total / Positive (count + %) / Neutral (count + %) / Negative (count + %) / Total Reach
- These KPI values filter to `source_type IN ('news', 'blog', 'rss')` only — from `by_source_type` data added in §5.4
- Filters + Export buttons in header row (already exist in `MentionsList`)
- Table shows 5 rows by default with pagination (already exists)

**File:** `frontend/src/components/NewsRSSMentionsPanel.tsx` (thin wrapper around `MentionsList` with source pre-filter and KPI strip)

### 7.2 Review Site Analysis Panel (Screen 3, left bottom)

**Existing component:** `ReviewSitesSummary` — extend significantly.

**Changes:**
- Add breadcrumb header: "Executive Overview › Review Site Analysis"
- Add KPI strip: Total Reviews + Avg Rating + Positive (4-5★) + Neutral (3★) + Negative (1-2★)
- Add Rating Trend line chart (already have `SentimentTrendChart` filtered to review sources; adapt or create `RatingTrendChart`)
- Add Top Review Themes horizontal bar chart (already have topics data from review sources)
- "View all reviews →" link that scrolls to News & RSS panel filtered to `source_type=google_review`

**File:** `frontend/src/components/ReviewSiteAnalysisPanel.tsx`

### 7.3 Competitor Comparison (Screen 3, right)

**Existing component:** `CompetitorShareOfVoice` — extend with tabs.

**Three tabs:**
1. **Share of Voice** — current donut chart (Total 150.2K, Our Brand 32%, Competitor A 27% etc)
2. **Sentiment Comparison** — horizontal stacked bar chart: for each competitor, show % Positive / % Neutral / % Negative
3. **Topics Comparison** — top 5 issue categories for Our Brand vs top competitor (two-column comparison)

**New backend endpoint for tab 2:** `GET /dashboard/competitor-sentiment/{brand_id}?days=30`

Response:
```json
{
  "brands": [
    {"name": "Our Brand", "positive_pct": 72, "neutral_pct": 7, "negative_pct": 21},
    {"name": "Competitor A", "positive_pct": 68, "neutral_pct": 6, "negative_pct": 26},
    ...
  ]
}
```

This requires competitor articles to be tagged with `brand_id` of competitor brands. Data already exists if competitors are tracked as separate brands in the system; otherwise derive from `entities` field mentions.

**Last 30 days dropdown + Export button** in tab bar header — hook into same `days` state.

**File:** `frontend/src/components/CompetitorComparison.tsx` (new, replaces `CompetitorShareOfVoice` on this screen)

### 7.4 Drill-Down Journey (Screen 3, right bottom)

Static informational panel. No data, no interactivity.

```
Executive Overview → Source Level → Mention Level → Insights & Action
High level snapshot    Deep dive      Article/Review   Take action & track
```

**File:** Inline JSX within Screen 3 component. No separate component needed.

---

## 8. New Backend Endpoints Summary

| Priority | Endpoint | File | Complexity | Data Source |
|----------|----------|------|------------|-------------|
| P0 (Screen 1) | `GET /dashboard/overview/{brand_id}` — extend with `by_source_type`, `total_reach` | `overview.py` | Low | articles grouped by source_type |
| P1 (Screen 1) | `GET /dashboard/ai-summary/{brand_id}` | `ai_summary.py` (new) | High | Gemini LLM + cached |
| P2 (Screen 2) | `GET /dashboard/top-sources/{brand_id}` | `sources.py` (extend) | Low | articles grouped by portal, sorted by impact_score |
| P3 (Screen 2) | `GET /dashboard/risk-drivers/{brand_id}` | `risk.py` (new) | Medium | issue_categories + alerts table |
| P4 (Screen 2) | `GET /dashboard/top-advocates/{brand_id}` | `advocates.py` (new) | Low | positive articles by author/portal, sorted by reach |
| P5 (Screen 3) | `GET /dashboard/competitor-sentiment/{brand_id}` | `competitors.py` (new) | Medium | articles for competitor entities |

---

## 9. New Frontend Components Summary

| Component | Status | Source → Target | Complexity |
|-----------|--------|-----------------|------------|
| `KPICard` (extended) | Modify | Add sparkline + donut variants | Medium |
| `AIExecutiveSummary` | New | — | Medium |
| `MentionsBySourceCards` | New | Replaces `MentionsBySourceDonut` | Low |
| `ReputationRiskGauge` | New | — | Medium |
| `TopInfluentialSources` | New | — | Low |
| `TopNegativeMentions` | New | — | Low |
| `TopBrandAdvocates` | New | — | Low |
| `DashboardFooterBar` | New | — | Low |
| `CompetitorComparison` | New | Extends `CompetitorShareOfVoice` | Medium |
| `NewsRSSMentionsPanel` | New | Wraps `MentionsList` | Low |
| `ReviewSiteAnalysisPanel` | New | Extends `ReviewSitesSummary` | Medium |
| `IndiaStateMap` (extended) | Modify | Add `variant="regions"` mode | Low |
| `TopIssuesTable` (extended) | Modify | New visual style, keep data | Low |
| `Sidebar` | Modify | New nav items + date range | Low |

**Components fully reused without change:**
- `SentimentTrendChart` — Screen 1
- `MentionsList` — used inside `NewsRSSMentionsPanel`
- `TopHeadlines` — can remain as fallback on Screen 2 if needed
- `EditorialToneChart` — move to Journalist Coverage or Reports page

---

## 10. Phased Execution Order

### Phase A — Scroll Infrastructure (no data changes)
1. Modify `App.tsx`: change `main` element from `overflow-hidden` to `overflow-y-scroll snap-y snap-mandatory scroll-smooth`
2. Create `pages/DashboardScreen1.tsx`, `DashboardScreen2.tsx`, `DashboardScreen3.tsx` — each with `h-screen shrink-0 snap-start overflow-hidden` wrapper
3. Move current Overview content into Screen 1 as a temporary stub; Screens 2 & 3 show placeholder text
4. Verify scroll snap behavior — screens must lock exactly to viewport on scroll
5. Verify sidebar remains static during scroll

### Phase B — Sidebar & Top Bar
1. Update `Sidebar.tsx`: new nav items, "Reputation Intelligence" subtitle, Date Range display at bottom
2. Remove App.tsx top bar (date pickers, pipeline status) — move into Screen 1 header
3. Add `Filters` pill button (opens a filter panel — stub for now, wire up later)
4. Add Download / Save / Settings icon buttons to Screen 1 top bar (Download = existing CSV export)

### Phase C — Screen 1 Rebuild
1. Extend `KPICard` with sparkline + donut + label variants
2. Extend backend `get_overview()` with `by_source_type` + `total_reach`
3. Build new 5-card KPI row in `DashboardScreen1.tsx` using extended `KPICard`
4. Build `AIExecutiveSummary` component (stub with static text first, wire to API in Phase F)
5. Place `SentimentTrendChart` in right column of AI Summary row
6. Build `MentionsBySourceCards` component (5 source cards with counts + delta + sparkline)
7. Remove `MentionsBySourceDonut` from Screen 1

### Phase D — Screen 2 Rebuild
1. Extend `TopIssuesTable` with new visual (horizontal bars, Negative/Positive toggle)
2. Build `TopInfluentialSources` component (static then wire to new endpoint)
3. Build `TopNegativeMentions` component (wire to existing mentions endpoint with filters)
4. Build `ReputationRiskGauge` (SVG semi-circle + risk drivers table)
5. Extend `IndiaStateMap` with `variant="regions"` mode
6. Build `TopBrandAdvocates` component
7. Build `DashboardFooterBar`
8. Wire all into `DashboardScreen2.tsx`

### Phase E — Screen 3 Rebuild
1. Build `NewsRSSMentionsPanel` (wrapper around `MentionsList` + KPI strip + breadcrumb)
2. Build `ReviewSiteAnalysisPanel` (extend `ReviewSitesSummary` + rating trend + themes bar)
3. Build `CompetitorComparison` with 3 tabs (SoV + Sentiment Comparison + Topics)
4. Wire all into `DashboardScreen3.tsx`

### Phase F — New Backend Endpoints
1. `GET /dashboard/top-sources/{brand_id}` — impact score ranking
2. `GET /dashboard/risk-drivers/{brand_id}` — derived risk signals
3. `GET /dashboard/top-advocates/{brand_id}` — positive authors
4. `GET /dashboard/competitor-sentiment/{brand_id}` — stacked sentiment by competitor
5. `GET /dashboard/ai-summary/{brand_id}` — Gemini-powered summary (last, most complex)

### Phase G — Mentions Monitor Page
New sidebar item "Mentions Monitor" → new page at `pages/MentionsMonitor.tsx`
- Combines `MentionsList` full-screen with source tabs (All / News & RSS / YouTube / Reviews / Reddit)
- Replaces current `SourceBreakdown` page
- Integrates `JournalistCoverage` as a sub-tab

### Phase H — Docs & Cleanup
1. Remove `Overview.tsx` (replaced by `DashboardScreen1/2/3.tsx`)
2. Remove `MentionsBySourceDonut.tsx` if fully superseded
3. Update `team-requirements.md` and `competitive-analysis-and-pricing.md`
4. Update `docs/Phase 3.0/LanguageParsing.md` if status changed

---

## 11. What Does NOT Change

- All existing data API endpoints (until Phase F extends them)
- Authentication flow (Login, BrandSearch, session management)
- `MentionsList` component internals (used unchanged inside panels)
- Supabase schema (no new tables; Phase F adds computed queries only)
- Pipeline, Railway deployment, ingestion code
- `JournalistCoverage`, `ReviewQueue`, `UserManagement`, `BrandConfig` pages
- `TopicSentimentChart`, `SourceSentimentChart` (used in sub-pages)
- All existing alert logic

---

## 12. Migration Risk Notes

| Risk | Mitigation |
|------|------------|
| Scroll snap may feel laggy on low-end devices | Test on mobile; fallback to `scroll-behavior: smooth` without snap |
| Screen 1 content taller than one viewport | Use `overflow-hidden` + smaller font sizes; measure and adjust flex ratios |
| AI Summary endpoint adds latency | Show skeleton placeholder; load async after initial data |
| `IndiaStateMap` region aggregation math may be off | Unit test state → region mapping before UI integration |
| Competitor Sentiment tab needs competitor data in DB | Fallback to SoV tab only if competitor articles < 10 |
| `total_reach` sum can be very large (215M+) | Format with `formatCount()` utility (already handles M/K suffixes) |

---

## 13. File Change Index

### New files
```
frontend/src/components/AIExecutiveSummary.tsx
frontend/src/components/MentionsBySourceCards.tsx
frontend/src/components/ReputationRiskGauge.tsx
frontend/src/components/TopInfluentialSources.tsx
frontend/src/components/TopNegativeMentions.tsx
frontend/src/components/TopBrandAdvocates.tsx
frontend/src/components/DashboardFooterBar.tsx
frontend/src/components/CompetitorComparison.tsx
frontend/src/components/NewsRSSMentionsPanel.tsx
frontend/src/components/ReviewSiteAnalysisPanel.tsx
frontend/src/pages/DashboardScreen1.tsx
frontend/src/pages/DashboardScreen2.tsx
frontend/src/pages/DashboardScreen3.tsx
frontend/src/pages/MentionsMonitor.tsx
backend/app/dashboard/ai_summary.py
backend/app/dashboard/risk.py
backend/app/dashboard/advocates.py
```

### Modified files
```
frontend/src/App.tsx                          ← scroll container, screen routing
frontend/src/components/Sidebar.tsx           ← new nav, date range, subtitle
frontend/src/components/cards/KPICard.tsx     ← sparkline + donut + label variants
frontend/src/components/TopIssuesTable.tsx    ← new visual style
frontend/src/components/charts/IndiaStateMap.tsx  ← regions variant
frontend/src/components/ReviewSitesSummary.tsx    ← extend for Screen 3 panel
backend/app/dashboard/overview.py            ← add by_source_type, total_reach
backend/app/dashboard/sources.py             ← add get_top_influential_sources()
backend/app/main.py                          ← register new routes
```

### Retired files (after migration complete)
```
frontend/src/pages/Overview.tsx               ← replaced by DashboardScreen1/2/3
frontend/src/components/charts/MentionsBySourceDonut.tsx  ← replaced by MentionsBySourceCards
```

---

## 14. Effort & Appeal Impact Assessment

> *Added 2026-06-22 — assessment of migration cost vs visual/business value*

### 14.1 Effort Breakdown

| Phase | Scope | Est. Days |
|-------|-------|-----------|
| A — Scroll infrastructure | Change 3 CSS classes, create 3 screen wrappers | 0.5 |
| B — Sidebar rebuild | New nav items + date range display | 1 |
| C — Screen 1 | 4 new components, extend KPICard, 1 backend change | 4 |
| D — Screen 2 | 6 new components, SVG gauge, region map, 3 backend endpoints | 5 |
| E — Screen 3 | 3 new components, tabbed competitor view, 1 backend endpoint | 4 |
| F — AI Summary backend | Gemini prompt + caching layer | 2 |
| G — Mentions Monitor page | New page + tab routing | 2 |
| **Total** | | **~18–19 dev days** |

Roughly **3.5–4 weeks** at current pace. The hardest parts are the SVG semi-circle gauge (Screen 2) and the AI Summary backend (caching + prompt engineering). Everything else maps cleanly to existing components.

About **65% of the effort is net-new UI**; the remaining 35% is wiring existing components (`MentionsList`, `SentimentTrendChart`, `TopIssuesTable`, `IndiaStateMap`) into the new screen layout.

---

### 14.2 Appeal Comparison

| Dimension | Current | New | What changes |
|-----------|---------|-----|-------------|
| First impression | Looks like a tool | Looks like a product | Dark card design, spacious layout, visual hierarchy |
| Executive readiness | Requires interpretation | Self-narrating | AI Summary explains *what changed / why / what to do* |
| Information density | Cramped (4 rows compressed to one screen) | Breathing room across 3 screens | Users read, not squint |
| Emotional impact | Neutral | Urgent/professional | Risk gauge, advocate highlights, negative impact cards |
| Sales demo moment | Weak — looks like a prototype | Strong — looks like Brand24 / Meltwater | Parallax scroll is immediately impressive to a prospect |
| Competitor story | 1 donut (SoV only) | 3-tab comparison (SoV + Sentiment + Topics) | Much deeper competitive narrative |
| India focus | State map buried in a detail panel | Geographic heatmap front-and-centre on Screen 2 | Visible regional intelligence |
| Unique differentiator | Nothing that standalone tools don't have | AI Executive Summary on the home screen | No Indian competitor at this price tier does this |

**Current appeal: 6/10** — functional, information-complete, feels like a developer's internal tool.
**New appeal: 9/10** — product-grade, executive-presentable, demo-able in 30 seconds to a CMO.

---

### 14.3 Minimum Viable Visual Upgrade (if time-pressured)

Executing only **Phases A + B + C** (scroll layout + sidebar + Screen 1) delivers ~70% of the visual improvement in approximately **6 dev days**:

| Item | Why it matters |
|------|---------------|
| CSS Scroll Snap layout (Phase A) | The three-screen structure alone changes perception dramatically — visitors immediately feel a richer product |
| AI Executive Summary (Phase C + F) | Only feature in the Indian market at this tier that narrates the brand story on the dashboard home screen |
| Reputation Risk Gauge (Phase D) | A semi-circle dial with "Medium Risk 58/100" is what gets screenshotted and shared in client presentations |

**Lowest ROI items to defer:**

| Item | Why it can wait |
|------|----------------|
| Top Brand Advocates | No advocate tracking data in DB today |
| Drill-Down Journey panel | Purely decorative, static |
| Competitor Sentiment tab | Requires competitor articles tracked in DB |
| Topics Comparison tab | No competitor topic data yet |
