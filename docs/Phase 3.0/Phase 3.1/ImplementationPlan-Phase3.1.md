# Phase 3.1 — AI Intelligence Copilot: Implementation Plan
**Date:** 2026-06-24
**Baseline score:** 100/120 (post–Session 12)
**Target score:** 120/120
**Theme:** Complete the reference vision — transform the monitoring dashboard into a full AI Reputation Intelligence Operating System

---

## Reference Vision Alignment

The ScreenFlow spec (`docs/Phase 3.0/Drilldown/ScreenFlow.md`) defines 9 screens. Current implementation has 8 snap screens in `Overview.tsx`. Phase 3.1 closes the remaining gaps.

| ScreenFlow Screen | Current State | Phase 3.1 Goal |
|---|---|---|
| S1 AI Executive Copilot | 6/10 — Morning Brief ✅, What Changed ❌, Confidence ✅, Chat ✅ | Add What Changed Since Yesterday widget |
| S2 Intelligence Feed | 5/10 — Stories ✅ (data issue), Issue Radar ❌ (table only), Narratives ✅ | Add animated AI Issue Radar; ensure 5 narratives |
| S3 Situation Room | 3/10 — Risk gauge only, no Risk Copilot, no Crisis Timeline | Add Risk Copilot + Crisis Timeline + Scenario Simulator |
| S4 Narrative Explorer | 8/10 — Entity graph + NarrativeDNA ✅ | No changes planned |
| S5 Investigation Workspace | 7/10 — DrillDown ✅ | No changes planned |
| S6 Response Studio | 7/10 — ContentGenerator + language selector ✅ | Add Response Calendar |
| S7 Advocacy Hub | 4/10 — TopBrandAdvocates ✅ | No changes planned |
| S8 Geo Intelligence | 7/10 — State map + Regional Summary ✅ | Add compact AI Snapshot card |
| S9 Board Mode | 7/10 — Top5 + Risk + Headlines ✅ | Add Top 5 Opportunities section |

---

## Part A — Carry-Forward Bug Fixes

These are bugs reported in the prior sprint. Items marked ✅ were fixed in commit `5322eb1`. Items marked 🔄 need verification or remain unresolved.

| # | Bug | Status | Action |
|---|---|---|---|
| 1 | All 5 KPI Explain buttons show same content | ✅ Fixed | Verify in prod — each metric now has a separate Gemini prompt |
| 2 | View in Tab B does nothing | ✅ Fixed | `onDrillTab` prop now threaded through `AIExplainerChip` |
| 3 | Co-Pilot chat returns "Error. Please try again." | ✅ Fixed | `KeyError: 'days'` in `_build_chat_context` resolved |
| 4 | View Full Insight → goes to Sentiment Trend | ✅ Fixed | Now opens `ai-report` panel overlay |
| 5 | Empty space below Morning Brief | ✅ Fixed | `flex-none` → `h-full` on `AIExecutiveSummary` root div |
| 6 | Empty space after Situation/Root Cause row | ✅ Fixed | Same fix as #5 |
| 7 | AskBar errors + overlaps brand name | ✅ Fixed | `left: 240px` → `left: 14rem`; chat `KeyError` fixed |
| 8 | Stories That Matter shows "No stories in last 7 days" | 🔄 Data issue | Pipeline must ingest articles into `story_feed` for current period. No code fix needed — verify `story_feed` table has recent rows for active brands |
| 9 | Drilldown for Top Influential Sources | ✅ Fixed | Click on source row → `openDrillDown` with `{ q: source }` |
| 10 | Drilldown for Reputation Risk Gauge | ✅ Fixed | Click on gauge → `openDrillDown` with `{ issueCategory: topIssue }` |
| 11 | "+N more" in EmergingNarrative disrupts layout | ✅ Fixed | Expansion changed to `position: absolute` dropdown |
| 12 | SoV refresh button not clickable | ✅ Fixed | `isRefreshing` state + spinner + disabled state |
| 13 | Google Reviews — only 5 retrieved; View All not clickable | ✅ Fixed | SerpAPI pagination (up to 20); View All fires scroll event |
| 14 | Geo Intelligence — widget too large; no AI snapshot | 🔄 Partial | Geo map renders but takes full screen. Phase 3.1 adds compact AI snapshot card overlay |
| 15 | Response Studio generation fails; no language selector | ✅ Fixed | `language` field in `GenerateRequest`; 6 radio buttons in UI |
| 16 | Board Mode top headlines not populating | ✅ Fixed | Section now always visible; 2-col card grid with loading/empty states |
| 17 | Sidebar nav items missing | ✅ Fixed | Response Studio/Narrative Explorer/Review Sites scroll events added |

---

## Part B — New Feature Implementations

### FEATURE 1 — "What Changed Since Yesterday?" Widget

**Screen:** S1 AI Executive Copilot (below AIExecutiveSummary, above SentimentTrendChart)
**Reference:** ScreenFlow Widget 2 on Screen 1 — "Three major developments detected. Negative mentions declined. Polimer News shifted positive. Google reviews worsened."

#### B1.1 Backend — `GET /dashboard/yesterday-diff/{brand_id}`

**File:** `backend/app/dashboard/router.py`

```python
class YesterdayChange(BaseModel):
    title: str          # "Negative coverage dropped 18%"
    body: str           # "Tamil media shifted positive after Vikatan piece"
    direction: str      # "positive" | "negative" | "neutral"
    category: str       # "sentiment" | "source" | "reviews" | "volume" | "risk"
    delta_value: str    # "+4 pts" | "-18%" | "2 new portals"

class YesterdayDiffResponse(BaseModel):
    changes: list[YesterdayChange]    # 3–5 items
    summary_line: str                 # one-liner for the header
    confidence_pct: int
    generated_at: str
```

**Logic:**
1. Query KPI snapshot for today vs 24 hours ago (perception_score, negative_pct, mention_count, top portal by volume, avg_review_rating)
2. Compute deltas: score_delta, negative_pct_delta, mention_delta, review_delta
3. Identify significant portals that changed direction (were negative, now positive — or vice versa) by comparing sentiment ratios per `portal_id` with a 48h vs 24h window
4. Build a context string of all significant changes
5. Gemini prompt:
   ```
   You are a senior PR analyst. Based on these data changes for {brand_name}:
   {changes_summary}
   Write 3–5 development cards in this JSON format:
   [{"title": "<4-word headline>", "body": "<1–2 sentences explaining what changed and why it matters>", "direction": "positive|negative|neutral", "category": "sentiment|source|reviews|volume|risk"}]
   Be specific — name the portal, the percentage, the issue.
   ```
6. Cache: 60 minutes (stale data acceptable; this is a delta card, not real-time)

**New schema:** `schemas.py`
```python
class YesterdayDiffResponse(BaseModel):
    changes: list[dict]
    summary_line: str
    confidence_pct: int
    generated_at: str
```

#### B1.2 Frontend — `WhatChangedYesterday.tsx`

**File:** `frontend/src/components/WhatChangedYesterday.tsx`

```tsx
interface Change {
  title: string;
  body: string;
  direction: "positive" | "negative" | "neutral";
  category: string;
  delta_value?: string;
}

// Layout: horizontal scroll of swipeable cards OR 3-card flex row
// Card anatomy:
//   Left border: 3px solid (emerald=positive, red=negative, amber=neutral)
//   Top: small label chip ("Sentiment" | "Source" | "Reviews" | "Volume" | "Risk")
//   Middle: bold 4-word title
//   Bottom: 1–2 sentence body in text-white/60
//   Far-right: direction arrow icon (↑ / ↓ / →) in matching color

// Loading state: 3 skeleton cards
// Empty state: "No significant changes detected since yesterday."

// Prop: { brandId: string; days: number }
// Query key: ["yesterday-diff", brandId]
// Endpoint: GET /dashboard/yesterday-diff/{brandId}
```

**Position in Overview.tsx:**
- Insert between `AIExecutiveSummary` and `SentimentTrendChart` in Screen 1
- Wrap in a `<div className="mt-4">` — no layout changes to surrounding elements

---

### FEATURE 2 — AI Issue Radar (Animated Bubble Chart)

**Screen:** S2 Intelligence Feed (replaces or supplements `TopIssuesTable` in Screen 2)
**Reference:** ScreenFlow Widget 2 on Screen 2 — "Animated clusters. Issues floating. Consumer Boycott / CSR / Political / Pricing / Product. Hover: Summary / Mentions / Velocity."

#### B2.1 Backend — Enhance `GET /dashboard/issue-categories/{brand_id}`

**File:** `backend/app/dashboard/router.py`

Add velocity calculation to existing endpoint response:
```python
class IssueCategoryItem(BaseModel):
    category: str
    count: int
    negative_pct: float
    severity: str                    # "low" | "medium" | "high" | "critical"
    velocity: float                  # articles/day in last 7d vs prior 7d ratio
    momentum: str                    # "rising" | "stable" | "declining"
    ai_summary: str | None = None    # 1-sentence Gemini summary per issue (optional, cached)
```

Velocity formula:
```python
recent_count = count of articles with issue_category=X in last 7 days
prior_count = count of articles with issue_category=X in days 8–14
velocity = (recent_count / 7) / max((prior_count / 7), 0.1)
# velocity > 1.5 = rising, 0.7–1.5 = stable, < 0.7 = declining
```

#### B2.2 Frontend — `AIIssueRadar.tsx`

**File:** `frontend/src/components/AIIssueRadar.tsx`

```tsx
// Layout: SVG canvas 400×300 (responsive via viewBox)
// Bubbles:
//   - Size: proportional to count (min r=20, max r=55)
//   - Position: random but non-overlapping (use d3-force simulation or pre-computed positions)
//   - Color by severity: critical=red (#ef4444), high=amber (#f59e0b), medium=blue (#3b82f6), low=emerald (#10b981)
//   - Label: category name (replace _ with space, capitalize)
//   - Sub-label: velocity arrow (↑↑ / ↑ / → / ↓) in smaller font

// Animation:
//   - Gentle float: CSS @keyframes with translateY(-4px/+4px), 3s ease-in-out infinite
//   - Each bubble gets a different animation-delay (i * 0.4s) to desync

// Hover tooltip:
//   - Issue name
//   - "X articles · Y% negative"
//   - Velocity: "Rising 2.3×" | "Stable" | "Declining"
//   - AI summary (1 sentence if available)

// Click: calls onIssueClick(category) → openDrillDown filtered by issueCategory

// Props:
//   brandId: string
//   days: number
//   onIssueClick?: (category: string) => void
```

**Integration in Overview.tsx:**
- Add as a second tab in the existing Screen 2 TopIssues section (Tab 1: Table, Tab 2: Radar)
- OR replace the table entirely — user preference
- **Recommended:** Add as a toggle — "Table | Radar" switch in the section header

---

### FEATURE 3 — Emerging Narratives (5 Narratives, AI Generated)

**Screen:** S2 Intelligence Feed (Screen 7 Narrative Explorer also shows this)
**Reference:** ScreenFlow Widget 3 on Screen 2 — "AI discovered. 5 new narratives. Appearing in Tamil media."

#### B3.1 Backend — `GET /dashboard/emerging-narratives/{brand_id}`

**File:** `backend/app/dashboard/router.py`

```python
class EmergingNarrative(BaseModel):
    title: str               # "Quality claims resurface in Tamil media"
    summary: str             # 2-sentence Gemini description
    article_count: int
    first_seen: str          # ISO date
    momentum: str            # "emerging" | "accelerating" | "peaking" | "fading"
    primary_language: str    # "Tamil" | "English" | "Hindi"
    tags: list[str]          # ["product_quality", "youtube_comments"]

class EmergingNarrativesResponse(BaseModel):
    narratives: list[EmergingNarrative]   # always 5 items (pad with low-signal if needed)
    generated_at: str
    confidence_pct: int
```

**Logic:**
1. Cluster recent articles by topic similarity (existing `topics` field) — top 10 topic clusters
2. Filter out clusters already covered by the 12 issue_category taxonomy
3. Feed remaining clusters to Gemini: "Based on these article clusters, identify 5 emerging narrative themes that are gaining momentum for {brand}. Each narrative must have: title (6 words max), 2-sentence summary, momentum label (emerging/accelerating/peaking/fading), primary language of coverage."
4. If fewer than 5 organic clusters, pad with smallest issue_category items labeled "low signal"
5. Cache: 2 hours

**Existing `EmergingNarrativeBanner.tsx` already handles display.** Only change needed: ensure backend returns 5 items and momentum label is included, then display momentum as a badge next to the narrative title.

#### B3.2 Frontend Update — `EmergingNarrativeBanner.tsx`

**Minimal changes:**
- Add momentum badge: `<span className={momentumColor}>{narrative.momentum}</span>`
- Colors: emerging=blue, accelerating=amber, peaking=red, fading=white/30
- Show `primary_language` as a small flag/tag
- First narrative always expanded (currently all collapsed)
- "+N more" already fixed to absolute dropdown

---

### FEATURE 4 — Risk Copilot Widget

**Screen:** S3 Situation Room (Screen 2 currently has ReputationRiskGauge — this is a richer replacement)
**Reference:** ScreenFlow Screen 3 Widget 1 — "Medium risk. Probability of escalation: 62%. Show me why → Prediction model / Signals."

#### B4.1 Backend — `GET /dashboard/risk-copilot/{brand_id}`

**File:** `backend/app/dashboard/router.py`

```python
class RiskDriver(BaseModel):
    driver: str              # "Negative YouTube comments surging"
    weight_pct: int          # 0–100 (relative weight in risk score)
    trend: str               # "rising" | "stable" | "declining"
    evidence_count: int      # number of articles driving this

class RiskCopilotResponse(BaseModel):
    risk_level: str          # "low" | "medium" | "high" | "critical"
    current_score: int       # 0–100
    escalation_probability: float   # 0.0–1.0
    risk_drivers: list[RiskDriver]  # top 3
    why_explanation: str     # Gemini 3-sentence explanation
    confidence_pct: int
    last_updated: str
```

**Logic:**
1. Pull current risk score from existing `risk-forecast` calculation
2. Calculate escalation probability:
   - Base = current_score / 100
   - Adjust: +0.15 if velocity > 2.0 on any issue, +0.10 if negative_pct > 0.5, -0.10 if score trending down over 7d
   - Clamp to 0.0–0.99
3. Identify top 3 risk drivers from issue_categories ranked by (negative_pct × velocity × count)
4. Gemini generates `why_explanation`: "Risk is elevated due to [driver1]. [driver2] is the secondary signal. [forward-looking sentence]."
5. Cache: 30 minutes (risk copilot should feel near-current)

#### B4.2 Frontend — `RiskCopilot.tsx`

**File:** `frontend/src/components/RiskCopilot.tsx`

```tsx
// Layout (card, dark bg-[#0d1626], border-[#1a2744]):
//
// ┌─────────────────────────────────────────────┐
// │  MEDIUM RISK          Score: 62 / 100       │
// │  ─────────────────────────────────────────  │
// │  Probability of Escalation                  │
// │  [████████░░░░░░] 62%                       │
// │  ─────────────────────────────────────────  │
// │  Risk Drivers              [Show me why →]  │
// │  ▲ Neg YouTube comments   35% ↑            │
// │  ◆ Tamil media coverage   28% →            │
// │  ▼ Google Reviews drop    22% ↓            │
// │  ─────────────────────────────────────────  │
// │  [why panel — hidden until "Show me why"]   │
// │  "Risk elevated due to..."                  │
// └─────────────────────────────────────────────┘

// State: showWhy (boolean toggle)
// "Show me why →" button → expand why_explanation text block
// Escalation bar: color gradient — green (0–30%) → amber (30–60%) → red (60–100%)
// Driver rows: icon (▲=rising red / ◆=stable amber / ▼=declining green), driver text, weight bar

// Props: { brandId: string; days: number; onClick?: () => void }
// onClick → openDrillDown("Risk Analysis", { issueCategory: topDriver })
```

---

### FEATURE 5 — Crisis Timeline + Scenario Simulator

**Screen:** S3 Situation Room (new section below Risk Copilot)
**Reference:** ScreenFlow Screen 3 Widgets 2+3 — "AI generated timeline. Netflix style. If This Continues Forecast. Scenario Simulator."

#### B5.1 Backend — `GET /dashboard/crisis-timeline/{brand_id}`

**File:** `backend/app/dashboard/router.py`

```python
class TimelineEvent(BaseModel):
    date: str                # "2026-06-18"
    event_type: str          # "story_detected" | "amplified" | "platform_spread" | "response" | "recovery"
    title: str               # "Story detected on Vikatan"
    description: str         # "First mention appeared in Tamil media..."
    source_type: str         # "news" | "youtube" | "reddit" | "reviews"
    impact_delta: int        # change in risk score at this event (+8 / -4)

class ScenarioOutcome(BaseModel):
    action: str              # "respond_in_24h" | "stay_silent"
    risk_change_pct: int     # -18 (negative = decrease) or +12 (positive = increase)
    confidence_pct: int
    reasoning: str           # 1-sentence Gemini explanation

class CrisisTimelineResponse(BaseModel):
    is_active_crisis: bool
    events: list[TimelineEvent]         # chronological, up to 10 events
    forecast: list[dict]                # [{horizon: "tomorrow", risk_score: 54}, ...]
    scenarios: list[ScenarioOutcome]    # 2 scenarios: respond vs silent
    suggested_action: str               # Gemini 1-sentence recommendation
    confidence_pct: int
```

**Logic:**
1. Cluster articles by date — find days with significant mention spikes (> 1.5× average daily volume)
2. For each spike day: identify primary source_type, top portal, sentiment shift → generate `TimelineEvent` label via Gemini ("Coverage amplified on YouTube with {count} new videos discussing {topic}")
3. Forecast: project current risk trend linearly + Gemini adjustment for "if this continues"
4. Scenario Simulator:
   - "Respond in 24h": base risk reduction = 15–25% (Gemini adjusted for crisis severity)
   - "Stay silent": base risk increase = 8–18% (Gemini adjusted)
   - Gemini generates reasoning for each
5. Cache: 1 hour (timeline is historical + near-future, not real-time)

#### B5.2 Frontend — `CrisisTimeline.tsx`

**File:** `frontend/src/components/CrisisTimeline.tsx`

```tsx
// SECTION 1: Timeline
// Layout: vertical timeline with left rail
//
// ●────────────────────────────────────────
// │  Jun 18  Story detected                 [news icon]
// │          "First mention on Vikatan..."
// │
// ●────────────────────────────────────────
// │  Jun 20  Amplified                      [trending icon]
// │          "3 YouTube channels discussed..."
// │
// ●────────────────────────────────────────    ← pulsing if "today"
// │  Jun 22  Platform spread                [youtube icon]
// │          "Reddit thread with 45 upvotes..."
//
// Colors: news=blue, youtube=red, reddit=orange, reviews=amber
// Active event (today or most recent): pulsing dot + highlighted border
// No crisis state: single row "No active crisis. Monitoring normal."
// Max 6 events shown; "Show more" expands to all

// SECTION 2: If This Continues Forecast
// 3 horizontal cards: Tomorrow | 3 Days | 7 Days
// Each: risk_score number + color bar + risk label (LOW/MEDIUM/HIGH/CRITICAL)

// SECTION 3: Scenario Simulator
// Side-by-side comparison:
//
// ┌─────────────────────┐  ┌─────────────────────┐
// │  If we respond      │  │  If we stay silent  │
// │  in 24 hrs          │  │                     │
// │  Risk ↓ by 18%      │  │  Risk ↑ by 12%      │
// │  (72% confidence)   │  │  (65% confidence)   │
// └─────────────────────┘  └─────────────────────┘
//
// Below: Suggested Action (full-width text box)
// "Issue proactive statement to Tamil media within 24 hours."
//
// "Run more scenarios →" button → opens Co-Pilot drawer with prompt:
// "Simulate risk impact if we [scenario]. Brand: {brandName}. Current risk: {score}."

// Props: { brandId: string; days: number; onRunScenarios?: () => void }
```

---

### FEATURE 6 — Response Calendar

**Screen:** S6 Response Studio (below `ContentGenerator` and `TopBrandAdvocates`)
**Reference:** ScreenFlow Screen 6 Widget 1 — "AI Recommended Actions. Priority: High. Issue clarification. Engage advocate. Meet journalist."

#### B6.1 Backend — `GET /dashboard/response-calendar/{brand_id}`

**File:** `backend/app/dashboard/router.py`

```python
class CalendarAction(BaseModel):
    date: str                # "2026-06-25"
    time_slot: str           # "09:00" | "14:00" | "EOD"
    action: str              # "Issue press clarification on product quality"
    priority: str            # "critical" | "high" | "medium" | "low"
    channel: str             # "Press Release" | "Social Media" | "Internal" | "Media Call"
    owner: str               # "PR Head" | "CEO" | "Communications Team"
    status: str              # "pending" | "accepted" | "deferred"
    rationale: str           # 1-sentence: why this action at this time

class ResponseCalendarResponse(BaseModel):
    calendar: list[CalendarAction]   # 5–7 items, next 7 days
    context_summary: str             # Gemini 2-sentence overall situation
    confidence_pct: int
```

**Gemini prompt:**
```
You are a senior PR advisor for {brand_name}.
Current situation: {situation_summary}
Top risks: {top_3_risks}
Create a 7-day response action calendar with 5–7 specific actions.
Each must have: date (YYYY-MM-DD starting {today}), time_slot, action (imperative, specific),
priority (critical/high/medium/low), channel, owner (PR Head/CEO/Communications Team),
rationale (1 sentence why this timing).
Return JSON array only.
```

Cache: 2 hours (calendar is strategic, not operational)

#### B6.2 Frontend — `ResponseCalendar.tsx`

**File:** `frontend/src/components/ResponseCalendar.tsx`

```tsx
// Layout: vertical list card
//
// ┌──────────────────────────────────────────────────────────┐
// │ Response Calendar                        AI Generated    │
// │ "Situation requires proactive media engagement in 48h." │
// ├──────────────────────────────────────────────────────────┤
// │ Jun 25  09:00  Issue press clarification    [CRITICAL]  │
// │                Press Release · PR Head                   │
// │                "Address quality claims before..."        │
// │                [Accept] [Defer] [Delegate]               │
// ├──────────────────────────────────────────────────────────┤
// │ Jun 25  14:00  Call Vikatan journalist      [HIGH]      │
// │                Media Call · PR Head                      │
// │                [Accept] [Defer] [Delegate]               │
// ├──────────────────────────────────────────────────────────┤
// │ Jun 26  EOD    Post social response         [MEDIUM]    │
// │                Social Media · Communications Team        │
// │                [Accept] [Defer] [Delegate]               │
// └──────────────────────────────────────────────────────────┘
//
// Priority colors: critical=red, high=amber, medium=blue, low=white/40
// Action buttons: Accept (green, fires status update), Defer (amber), Delegate (blue)
// Status badge: accepted=green check, deferred=clock icon, pending=dot
// Date grouping: show date header when date changes
//
// Props: { brandId: string }
// Query: GET /dashboard/response-calendar/{brandId}
// Local state: accepted/deferred actions (no backend persistence yet)
```

---

### FEATURE 7 — Top 5 Opportunities (Board Mode Enhancement)

**Screen:** S9 Executive Board Mode (`BoardMode.tsx`)
**Reference:** ScreenFlow Screen 9 Widgets 1–3 — "Top 5 Things / Top 3 Risks / Top 5 Opportunities"

#### B7.1 Backend — Enhance `GET /dashboard/board-briefing/{brand_id}`

**File:** `backend/app/dashboard/router.py`

Add `top_5_opportunities` to the existing `board-briefing` endpoint:

```python
class BoardBriefingResponse(BaseModel):
    greeting: str
    score_direction: str
    score_change: float
    highlights: list[str]            # = "Top 5 Things You Need To Know"
    top_3_risks: list[str]           # NEW — currently not returned
    top_5_opportunities: list[str]   # NEW
    confidence_pct: int
```

**Gemini prompt update** (add to existing single prompt):
```
Respond in JSON with exactly these keys:
{
  "highlights": ["<5 things need to know>"],
  "top_3_risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "top_5_opportunities": ["<opp 1>", ..., "<opp 5>"],
  "score_direction": "up|down|stable",
  "score_change": <number>,
  "confidence_pct": <number>
}
```

#### B7.2 Frontend — `BoardMode.tsx` Update

Add Top 5 Opportunities section between "Top Headlines" and "AI Recommendation":

```tsx
{/* Top 5 Opportunities */}
<div className="border-t border-white/8 pt-8">
  <div className="text-[9px] uppercase tracking-widest text-white/30 mb-4">
    Top 5 Opportunities
  </div>
  {loadBrief ? <Skeleton lines={5} /> : (
    <ol className="space-y-4">
      {(brief?.top_5_opportunities ?? []).map((opp, i) => (
        <li key={i} className="flex gap-5">
          <span className="text-[15px] font-semibold text-emerald-400/40 tabular-nums w-6 shrink-0 pt-0.5">{i + 1}.</span>
          <p className="text-[14px] text-white/70 leading-relaxed">{opp}</p>
        </li>
      ))}
    </ol>
  )}
</div>
```

Also add Top 3 Risks as a dedicated section (currently using `IssueRow` from issue radar data — replace with Gemini-generated `top_3_risks` list):

```tsx
{/* Top 3 Risks */}
<div>
  <div className="text-[9px] uppercase tracking-widest text-white/30 mb-4">Top 3 Risks</div>
  <ol className="space-y-3">
    {(brief?.top_3_risks ?? topIssues.map(i => i.issue)).slice(0, 3).map((risk, i) => (
      <li key={i} className="flex gap-4">
        <span className="text-[13px] font-bold text-red-400/50 w-5">{i + 1}.</span>
        <p className="text-[13px] text-white/65 leading-relaxed">{risk}</p>
      </li>
    ))}
  </ol>
</div>
```

---

### FEATURE 8 — Geo Intelligence Compact AI Snapshot

**Screen:** S8 Geo Intelligence (Screen 8 in Overview.tsx)
**Reference:** User request — "compact the Geographic Sentiment widget or bring in AI generated snapshot based on those specific geography"

#### B8.1 Backend — Already exists

`GET /dashboard/regional-summary/{brand_id}` already returns `AIRegionalSummaryResponse`:
- `summary`: Gemini paragraph on regional sentiment
- `state_highlights`: per-state direction (improving/declining)
- `confidence_pct`

No new endpoint needed.

#### B8.2 Frontend — Add compact overlay card on Geo map

**File:** `frontend/src/components/GeoIntelligence/IndiaStateMap.tsx` or a wrapper in `Overview.tsx`

Add a floating card panel **overlaid** on the map (bottom-left corner, `position: absolute`):

```tsx
// Compact AI Snapshot — overlaid on the map, not below it
// ┌────────────────────────────────────────────┐
// │ AI Regional Snapshot              [Expand] │
// │ "South India improving. West declining."   │
// │                                            │
// │ 🟢 Tamil Nadu  ↑  🟢 Karnataka  ↑        │
// │ 🔴 Maharashtra ↓  🟡 Delhi     →         │
// └────────────────────────────────────────────┘
//
// Position: absolute bottom-4 left-4 z-10
// Width: ~340px
// Bg: bg-[#0d1626]/90 backdrop-blur
// Collapsed: shows summary line + top 2 states
// [Expand]: opens full AIRegionalSummary panel (existing component)
//
// This keeps the map taking its full visual space
// while surfacing the AI insight without scrolling
```

---

## Part C — Future: Influencer Tree

**Status:** Deferred to Phase 4 (complexity requires graph database or D3.js force layout)
**Reference:** ScreenFlow Screen 5 Widget 3 — "Root source → Amplifiers → Consumers. Graph database."

**Design when built:**
- Input: a specific article cluster or story (identified by `story_id` or `topic`)
- Backend: trace article cascade — find first publication date + source, then all articles that cite/reference the same story (matched by title similarity or URL in body text)
- Nodes: portal/channel nodes sized by reach, colored by source_type
- Edges: "amplified by" arrows with timestamps
- Leaf nodes: YouTube channels, Reddit posts, Google Reviews that echo the original story
- Frontend: `react-flow` or D3.js force-directed graph
- Click node: open that source's mentions in DrillDown

**Prerequisite:** Requires `parent_article_id` or `origin_story_id` field on articles table — not yet tracked in the pipeline.

---

## Implementation Session Sequence

Estimated 4 sessions × 2 hours each. Each session is a complete, deployable vertical slice.

### Session A — Risk Intelligence (S3 Situation Room)
**Target:** +8 pts (100 → 108/120)

```
[SEQ] Backend router.py:
  1. GET /dashboard/risk-copilot/{brand_id}
     - RiskDriver model + RiskCopilotResponse model in schemas.py
     - Escalation probability calculation
     - Gemini "why_explanation" with 30-min cache

  2. GET /dashboard/crisis-timeline/{brand_id}
     - TimelineEvent model + ScenarioOutcome model + CrisisTimelineResponse
     - Article clustering by date spike
     - Gemini event labeling per cluster
     - Scenario probability calculation
     - 1-hour cache

[PARALLEL]:
  [A1] frontend/src/components/RiskCopilot.tsx
       - Risk level header + score
       - Escalation probability bar (color-coded)
       - 3 risk driver rows with weight bars + trend icons
       - "Show me why" toggle → expand why_explanation

  [A2] frontend/src/components/CrisisTimeline.tsx
       - Vertical timeline with event nodes
       - 3-card forecast row (Tomorrow / 3 Days / 7 Days)
       - Scenario simulator 2-card comparison
       - Suggested action text + "Run more scenarios" button

  [A3] Update Overview.tsx Screen 3 (Situation Room):
       - Import + render RiskCopilot (replace/supplement ReputationRiskGauge)
       - Import + render CrisisTimeline below it
       - Wire "Run more scenarios" to open CoPilotPanel with pre-filled query

Push → verify Railway + Vercel → tsc --noEmit clean
```

---

### Session B — AI Intelligence Feed (S2 Intelligence Feed)
**Target:** +6 pts (108 → 114/120)

```
[SEQ] Backend router.py:
  1. Enhance GET /dashboard/issue-categories/{brand_id}
     - Add velocity + momentum + ai_summary fields to response

  2. GET /dashboard/emerging-narratives/{brand_id}
     - EmergingNarrative model in schemas.py
     - Topic cluster extraction from articles.topics JSONB
     - Gemini narrative generation (5 items guaranteed)
     - 2-hour cache

[PARALLEL]:
  [B1] frontend/src/components/AIIssueRadar.tsx
       - SVG bubble chart with D3-style positioning
       - Animated float (CSS keyframes per bubble)
       - Hover tooltip: category / count / velocity / ai_summary
       - Click → openDrillDown by issueCategory

  [B2] Update EmergingNarrativeBanner.tsx
       - Add momentum badge (emerging/accelerating/peaking/fading)
       - Add primary_language tag
       - Ensure 5 narratives render (backend now guarantees 5)
       - First narrative expanded by default

  [B3] Update Overview.tsx Screen 2:
       - Replace TopIssuesTable with AIIssueRadar (or add toggle)
       - Wire emerging-narratives endpoint to EmergingNarrativeBanner
       - Add "Radar | Table" toggle in section header

Push → verify → tsc clean
```

---

### Session C — What Changed + Response Calendar (S1 + S6)
**Target:** +4 pts (114 → 118/120)

```
[SEQ] Backend router.py:
  1. GET /dashboard/yesterday-diff/{brand_id}
     - YesterdayChange + YesterdayDiffResponse models
     - KPI delta computation (today vs 24h ago)
     - Portal sentiment direction change detection
     - Gemini 3–5 change cards
     - 60-min cache

  2. GET /dashboard/response-calendar/{brand_id}
     - CalendarAction + ResponseCalendarResponse models
     - Gemini 7-day action calendar generation
     - 2-hour cache

[PARALLEL]:
  [C1] frontend/src/components/WhatChangedYesterday.tsx
       - 3-card horizontal flex row
       - Left border color by direction
       - Category chip + title + body text
       - Loading skeleton (3 shimmer cards)

  [C2] frontend/src/components/ResponseCalendar.tsx
       - Vertical action list with date groupings
       - Priority badges (critical/high/medium/low)
       - Accept/Defer/Delegate local state buttons
       - Context summary header

  [C3] Update Overview.tsx Screen 1 + Screen 6:
       - Insert WhatChangedYesterday below AIExecutiveSummary in Screen 1
       - Insert ResponseCalendar below ContentGenerator in Screen 6

Push → verify → tsc clean
```

---

### Session D — Board Intelligence + Geo Snapshot (S9 + S8)
**Target:** +2 pts (118 → 120/120)

```
[SEQ] Backend router.py:
  1. Enhance GET /dashboard/board-briefing/{brand_id}
     - Add top_3_risks + top_5_opportunities to Gemini prompt + response schema
     - Update BoardBriefingResponse in schemas.py
     - No new endpoint — amend existing

[PARALLEL]:
  [D1] Update frontend/src/pages/BoardMode.tsx
       - Replace IssueRow-based "Top Concerns" with Gemini top_3_risks list
       - Add "Top 5 Opportunities" section (numbered, emerald accent)
       - Ensure section order: Top 5 Things → Risk Status → Top 3 Risks
         → Top Headlines → Top 5 Opportunities → AI Recommendation

  [D2] Geo Intelligence compact AI snapshot
       - Add floating card overlay on IndiaStateMap (position: absolute bottom-4 left-4)
       - Use existing /dashboard/regional-summary data
       - Show 2-line summary + top 4 state pills (🟢/🔴/🟡)
       - [Expand] button shows full AIRegionalSummary below map

Push → verify → tsc clean → Score: 120/120
```

---

## Component File Inventory

| New File | Session | Screen |
|---|---|---|
| `frontend/src/components/RiskCopilot.tsx` | A | S3 |
| `frontend/src/components/CrisisTimeline.tsx` | A | S3 |
| `frontend/src/components/AIIssueRadar.tsx` | B | S2 |
| `frontend/src/components/WhatChangedYesterday.tsx` | C | S1 |
| `frontend/src/components/ResponseCalendar.tsx` | C | S6 |

| Modified File | Session | Change |
|---|---|---|
| `backend/app/dashboard/router.py` | A, B, C, D | 5 new/enhanced endpoints |
| `backend/app/dashboard/schemas.py` | A, B, C, D | 8 new Pydantic models |
| `frontend/src/components/EmergingNarrativeBanner.tsx` | B | momentum badge + language tag |
| `frontend/src/pages/Overview.tsx` | A, B, C | 3 new screen sections |
| `frontend/src/pages/BoardMode.tsx` | D | Top 3 Risks + Top 5 Opportunities |
| `frontend/src/lib/api.ts` | A, B, C, D | 5 new fetch functions |
| `frontend/src/lib/types.ts` | A, B, C, D | New TypeScript interfaces |

---

## New Backend Endpoints Summary

| Endpoint | Cache | Session |
|---|---|---|
| `GET /dashboard/yesterday-diff/{brand_id}` | 60 min | C |
| `GET /dashboard/emerging-narratives/{brand_id}` | 2 hr | B |
| `GET /dashboard/risk-copilot/{brand_id}` | 30 min | A |
| `GET /dashboard/crisis-timeline/{brand_id}` | 1 hr | A |
| `GET /dashboard/response-calendar/{brand_id}` | 2 hr | C |
| `GET /dashboard/board-briefing/{brand_id}` | 2 hr (enhanced) | D |
| `GET /dashboard/issue-categories/{brand_id}` | 30 min (enhanced) | B |

All Gemini calls use `gemini-2.5-flash` via `gemini_free_api_key` (free tier). Cache is Redis with `aioredis`. Fallback: return data-driven defaults without Gemini text when API unavailable.

---

## Future Roadmap (Post 120/120)

### Phase 4.0 — Social Channels + Real-time
- Twitter/X monitoring (the most critical remaining gap)
- Instagram + Facebook
- Near-real-time ingestion (< 15 min from publication)
- Webhook-based alert delivery (Slack, WhatsApp)

### Phase 4.1 — Influencer Tree
- `parent_article_id` field added to articles (pipeline change)
- Article cascade graph: first source → reshares → YouTube → Reddit → Reviews
- `react-flow` visualization with source-type colored nodes
- Click node → DrillDown filtered to that source's articles about this story
- Backend: `GET /dashboard/influence-cascade/{brand_id}?story_cluster={id}`

### Phase 4.2 — Approval Workflow + PDF Export
- Accept/Defer/Delegate buttons persist to `generated_content` table (status field)
- Response Calendar saved to Supabase
- "Export as PDF" via browser print CSS (`@media print`) — already partially wired in BoardMode

### Phase 4.3 — Billing Integration
- Razorpay / Stripe India payment flow
- Subscription management screen
- Usage metering (API calls, brands, users)
