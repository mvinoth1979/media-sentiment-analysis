# MediaSense Dashboard — Gap Analysis
## Reference Vision vs. Current Implementation
**Date:** 2026-06-23 | **Analyst:** Claude Sonnet 4.6 + Manual Audit
**Reference:** `references/ChatGPT Image Jun 23, 2026, 05_04_11 PM.png` + `docs/Phase 3.0/Drilldown/ScreenFlow.md`
**Current codebase:** `frontend/src/pages/Overview.tsx` + all `frontend/src/components/**`

---

## Methodology

Each screen and universal widget is rated **0–10** against the reference image and ScreenFlow spec.

| Score | Meaning |
|-------|---------|
| 0 | Not implemented — screen or feature does not exist |
| 1–2 | Placeholder or name-only stub; no real data or AI |
| 3–4 | Basic data table/chart present; no AI layer, no interactivity to spec |
| 5–6 | Core feature working; partially AI-augmented; UX mismatches remain |
| 7–8 | Feature-complete vs reference; AI integrated; minor cosmetic gaps |
| 9–10 | Matches reference vision exactly — data, AI, and UX all aligned |

---

## Reference Vision — What the Image Shows

The reference image shows **9 distinct screens in a 3×3 grid**, each a dedicated intelligence surface:

| Position | Screen | Visual Identity |
|----------|--------|----------------|
| Top-left | AI Executive Copilot | Morning brief card, chat input, confidence meter |
| Top-center | Intelligence Feed | Story cards (Investigate/Watch/Ignore), animated issue radar |
| Top-right | Situation Room | Risk % dial, crisis timeline, forecast numbers |
| Mid-left | Narrative Explorer | Knowledge graph (radial), narrative DNA spider chart |
| Mid-center | Investigation Workspace | AI "Why" explanation, entity list, influence tree |
| Mid-right | Response Studio | Content generator form, approval workflow, scenario sim |
| Bot-left | Advocacy Hub | Advocate cards with affinity/influence/trust scores |
| Bot-center | Geo Intelligence | India heat map + AI regional summary text |
| Bot-right | Executive Board Mode | Text-only CEO view, confidence 91% |

All screens share three **Universal AI Widgets**: Ask Bar, Insight Chips, Co-Pilot Drawer.

---

## Current Dashboard Architecture

The current implementation uses a **single-page 5-screen vertical snap scroll** inside `Overview.tsx`:

| Snap Screen | Current Label | Content |
|-------------|--------------|---------|
| Screen 1 | Executive Overview | 5 KPI cards + AI Summary + Sentiment Trend + Mentions by Source + Top Headlines |
| Screen 2 | Media Intelligence | Top Issues + Sources + Negative Mentions + Risk Gauge + India Map + Advocates |
| Screen 3 | Drill-Down Analysis | News RSS + Review Sites + Competitor Comparison + Virality Alerts |
| Screen 4 | Review Sites Intelligence | Full `ReviewSitesDashboard` page |
| Screen 5 | Drill-Down Explorer | `DrillDownScreen` (cascading filter + article list + article detail) |

**Navigation:** Sidebar tabs map to separate pages (`SourceBreakdown`, `TopicsView`, `JournalistCoverage`, `MentionsMonitor`, `ReviewQueue`, `UserManagement`, `BrandConfig`).

**Fundamental mismatch:** Current is a monitoring dashboard with data tables. Reference is an AI intelligence copilot with natural language interactions. The navigation paradigm and screen purposes differ entirely.

---

## Screen-by-Screen Gap Analysis

---

### SCREEN 1 — AI Executive Copilot

**Reference spec:** 30-second CEO briefing — Morning Brief (AI-generated greeting), "What Changed Since Yesterday" (swipeable timeline cards), AI Confidence Meter, Ask BrandPulse (chat interface). Actions: Explain, Summarize, Generate PPT.

**Current state (`Overview.tsx` Screen 1):**
- ✅ `AIExecutiveSummary` — 3-column (Situation / Root Cause / Recommended Actions) — close to the Morning Brief intent
- ✅ `KPICard` ×5 — Reputation Score (sparkline), Mentions (sparkline), SoV (donut), Risk (donut), Reach (sparkline)
- ✅ `SentimentTrendChart` — compact overlay, click to expand
- ✅ `AIExplainerChip` — on all 5 KPI cards (just shipped)
- ✅ `AIExplainerBanner` — auto-fires on reputation drop >10pts (just shipped)
- ❌ Morning Brief greeting ("Good Morning, [Name]. Brand reputation stable…")
- ❌ "What Changed Since Yesterday" — swipeable timeline diff cards
- ❌ AI Confidence Meter — overall model confidence % displayed prominently
- ❌ Ask BrandPulse — chat interface with example queries
- ❌ Speaker icon / Translate / Expand / Generate PPT actions
- ❌ Drill-down to "Detailed AI report with Evidence and Sources" via click
- ❌ Comparison with yesterday / prior period text ("Score increased by 4 pts. South improved.")

| Feature | Status | Rating |
|---------|--------|--------|
| Morning Brief / AI greeting | ❌ Missing | 0/10 |
| AI Executive Summary panel | ✅ Working (3-col layout) | 6/10 |
| What Changed Since Yesterday | ❌ Missing | 0/10 |
| AI Confidence Meter | ❌ Missing | 0/10 |
| Ask BrandPulse chat | ❌ Missing | 0/10 |
| KPI Cards (5 cards) | ✅ All 5 present + sparklines | 7/10 |
| AI Explainer Chips on KPI | ✅ Just shipped | 5/10 |
| Actions (PPT, Translate, Speak) | ❌ Missing | 0/10 |

**Screen 1 Composite: 3.2/10**

---

### SCREEN 2 — Intelligence Feed

**Reference spec:** LinkedIn/Bloomberg Terminal-style feed. "Stories That Matter" cards (headline + impact score + summary + Investigate/Watch/Ignore buttons). AI Issue Radar (animated floating topic bubbles with hover stats). Emerging Narratives (topic cloud, "5 new narratives in Tamil media").

**Current state (`Overview.tsx` Screen 2):**
- ✅ `TopIssuesTable` — Issue clusters with article counts, net sentiment, rising badges, split sentiment bar, top articles per cluster — clickable to drill-down
- ✅ `TopInfluentialSources` — Top 5 sources by impact score, sentiment, article count
- ✅ `TopNegativeMentions` — Highest-reach negative articles
- ✅ `ReputationRiskGauge` — Dial gauge with risk score + negative % + top issue label
- ✅ `TopBrandAdvocates` — Basic table (name, source, article count, reach)
- ✅ `IndiaStateMap` (regions variant) — click-to-drill state map
- ❌ Story cards (LinkedIn feed style) with **Investigate / Watch / Ignore** buttons
- ❌ **AI Issue Radar** — animated floating topic bubble clusters
- ❌ Impact Score badge (0–100) on individual stories
- ❌ Story summary text (AI-generated, 1–2 sentences per story)
- ❌ Emerging Narratives section with topic cloud
- ❌ "5 new narratives appearing in Tamil media" AI detection

| Feature | Status | Rating |
|---------|--------|--------|
| Stories That Matter (feed cards) | ❌ Missing | 0/10 |
| Investigate / Watch / Ignore actions | ❌ Missing | 0/10 |
| Impact Score per story | ❌ Missing | 0/10 |
| AI Issue Radar (animated clusters) | ❌ Missing | 0/10 |
| Issue clusters (TopIssuesTable) | ✅ Good data table, rising badge | 6/10 |
| Top Influential Sources | ✅ Working | 5/10 |
| Emerging Narratives / topic cloud | ❌ Missing | 0/10 |
| India State Map | ✅ Working | 6/10 |

**Screen 2 Composite: 2.1/10**

---

### SCREEN 3 — Situation Room

**Reference spec:** Live monitoring. Risk Copilot AI ("Medium risk. Probability of escalation: 62%"). Crisis Timeline (Netflix-style timeline — date + event + channel). "If This Continues" forecast (Tomorrow/3 Days/7 Days risk scores). Simulate Response button.

**Current state (`Overview.tsx` Screen 2 bottom half):**
- ✅ `ReputationRiskGauge` — SVG dial, risk score (0–100), colored zones, top issue label
- ✅ `IndiaStateMap` — regional sentiment (in current Screen 2 position)
- ✅ `TopBrandAdvocates` — basic advocate list
- ❌ No dedicated Situation Room screen
- ❌ Risk Copilot AI text ("Medium risk. Probability of escalation: 62%")
- ❌ Escalation probability % (ML forecast)
- ❌ "Show me why" button triggering AI explanation
- ❌ Crisis Timeline — Netflix-style annotated timeline ("18 June: Story detected → 20 June: Amplified → 22 June: YouTube discussion")
- ❌ "If This Continues" forecast with D+1/D+3/D+7 risk values
- ❌ Scenario Simulator ("If we respond → risk 48% / If silent → risk 74%")
- ❌ Real-time / live monitoring refresh

| Feature | Status | Rating |
|---------|--------|--------|
| Risk Copilot AI (escalation %) | ❌ Missing | 0/10 |
| Risk Gauge dial | ✅ SVG gauge working | 5/10 |
| Crisis Timeline (Netflix style) | ❌ Missing | 0/10 |
| Escalation probability forecast | ❌ Missing | 0/10 |
| D+1/D+3/D+7 risk forecast | ❌ Missing | 0/10 |
| "Show me why" AI drill | ❌ Missing | 0/10 |
| Scenario Simulator | ❌ Missing | 0/10 |

**Screen 3 Composite: 0.7/10**

---

### SCREEN 4 — Narrative Explorer

**Reference spec:** AI knowledge graph with brand at center, connected nodes for People / Media / Issues / Products. Click to expand → article evidence. Example: CavinKare → Controversy → Polimer → Influencer chain. Narrative DNA spider chart (Emotion: Fear / Intent: Criticism / Theme: Consumer trust).

**Current state:**
- ❌ No dedicated Narrative Explorer screen
- ❌ No knowledge graph component (D3 or recharts-based)
- ❌ No radial/force-layout graph
- ❌ No entity connection visualization
- ❌ No Narrative DNA spider/radar chart
- Partial analog: `TopIssuesTable` clusters show issue groups, `DrillDownScreen` shows articles per cluster — but no graph visualization
- Partial analog: `ArticleDetail` shows entities array — but not visualized as a graph

| Feature | Status | Rating |
|---------|--------|--------|
| AI Knowledge Graph | ❌ Missing | 0/10 |
| Radial entity layout (brand → entities) | ❌ Missing | 0/10 |
| Click-to-expand evidence drill | ❌ Missing | 0/10 |
| Narrative DNA spider chart | ❌ Missing | 0/10 |
| Issue entity grouping (data exists) | ⚠️ Partial (table form only) | 2/10 |

**Screen 4 Composite: 0.4/10**

---

### SCREEN 5 — Investigation Workspace

**Reference spec:** AI-enhanced drill-down. "Why This Happened" AI block (Coverage concentrated in Tamil channels. 3 influencers amplified. 2 reviews caused spike.). Entity Intelligence panel (CEO / Products / Competitors / Regulators detected). Influence Tree (Root source → Amplifiers → Consumers). Similar Historical Events ("This resembles XYZ crisis in 2024 — Recovered in 12 days").

**Current state (`DrillDownScreen` in snap Screen 5):**
- ✅ Cascading breadcrumb navigation (stack-based, up to 5 levels deep)
- ✅ `MentionsList` — filters: source type / state / sentiment / keyword / issue category / date range / source tier — article cards with metadata
- ✅ `ArticleDetail` — full article view: title, URL, source, date, sentiment score/label, language, entities, topics, keywords, states, author, editorial tone, issue category, reach metadata
- ✅ Click-to-drill from widgets to filtered article list
- ❌ "Why This Happened" AI explanation block (AIExplainerInline exists but NOT wired into DrillDownScreen)
- ❌ Entity Intelligence panel — detected CEO / Products / Competitors / Regulators (entities exist in article data but not aggregated/displayed as a named entity panel)
- ❌ Influence Tree — root source → amplifiers → consumer graph visualization
- ❌ Similar Historical Events — AI pattern matching
- ❌ Source count summary / timeline of spread

| Feature | Status | Rating |
|---------|--------|--------|
| Cascading drill-down (breadcrumb) | ✅ Working, 5-level deep | 7/10 |
| Article list with filters | ✅ Comprehensive filter set | 7/10 |
| Article detail view | ✅ Full metadata shown | 6/10 |
| "Why This Happened" AI block | ❌ Not wired (component exists) | 1/10 |
| Entity Intelligence panel | ❌ Missing (data exists in articles) | 0/10 |
| Influence Tree visualization | ❌ Missing | 0/10 |
| Similar Historical Events | ❌ Missing | 0/10 |

**Screen 5 Composite: 3.0/10**

---

### SCREEN 6 — Response Studio

**Reference spec:** AI Recommended Actions (priority list), AI Content Generator (Press release / FAQ / Tweet / LinkedIn / CEO statement), Approval Workflow (PR Head → Legal → CEO, status: Pending), Scenario Simulator (respond → 48% / silent → 74%).

**Current state:**
- ⚠️ `DrillDownJourneyExample` — a placeholder/demo component showing the drill journey concept, not a real feature
- ❌ No dedicated Response Studio screen
- ❌ AI Recommended Actions (no endpoint or UI)
- ❌ AI Content Generator (no endpoint or UI)
- ❌ Approval Workflow (no database table, no UI)
- ❌ Scenario Simulator (no model, no UI)
- ❌ Story actions (Watch/Investigate/Ignore) — migration `030_story_actions.sql` planned but not executed

| Feature | Status | Rating |
|---------|--------|--------|
| AI Recommended Actions | ❌ Missing | 0/10 |
| AI Content Generator | ❌ Missing | 0/10 |
| Approval Workflow | ❌ Missing | 0/10 |
| Scenario Simulator | ❌ Missing | 0/10 |
| Response tracking | ❌ Missing | 0/10 |

**Screen 6 Composite: 0/10**

---

### SCREEN 7 — Advocacy Hub

**Reference spec:** Emerging Advocates (AI found 12 creators with scores: Affinity, Influence, Trust). Relationship Memory (past interactions: samples sent, campaigns). Suggested Engagements (Podcast / Review / Event invite).

**Current state:**
- ✅ `TopBrandAdvocates` — shows top creators from YouTube/Blog/Reddit with article count + total reach. Data-driven from `portal_id` + `source_type` grouping
- ❌ Affinity / Influence / Trust scoring (currently only article count + reach)
- ❌ AI discovery — "AI found 12 creators" (currently just top-N by reach/count)
- ❌ Relationship Memory (no database table, no interaction history)
- ❌ Suggested Engagements (no recommendation logic)
- ❌ Creator profiles with social links / contact info

| Feature | Status | Rating |
|---------|--------|--------|
| Advocate list (basic) | ✅ Working — article count + reach | 3/10 |
| AI discovery ("AI found X") | ❌ Missing | 0/10 |
| Affinity / Influence / Trust scores | ❌ Missing | 0/10 |
| Relationship Memory | ❌ Missing | 0/10 |
| Suggested Engagements | ❌ Missing | 0/10 |

**Screen 7 Composite: 0.6/10**

---

### SCREEN 8 — Geo Intelligence

**Reference spec:** AI Regional Summary text ("South India sentiment improving. West declining. North stable."). "Explain Geography" — AI explains why Tamil Nadu negative (TV debate, YouTube videos, Reviews). Map with regional sentiment heat.

**Current state:**
- ✅ `IndiaStateMap` — full SVG India map with per-state sentiment (positive/negative/neutral count + %) — click-to-drill-down
- ✅ State-level data from `state_breakdown` endpoint
- ✅ Region variant (`variant="regions"`) on Screen 2 showing North/South/East/West/Central groupings
- ❌ AI Regional Summary text block (no "South improving, West declining" AI sentence)
- ❌ "Explain Geography" — `state_sentiment` metric in `POST /dashboard/explain` exists, but NOT wired to a button on the map
- ❌ Regional trend lines / sparklines alongside the map
- ❌ State-level brand comparison vs competitors

| Feature | Status | Rating |
|---------|--------|--------|
| India map with state sentiment | ✅ Full SVG map working | 7/10 |
| Click-to-drill per state | ✅ Working | 7/10 |
| AI Regional Summary text | ❌ Missing | 0/10 |
| Explain Geography button | ❌ Endpoint exists, UI missing | 1/10 |
| Regional trend sparklines | ❌ Missing | 0/10 |

**Screen 8 Composite: 3.0/10**

---

### SCREEN 9 — Executive Board Mode

**Reference spec:** Designed for CEOs. No charts — only answers. Top 5 Things You Need To Know. Top 3 Risks. Top 5 Opportunities. Competitor Movements. Actions Awaiting Approval. AI Recommendation ("Schedule media engagement within 48 hours.") with Confidence: 91%.

**Current state:**
- ❌ No Executive Board Mode screen exists
- ❌ No CEO-mode toggle / view
- ❌ Top 5 Things / Top 3 Risks / Top 5 Opportunities (no AI generation)
- ❌ Competitor Movements summary
- ❌ Actions Awaiting Approval
- ❌ AI Recommendation with confidence %
- Analog: `AIExecutiveSummary` shows 3 recommended actions — far below Board Mode spec

| Feature | Status | Rating |
|---------|--------|--------|
| Board Mode screen | ❌ Missing | 0/10 |
| Top 5 Things You Need To Know | ❌ Missing | 0/10 |
| Top 3 Risks | ❌ Missing | 0/10 |
| Top 5 Opportunities | ❌ Missing | 0/10 |
| Competitor Movements | ❌ Missing | 0/10 |
| AI Recommendation (confidence %) | ❌ Missing | 0/10 |

**Screen 9 Composite: 0/10**

---

## Universal AI Widgets

---

### Universal Widget 1 — AI Ask Bar

**Reference spec:** Appears on every screen. Persistent bottom/top bar. Example queries: "Explain decline / Predict crisis / Generate summary / Find advocates / Compare competitors / Draft response / Show hidden trends."

**Current state:**
- ❌ No AI Ask Bar exists anywhere in the UI
- ❌ No conversational input
- ❌ No streaming AI response
- ❌ No query suggestions

| Feature | Status | Rating |
|---------|--------|--------|
| Ask Bar UI (input + send) | ❌ Missing | 0/10 |
| Streaming AI response | ❌ Missing | 0/10 |
| Example query suggestions | ❌ Missing | 0/10 |
| Persistent across screens | ❌ Missing | 0/10 |

**Ask Bar Composite: 0/10**

---

### Universal Widget 2 — AI Insight Chips

**Reference spec:** Floating chips appearing contextually: "Negative reviews increased / Tamil media impact / Competitor campaign detected / Advocacy opportunity / Escalation warning."

**Current state:**
- ✅ `AIExplainerChip` — ships on all 5 KPI cards; click-to-fetch from `/dashboard/explain`; shows tooltip with headline/confidence/drivers/evidence/action
- ⚠️ Limited to KPI cards only — not yet on article cards, source cards, or state map cells
- ⚠️ On-demand only — user must click; no auto-surfaced chips
- ❌ Auto-generated chips that surface proactively ("Tamil media impact" appearing without user interaction)
- ❌ Chips on story cards (Intelligence Feed)
- ❌ Chips on advocate cards (Advocacy Hub)
- ❌ Chips on map regions (Geo Intelligence)

| Feature | Status | Rating |
|---------|--------|--------|
| Chip component (click-to-explain) | ✅ Working on KPI cards | 5/10 |
| Tooltip/popover with AI content | ✅ Working (AIExplainerTooltip) | 5/10 |
| Auto-surfaced contextual chips | ❌ Missing (all on-demand) | 0/10 |
| Chips on story cards | ❌ Not wired | 0/10 |
| Chips across all screens | ❌ KPI cards only | 2/10 |

**Insight Chips Composite: 2.4/10**

---

### Universal Widget 3 — AI Co-Pilot Drawer

**Reference spec:** Persistent right panel. Ask questions, Generate reports, Translate, Export PPT, Email summary, Create meeting notes.

**Current state:**
- ✅ `AIExplainerDrawer` — right-side slide-in drawer (400px), fetches `/dashboard/explain`, shows headline/confidence/drivers/evidence/action, copy to clipboard
- ⚠️ Metric-specific only — triggered from individual KPI chips, not a universal co-pilot
- ❌ Not persistent — not always-available on every screen
- ❌ No Translate capability
- ❌ No Export PPT / Email summary
- ❌ No conversational multi-turn capability
- ❌ No "Create meeting notes" generation

| Feature | Status | Rating |
|---------|--------|--------|
| Drawer UI (slide-in 400px panel) | ✅ Working | 6/10 |
| AI explanation content | ✅ Working (metric-specific) | 5/10 |
| Universal co-pilot (ask anything) | ❌ Missing | 0/10 |
| Translate | ❌ Missing | 0/10 |
| Export PPT / Email | ❌ Missing | 0/10 |
| Persistent (all screens) | ❌ Not persistent | 0/10 |

**Co-Pilot Drawer Composite: 1.8/10**

---

## Navigation Architecture Gap

| Dimension | Reference Vision | Current Implementation | Gap |
|-----------|-----------------|----------------------|-----|
| Navigation paradigm | 9 dedicated intelligence screens | Single `Overview.tsx` + sidebar tabs to separate pages | Fundamental mismatch |
| Screen routing | Screen 1–9 as named routes or tabs | Vertical snap-scroll within Overview | Navigation model wrong |
| URL structure | `/executive-copilot`, `/intelligence-feed`, etc. | `/` + sidebar tab state | No dedicated routes |
| Screen persistence | Each screen remembers state | Snap-scroll resets on tab change | State not preserved |
| Transition style | Reference shows grid/card navigation | Snap-scroll vertical | Visual paradigm different |
| Mobile / responsive | Reference is clearly desktop-first | Current is also desktop-first | Aligned |
| Sidebar role | Universal AI Co-Pilot Drawer | Data source filters + admin tabs | Purpose mismatch |

---

## Additional Features Audit (Pages/Components not in ScreenFlow)

These features exist in the current codebase but are not in the ScreenFlow reference. They add analytical depth but need to be mapped to the new screen architecture:

| Current Feature | Current Location | Map to ScreenFlow Screen |
|----------------|-----------------|--------------------------|
| `JournalistCoverage` (journalist profiles + beat detection) | Sidebar → Journalists | Screen 5: Investigation Workspace |
| `ReviewQueue` (human review of AI-flagged articles) | Sidebar → Review Queue | Screen 6: Response Studio (Approval Workflow) |
| `MentionsMonitor` (real-time article feed) | Sidebar → Mentions Monitor | Screen 2: Intelligence Feed |
| `ViralityAlertsPanel` (virality flag detection) | Overview Screen 3 | Screen 3: Situation Room |
| `ReviewSitesDashboard` (Google/App Store/review analysis) | Overview Screen 4 | Screen 7: Advocacy Hub or Screen 2 |
| `CompetitorComparison` (competitor sentiment bars) | Overview Screen 3 | Screen 9: Board Mode (Competitor Movements) |
| `EditorialToneChart` (factual/positive/critical weekly bars) | Panel on click | Screen 5: Investigation Workspace |
| `YouTubeSentimentSplit` (creator vs audience sentiment) | Panel on click | Screen 5: Investigation Workspace |
| `BrandRiskScores` (per-video risk scoring) | Backend only | Screen 3: Situation Room |
| `NewsRSSMentionsPanel` (filterable article feed) | Overview Screen 3 | Screen 2: Intelligence Feed |

---

## Composite Score Summary

| Screen / Widget | Current Score | Target (Reference) | Gap |
|----------------|---------------|--------------------|-----|
| Screen 1: AI Executive Copilot | **3.2 / 10** | 10/10 | -6.8 |
| Screen 2: Intelligence Feed | **2.1 / 10** | 10/10 | -7.9 |
| Screen 3: Situation Room | **0.7 / 10** | 10/10 | -9.3 |
| Screen 4: Narrative Explorer | **0.4 / 10** | 10/10 | -9.6 |
| Screen 5: Investigation Workspace | **3.0 / 10** | 10/10 | -7.0 |
| Screen 6: Response Studio | **0.0 / 10** | 10/10 | -10.0 |
| Screen 7: Advocacy Hub | **0.6 / 10** | 10/10 | -9.4 |
| Screen 8: Geo Intelligence | **3.0 / 10** | 10/10 | -7.0 |
| Screen 9: Executive Board Mode | **0.0 / 10** | 10/10 | -10.0 |
| Universal: AI Ask Bar | **0.0 / 10** | 10/10 | -10.0 |
| Universal: AI Insight Chips | **2.4 / 10** | 10/10 | -7.6 |
| Universal: AI Co-Pilot Drawer | **1.8 / 10** | 10/10 | -8.2 |
| **COMPOSITE TOTAL** | **17.2 / 120** | 120/120 | **-102.8** |

> **Overall: 14.3% of reference vision implemented.**

---

## Feature-Level Priority Matrix

Sorted by: Impact on composite score × Implementation effort (low-medium-high)

### Tier 1 — Quick Wins (implement in 1–2 sessions, +15–20 pts)

| Feature | Screens Impacted | Score Gain | Effort |
|---------|-----------------|------------|--------|
| AI Ask Bar (POST /dashboard/chat, streaming SSE) | All screens | +8 pts | Medium |
| Morning Brief widget (personalized greeting + delta text) | Screen 1 | +3 pts | Low |
| Wire AIExplainerInline into DrillDownScreen ("Why This Happened") | Screen 5 | +3 pts | Low |
| AI Regional Summary text on India map | Screen 8 | +3 pts | Low |
| "Explain Geography" button on state map click | Screen 8 | +2 pts | Low |

### Tier 2 — Core Intelligence Features (+20–30 pts)

| Feature | Screens Impacted | Score Gain | Effort |
|---------|-----------------|------------|--------|
| Stories That Matter feed (Investigate/Watch/Ignore) | Screen 2 | +6 pts | Medium |
| Risk Copilot AI (escalation %, "Show me why") | Screen 3 | +5 pts | Medium |
| Crisis Timeline widget (event annotation + timeline) | Screen 3 | +4 pts | Medium |
| "If This Continues" D+1/D+3/D+7 forecast | Screen 3 | +4 pts | Medium |
| AI Issue Radar (recharts ScatterChart radial layout) | Screen 2 | +5 pts | Medium |
| Executive Board Mode screen (text-only CEO view) | Screen 9 | +6 pts | Medium |

### Tier 3 — Advanced AI Features (+20–30 pts)

| Feature | Screens Impacted | Score Gain | Effort |
|---------|-----------------|------------|--------|
| Knowledge Graph — recharts radial entity graph | Screen 4 | +7 pts | High |
| AI Content Generator (press release/tweet/LinkedIn) | Screen 6 | +5 pts | Medium |
| Approval Workflow (PR Head/Legal/CEO chain) | Screen 6 | +4 pts | Medium |
| Influence Tree (root → amplifier → consumer) | Screen 5 | +4 pts | High |
| Entity Intelligence panel | Screen 5 | +3 pts | Medium |
| Advocate AI discovery (affinity/trust/influence) | Screen 7 | +4 pts | Medium |

### Tier 4 — Stretch Features (+10–15 pts)

| Feature | Screens Impacted | Score Gain | Effort |
|---------|-----------------|------------|--------|
| Narrative DNA spider/radar chart | Screen 4 | +3 pts | Medium |
| Scenario Simulator | Screen 6 | +3 pts | High |
| Similar Historical Events | Screen 5 | +3 pts | High |
| Relationship Memory (advocate CRM) | Screen 7 | +3 pts | High |
| Persistent Co-Pilot Drawer (all screens) | Universal | +4 pts | Medium |
| PPT/Email export | Universal | +2 pts | Medium |

---

## Navigation Architecture Recommendation

To bridge the gap from current to reference, the navigation needs restructuring:

**Option A — Screen tabs inside Overview (recommended for fastest delivery):**
Replace the current snap-scroll with 9 named tabs at the top of the Overview page. Each tab loads its screen as a component. Preserves the single-page architecture, avoids routing changes, keeps sidebar as-is.

**Option B — Dedicated routes:**
Add `/copilot`, `/feed`, `/situation`, `/narrative`, `/investigate`, `/response`, `/advocacy`, `/geo`, `/board` routes. Requires router changes but gives clean URLs and deep linking.

**Option C — Hybrid (current + new sidebar):**
Add a second sidebar section "AI Intelligence" with the 9 screens as links, keeping existing admin/config sidebar items.

---

## Implementation Sequence

Based on score impact and dependencies:

```
Sprint 1 (Sessions 1-2):  Screen 1 complete + Universal AI Ask Bar         → ~28/120
Sprint 2 (Sessions 3-4):  Screen 2 Intelligence Feed + Screen 3 Situation  → ~45/120
Sprint 3 (Sessions 5-6):  Screen 5 Investigation + Screen 8 Geo            → ~60/120
Sprint 4 (Sessions 7-8):  Screen 9 Board Mode + Screen 6 Response Studio   → ~75/120
Sprint 5 (Sessions 9-10): Screen 4 Narrative + Screen 7 Advocacy           → ~90/120
Sprint 6 (Sessions 11+):  Universal widgets full + polish + PPT/export      → ~105/120
```

---

## Key Gaps Summary (one-line each)

1. **No conversational AI** — zero chat or streaming anywhere in the current UI
2. **No story card feed** — TopIssuesTable is a data table, not a LinkedIn-style story card with actions
3. **No crisis intelligence** — no escalation probability, no crisis timeline, no risk forecast
4. **No knowledge graph** — narrative explorer screen does not exist; entity data is buried in article detail
5. **No response capability** — no content generation, no approval workflow, no scenario simulation
6. **No board mode** — no CEO-facing text-only summary screen
7. **No investigation AI** — DrillDownScreen has filters and articles but no "Why This Happened" AI block
8. **No advocate intelligence** — TopBrandAdvocates is a basic table; no AI scoring or engagement suggestions
9. **AI Explainer is partial** — Chips + Drawer + Inline exist but not wired across all surfaces
10. **Navigation paradigm mismatch** — 5 scroll-snap screens vs. 9 named intelligence screens

---

*Generated by gap audit of commit `7a65071` against reference image `ChatGPT Image Jun 23, 2026, 05_04_11 PM.png` and `ScreenFlow.md`.*
