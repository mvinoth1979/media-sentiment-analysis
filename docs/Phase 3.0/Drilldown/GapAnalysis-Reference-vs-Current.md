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

---
---

# IMPLEMENTATION PLAN — 17.2 → 100 / 120
## "How to reach 100/120 from the current 17.2/120"

---

## Score Targets Per Screen

| Screen / Widget | Current | Target | Gain | Achievability Note |
|----------------|---------|--------|------|--------------------|
| Screen 1: AI Executive Copilot | 3.2 | **9.0** | +5.8 | Morning Brief + Ask Chat + Confidence Meter |
| Screen 2: Intelligence Feed | 2.1 | **9.0** | +6.9 | Story cards + AI Issue Radar + Emerging Narratives |
| Screen 3: Situation Room | 0.7 | **8.0** | +7.3 | Risk Copilot + Crisis Timeline + D+7 forecast |
| Screen 4: Narrative Explorer | 0.4 | **7.0** | +6.6 | recharts radial graph + Narrative DNA radar |
| Screen 5: Investigation Workspace | 3.0 | **9.0** | +6.0 | AI Why block wired + Entity Intel + Influence Tree |
| Screen 6: Response Studio | 0.0 | **9.0** | +9.0 | Content Generator + Approval Workflow + Scenario Sim |
| Screen 7: Advocacy Hub | 0.6 | **7.0** | +6.4 | AI scores + Suggested Engagements + Relationship Memory |
| Screen 8: Geo Intelligence | 3.0 | **9.0** | +6.0 | AI Regional Summary + Explain Geography button |
| Screen 9: Executive Board Mode | 0.0 | **9.0** | +9.0 | Full CEO screen (text-only, no charts) |
| Universal: AI Ask Bar | 0.0 | **9.0** | +9.0 | Streaming SSE chat, all screens |
| Universal: AI Insight Chips | 2.4 | **7.0** | +4.6 | Auto-surfaced chips, story/map/entity surfaces |
| Universal: AI Co-Pilot Drawer | 1.8 | **8.0** | +6.2 | Universal persistent drawer + translate + email |
| **TOTAL** | **17.2** | **100.0** | **+82.8** | |

---

## Phase Architecture

```
PHASE 1 (Sessions 1–3):  Conversation AI + Screen 1 complete + Screen 8  → ~40/120
PHASE 2 (Sessions 4–6):  Intelligence Feed (S2) + Situation Room (S3)    → ~60/120
PHASE 3 (Sessions 7–9):  Investigation AI (S5) + Narrative (S4) + Board  → ~82/120
PHASE 4 (Sessions 10–12): Response Studio (S6) + Advocacy (S7) + Polish  → ~100/120
```

Each session follows the execution protocol:
- `[SEQ]` — Must run first (migrations, schema changes, shared registration)
- `[A1] [A2] [A3]` — Parallel agents for independent files

---

## PHASE 1 — Conversation AI Layer
### Sessions 1–3 · Score: 17.2 → 40/120

**Phase 1 Goal:** Give every screen a voice. The AI Ask Bar is the single highest-impact feature (+9 pts alone) because it transforms the product from a monitoring tool into a conversational intelligence platform. Build it first, then complete Screen 1 and Screen 8.

---

### SESSION 1 — AI Ask Bar (Streaming SSE Chat)
**Score impact:** Ask Bar 0→9 (+9) → **26.2/120**

#### [SEQ] Backend — `POST /dashboard/chat`

**File:** `backend/app/dashboard/router.py`

```python
# New SSE streaming endpoint after the explain endpoint

_CHAT_SYSTEM = (
    "You are BrandPulse AI, a media intelligence analyst. "
    "Brand: {brand_name}. Coverage period: last {days} days.\n"
    "Context: {total} articles — {pos_pct}% positive, {neg_pct}% negative. "
    "Top issues: {top_issues}. Top sources: {top_sources}.\n"
    "Recent negative headlines: {neg_headlines}\n\n"
    "Answer the user's question concisely and specifically. "
    "Always reference the actual data above — never give generic answers. "
    "If asked to predict, use trend direction from the data. "
    "If asked to generate content, produce it directly."
)

@router.post("/chat")
def chat_with_brand(
    req: ChatRequest,         # { message: str, brand_id: str, context_messages: list[dict] = [] }
    days: int = Query(7, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    # Fetch brand context (same pattern as explain endpoint)
    # Build system prompt with brand articles
    # Call Gemini, stream tokens as SSE: data: {"token": "...", "done": false}
    # Final: data: {"token": "", "done": true, "confidence_pct": N}
    return StreamingResponse(generate_chat_stream(...), media_type="text/event-stream")
```

**New schemas in `dashboard/schemas.py`:**
```python
class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    brand_id: str
    context_messages: list[ChatMessage] = []
```

**Gemini streaming pattern:**
```python
async def generate_chat_stream(prompt, context, api_key, model):
    client = _genai.Client(api_key=api_key)
    full_response = client.models.generate_content(model=model, contents=prompt)
    # Word-by-word streaming simulation (Gemini SDK returns full response)
    for word in full_response.text.split():
        yield f'data: {{"token": "{word} ", "done": false}}\n\n'
    yield f'data: {{"token": "", "done": true}}\n\n'
```

#### [A1] Frontend — `AskBar.tsx`

**File:** `frontend/src/components/AskBar.tsx`

```tsx
// Fixed-position bar that appears at the bottom of Overview on all screens
// Props: { brandId: string; days?: number; }
// State: open (bool), message (str), thread (ChatMessage[]), streaming (bool)
// On send: fetch POST /dashboard/chat with EventSource/ReadableStream
// Stream tokens into last assistant bubble in real-time
// Show example query chips: "Why did sentiment drop?" | "What's the top risk?" | "Compare with competitors"
// CSS: fixed bottom-4 left-[72px] right-4 z-30 (72px = sidebar width)
//      bg-[#1a2744] border border-white/10 rounded-2xl shadow-2xl
// Two modes:
//   Collapsed: single input row (height ~48px)
//   Expanded: input + ChatThread above it (max-h-96 overflow-y-auto)
```

#### [A2] Frontend — `ChatThread.tsx`

**File:** `frontend/src/components/ChatThread.tsx`

```tsx
// Renders message history as chat bubbles
// Props: { messages: ChatMessage[]; isStreaming?: boolean; }
// User bubble: right-aligned, bg-blue-600/30 text-white text-sm rounded-2xl px-3 py-2
// AI bubble: left-aligned, bg-white/5 text-white/85 text-sm rounded-2xl px-3 py-2
//   Shows typing cursor (blinking |) when isStreaming=true on last bubble
// Auto-scrolls to bottom on new token
```

#### [A3] Wire AskBar into Overview.tsx

- Add `import { AskBar } from "../components/AskBar"` to `Overview.tsx`
- Render `<AskBar brandId={brandId} days={days} />` just before the closing `</div>` of the snap-scroll container (it's fixed-position so renders above all screens)

**Acceptance criteria:**
- User types "Why did sentiment drop?" → streams AI answer referencing actual articles
- Enter key or Send button sends message
- Esc closes expanded mode
- Works on all 5 snap-scroll screens simultaneously

---

### SESSION 2 — Morning Brief + What Changed + AI Confidence Meter
**Score impact:** Screen 1 3.2→7.5 (+4.3) → **30.5/120**

#### [SEQ] Backend — `GET /dashboard/morning-brief/{brand_id}`

**File:** `backend/app/dashboard/router.py`

```python
class MorningBriefResponse(BaseModel):
    greeting: str           # "Good morning. Brand reputation stable."
    score_change: float     # +4.2 (delta vs 7 days ago)
    score_direction: str    # "up" | "down" | "stable"
    highlights: list[str]  # ["Score increased by 4 pts", "South sentiment improved", "1 issue requires attention"]
    confidence_pct: int
    generated_at: str

@router.get("/morning-brief/{brand_id}", response_model=MorningBriefResponse)
def get_morning_brief(brand_id: str, days: int = Query(7), _user=Depends(...)):
    # Fetch KPI (current + prior period)
    # Compute score_change = current_perception - prior_perception
    # Build 3-4 highlights from data (score, regional trend, top risk, top positive)
    # Call Gemini to write a 1-sentence greeting
    # Cache for 60 minutes
```

#### [A1] Frontend — `MorningBrief.tsx`

**File:** `frontend/src/components/MorningBrief.tsx`

```tsx
// Props: { brandId: string; queryParams: {...} }
// Uses useQuery to call GET /dashboard/morning-brief/{brandId}
// Layout: large card (full width of Screen 1 top section)
//   Left: greeting text (text-lg font-semibold text-white)
//         + 3-4 highlight bullet points (text-sm text-white/70)
//   Right: score change badge (+4 pts ▲) + timestamp
// CSS: bg-[#1a2744] border border-white/10 rounded-xl px-5 py-4
//      Speaker icon (🔊) and Expand icon (⛶) in top-right (stubs for now)
// Skeleton: 3 animated lines
```

#### [A2] Frontend — `WhatChangedCards.tsx`

**File:** `frontend/src/components/WhatChangedCards.tsx`

```tsx
// Props: { brandId: string; days: number }
// Calls GET /dashboard/ai-summary/{brandId} (existing endpoint)
// Renders data.actions as swipeable horizontal timeline cards
// Each card: icon + date label + change description
// CSS: horizontal flex overflow-x-auto gap-3 scrollbar-none
//      Each card: flex-shrink-0 w-48 bg-[#1a2744] border border-white/10 rounded-xl px-3 py-3
//      Left border color by sentiment: green (positive change), red (negative), gray (neutral)
// 3 events: What Changed (situation), Root Cause (why), Action Required
```

#### [A3] Frontend — `AIConfidenceMeter.tsx` + Screen 1 layout update

**File:** `frontend/src/components/AIConfidenceMeter.tsx`

```tsx
// Props: { pct: number; label?: string }
// SVG arc meter (180-degree semicircle, stroke-dasharray trick)
// Colors: <40% red, 40-70% amber, >70% green
// Center text: "{pct}%" in text-2xl + "AI Confidence" in text-[10px]
// Size: ~80×48px compact widget
```

**Update `Overview.tsx` Screen 1:**
- Replace current Row 2 layout: `[MorningBrief full-width]` on top
- Below: `[AIConfidenceMeter] [WhatChangedCards scrollable]` in a 2-col grid
- Keep existing `[AIExecutiveSummary | SentimentTrendChart]` row below that

---

### SESSION 3 — Screen 8 AI Regional Summary + Explain Geography + Wire Inline
**Score impact:** Screen 8 3→9 (+6.0), Screen 5 3→5 (+2.0) → **40.5/120**

#### [SEQ] Backend — `GET /dashboard/regional-summary/{brand_id}`

**File:** `backend/app/dashboard/router.py`

```python
class StateHighlight(BaseModel):
    state: str
    direction: str          # "improving" | "declining" | "stable"
    reason: str             # "Driven by Tamil TV coverage"
    sentiment_pct: float    # dominant sentiment %
    dominant_sentiment: str # "negative" | "positive"

class RegionalSummaryResponse(BaseModel):
    summary: str            # "South India sentiment improving. West declining. North stable."
    state_highlights: list[StateHighlight]  # top 5 notable states
    confidence_pct: int
    generated_at: str

@router.get("/regional-summary/{brand_id}", response_model=RegionalSummaryResponse)
def get_regional_summary(brand_id: str, days: int = Query(30), _user=Depends(...)):
    # Get state_breakdown data (existing endpoint pattern)
    # Compute top improving / declining states by comparing positive_pct
    # Group into North/South/East/West/Central regions
    # Call Gemini with regional breakdown data
    # Return structured response + 60-min cache
```

#### [A1] Frontend — `AIRegionalSummary.tsx`

**File:** `frontend/src/components/AIRegionalSummary.tsx`

```tsx
// Props: { brandId: string; days: number; onStateExplain?: (state: string) => void }
// Calls GET /dashboard/regional-summary/{brandId}
// Layout: text block with 3-5 state highlight pills below it
//   Summary line: text-sm text-white/80 (e.g. "South India sentiment improving")
//   State pills: [ 🟢 Tamil Nadu +12% ] [ 🔴 Karnataka -8% ]
//   "Explain →" link per state that calls onStateExplain(state)
// CSS: bg-[#1a2744] border border-white/10 rounded-xl px-4 py-3
```

**Update `IndiaStateMap.tsx`:**
- Add optional `onExplain?: (state: string) => void` prop
- In the state click popup/tooltip, add "🧠 Explain" button that calls `onExplain(state)`
  which triggers AIExplainerChip with `metric="state_sentiment"` and `context: { state }`

**Update `Overview.tsx` Screen 2 (India Map section):**
- Wrap `IndiaStateMap` + `AIRegionalSummary` in a stacked layout
- `AIRegionalSummary` renders below the map

#### [A2] Wire `AIExplainerInline` into `DrillDownScreen.tsx`

**File:** `frontend/src/components/DrillDown/DrillDownScreen.tsx`

- Import `AIExplainerInline` from `../explainer/AIExplainerInline`
- Add a thin "AI Analysis" section between the breadcrumb bar and the article list
- Render: `<AIExplainerInline metric="investigation_context" brandId={brandId} context={{ topic: current.label }} autoLoad={false} />`
- The component is already built — just needs to be imported and placed

#### [A3] Screen 1 final polish + AskBar refinement

- Add example query suggestions as clickable chips in the AskBar collapsed state
- Add keyboard shortcut: `Cmd/Ctrl + K` to open AskBar from any screen
- Add "Generating…" animated indicator in MorningBrief while loading

---

## PHASE 2 — Intelligence Feed + Situation Room
### Sessions 4–6 · Score: 40 → 60/120

**Phase 2 Goal:** Transform the passive data screens into active intelligence surfaces. Screen 2 becomes a live feed of "things that matter" and Screen 3 becomes a proactive risk watch.

---

### SESSION 4 — Stories That Matter + story_actions Migration
**Score impact:** Screen 2 2.1→5.5 (+3.4) → **63.9/120**

#### [SEQ] Database migration — `030_story_actions.sql`

```sql
-- Story actions: Watch / Investigate / Ignore per article per user
CREATE TABLE IF NOT EXISTS story_actions (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id    uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    article_id  uuid NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    action      text NOT NULL CHECK (action IN ('watch','investigate','ignore')),
    user_id     uuid REFERENCES auth.users(id),
    notes       text,
    created_at  timestamptz DEFAULT now(),
    UNIQUE (brand_id, article_id, user_id)   -- one action per user per article
);
CREATE INDEX idx_story_actions_brand ON story_actions(brand_id, created_at DESC);

-- Generated content (Response Studio — used in Phase 4 too)
CREATE TABLE IF NOT EXISTS generated_content (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id        uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    content_type    text NOT NULL,   -- press_release / faq / tweet / linkedin / ceo_statement
    content_text    text NOT NULL,
    context_json    jsonb DEFAULT '{}',
    status          text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','pending','approved','rejected')),
    created_by      uuid REFERENCES auth.users(id),
    approved_by     uuid REFERENCES auth.users(id),
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);
CREATE INDEX idx_generated_content_brand ON generated_content(brand_id, created_at DESC);
```

#### [SEQ] Backend — `GET /dashboard/story-feed/{brand_id}` + `POST /dashboard/story-action`

```python
class StoryCard(BaseModel):
    article_id: str
    title: str
    url: str
    portal_name: str
    published_at: str | None
    sentiment_label: str
    impact_score: int       # 0-100: computed from reach × sentiment_intensity × credibility
    ai_summary: str | None  # 1-sentence AI summary (Gemini, cached)
    source_type: str
    action: str | None      # "watch" | "investigate" | "ignore" | None (user's existing action)

class StoryFeedResponse(BaseModel):
    stories: list[StoryCard]
    total: int

@router.get("/story-feed/{brand_id}", response_model=StoryFeedResponse)
def get_story_feed(brand_id: str, days: int = Query(7), limit: int = Query(20), _user=Depends(...)):
    # Fetch articles sorted by reach_score DESC
    # Compute impact_score = round(reach_normalized * abs(sentiment_score) * credibility * 100)
    # Join with story_actions to get each user's current action
    # Return StoryFeedResponse

@router.post("/story-action")
def log_story_action(req: StoryActionRequest, _user=Depends(...)):
    # req: { brand_id, article_id, action }
    # Upsert into story_actions table
```

#### [A1] Frontend — `StoryFeedCard.tsx`

**File:** `frontend/src/components/StoryFeedCard.tsx`

```tsx
// LinkedIn/newsroom-style story card
// Props: { story: StoryCard; brandId: string; onAction: (action: string) => void }
// Layout:
//   Row 1: [Impact Score badge] [portal_name · time ago]  [sentiment badge]
//   Row 2: [Title — text-sm font-semibold text-white leading-snug] (max 2 lines)
//   Row 3: [ai_summary — text-xs text-white/60] (if present)
//   Row 4: [🔍 Investigate] [👁 Watch] [✗ Ignore] buttons + [🧠 Explain chip]
// Impact Score badge: 0-40=green, 41-70=amber, 71-100=red
//   "89 Impact" in bold, colored bg pill top-left of card
// Action buttons: 3 small outlined buttons that call POST /dashboard/story-action
//   Active action: filled button (user's current action highlighted)
// CSS: bg-[#1a2744] border border-white/10 rounded-xl p-3 hover:border-white/20
```

#### [A2] Frontend — `StoriesFeed.tsx`

**File:** `frontend/src/components/StoriesFeed.tsx`

```tsx
// Props: { brandId: string; days: number; onDrillDown?: (title: string, filters: DrillFilters) => void }
// Calls GET /dashboard/story-feed/{brandId} via useQuery
// Renders StoryFeedCard list with vertical scroll
// Header: "Stories That Matter" + article count + "↑ Sorted by impact"
// Filter row: [All | High Impact | Investigate | Watching]
// Infinite scroll: load 20 more on scroll-to-bottom
// Loading: 3 skeleton cards (pulsing bg-[#1a2744] rounded-xl h-24)
// Empty state: "No high-impact stories in the last {days} days"
```

#### [A3] Update Screen 2 layout in Overview.tsx

- Replace `TopHeadlines` in Screen 2 top-right with `StoriesFeed` component
- Keep `TopIssuesTable` and `TopInfluentialSources` in Screen 2 top-left and center
- Update imports

---

### SESSION 5 — AI Issue Radar (animated topic clusters)
**Score impact:** Screen 2 5.5→9 (+3.5) → **67.4/120**

#### [SEQ] Backend — `GET /dashboard/issue-radar/{brand_id}`

```python
class IssueRadarCluster(BaseModel):
    name: str               # "product_quality" → "Product Quality"
    count: int              # article count
    velocity: float         # articles per day (last 7d vs prior 7d ratio)
    sentiment_score: float  # -1.0 to +1.0
    size: int               # bubble size (10-60, log scale of count)
    color: str              # "#ef4444" red / "#f59e0b" amber / "#22c55e" green

class IssueRadarResponse(BaseModel):
    clusters: list[IssueRadarCluster]
    brand_id: str
    period_days: int

@router.get("/issue-radar/{brand_id}", response_model=IssueRadarResponse)
def get_issue_radar(brand_id: str, days: int = Query(30), _user=Depends(...)):
    # Fetch articles, group by issue_category
    # Compute velocity = (last_7d_count / max(prior_7d_count, 1)) - 1.0
    # Compute bubble size = max(10, min(60, round(log(count+1)*15)))
    # Color from sentiment_score: <-0.2 red, -0.2 to +0.2 amber, >+0.2 green
    # Return top 12 clusters sorted by count DESC
```

#### [A1] Frontend — `AIIssueRadar.tsx`

**File:** `frontend/src/components/AIIssueRadar.tsx`

```tsx
// recharts ScatterChart in radial layout (no D3 needed)
// Each cluster = bubble (Circle shape in recharts) positioned by polar-to-cartesian math:
//   x = cx + radius * cos(angle_i)
//   y = cy + radius * sin(angle_i)
//   radius = 120 for large clusters, 80 for small ones (2 rings)
// Bubble size = cluster.size (10–60px diameter)
// Color = cluster.color
// Hover tooltip: cluster.name + count + velocity badge (↑ 42% rising)
// Click: calls onClusterClick(cluster.name) → opens DrillDown
// Animation: CSS keyframe `float` on each bubble (translateY ±4px, 2-4s period, staggered)
// Header: "AI Issue Radar" + "Live — {N} active topics"
// CSS: bg-[#1a2744] border border-white/10 rounded-xl p-3 h-full
```

#### [A2] Frontend — `EmergingNarratives.tsx`

**File:** `frontend/src/components/EmergingNarratives.tsx`

```tsx
// Props: { brandId: string; days: number }
// Uses existing GET /dashboard/story-feed or top-topics endpoint
// Shows: "AI detected 3 new narratives" header
// Renders topic cloud: flex-wrap of styled topic pills
//   Rising topics: amber border + ↑ badge
//   New topics: blue border + NEW badge
//   Stable: gray text
// Each pill clickable → drill down to topic
// CSS: bg-[#1a2744] border border-white/10 rounded-xl px-4 py-3
```

#### [A3] Update Overview.tsx Screen 2 layout

- Replace bottom-left (ReputationRiskGauge) slot with `AIIssueRadar` (larger, takes full height of left column)
- Add `EmergingNarratives` in a small card below AIIssueRadar or replace the scroll hint area
- `ReputationRiskGauge` moves to Screen 3 (Situation Room — it fits there)

---

### SESSION 6 — Risk Copilot + Crisis Timeline + D+7 Forecast
**Score impact:** Screen 3 0.7→8 (+7.3) → **74.7/120**

#### [SEQ] Backend — `GET /dashboard/risk-forecast/{brand_id}` + `GET /dashboard/crisis-timeline/{brand_id}`

```python
class RiskForecast(BaseModel):
    current: float          # today's risk score (0-100)
    d1: float               # forecast D+1
    d3: float               # forecast D+3
    d7: float               # forecast D+7
    trend: str              # "escalating" | "stable" | "improving"
    escalation_pct: int     # 0-100 probability of escalation
    confidence: str         # "high" | "medium" | "low"

@router.get("/risk-forecast/{brand_id}", response_model=RiskForecast)
def get_risk_forecast(brand_id: str, days: int = Query(30), _user=Depends(...)):
    # Fetch 30-day daily KPI trend from InfluxDB (query_sentiment_trend)
    # Fit scipy.stats.linregress on the daily risk scores
    # Extrapolate D+1, D+3, D+7 from slope + intercept
    # Clamp to [0, 100]
    # escalation_pct = max(0, min(100, round(slope * 30 + current_risk)))
    # Cache 30 minutes

class CrisisEvent(BaseModel):
    date: str
    label: str              # "Story detected" | "Amplified" | "YouTube discussion"
    source_type: str        # "news" | "youtube" | "reddit"
    article_count: int
    sentiment: str          # "negative" | "neutral"
    is_amplification: bool  # True when count > prior day × 2

class CrisisTimelineResponse(BaseModel):
    events: list[CrisisEvent]
    period_days: int

@router.get("/crisis-timeline/{brand_id}", response_model=CrisisTimelineResponse)
def get_crisis_timeline(brand_id: str, days: int = Query(14), _user=Depends(...)):
    # Fetch articles grouped by day and source_type
    # Mark days where count > prior_day × 2 as amplification events
    # Return top 6 events sorted by date (most recent 14 days)
```

#### [A1] Frontend — `RiskCopilot.tsx`

**File:** `frontend/src/components/RiskCopilot.tsx`

```tsx
// Props: { brandId: string; days: number; onShowWhy?: () => void }
// Calls GET /dashboard/risk-forecast/{brandId}
// Layout:
//   Header: "Risk Copilot" + shield icon
//   Big text: "Medium risk." in text-2xl (color by escalation_pct)
//   Sub-line: "Probability of escalation: 62%"
//   Risk meter: thin progress bar (0-100%, colored red/amber/green)
//   Trend badge: "↑ Escalating" | "→ Stable" | "↓ Improving"
//   Button: "Show me why →" → calls onShowWhy() → opens AIExplainerDrawer with metric="risk_score"
// Forecast row: [Tomorrow: 54] [3 Days: 68] [7 Days: 81] — 3 numbered boxes
// CSS: bg-[#1a2744] border border-white/10 rounded-xl px-4 py-4
```

#### [A2] Frontend — `CrisisTimeline.tsx`

**File:** `frontend/src/components/CrisisTimeline.tsx`

```tsx
// Props: { brandId: string; days: number }
// Calls GET /dashboard/crisis-timeline/{brandId}
// Netflix/GitHub-style vertical timeline (left border line + event nodes)
//   Each event node: colored circle (red=negative, gray=neutral, amber=amplification)
//   Date label (e.g. "18 Jun") + event label ("Story detected") + count badge
//   Source type icon (📰/📺/💬)
//   Amplification events: amber border + "⚡ Amplified" badge
// CSS: relative border-l-2 border-white/10 pl-4 space-y-3
//      Each node: absolute left circle + event card to the right
```

#### [A3] Frontend — `SituationRoom.tsx` (new Screen 3 component)

**File:** `frontend/src/components/SituationRoom.tsx`

```tsx
// Props: { brandId: string; days: number; riskScore: number; kpi: KPISummary }
// Assembles the full Situation Room screen layout
// Layout (3-col grid):
//   Left: RiskCopilot (full height)
//   Center: CrisisTimeline (scrollable)
//   Right: ReputationRiskGauge (existing) + RiskForecast boxes below
// Self-contained — replace current Screen 3 content in Overview.tsx with <SituationRoom ... />
// RiskForecast boxes:
//   3 styled stat boxes: "Tomorrow / Risk 54" "3 Days / Risk 68" "7 Days / Risk 81"
//   Color: green <35, amber 35-65, red >65
```

**Update Overview.tsx:**
- Replace Screen 3 (Drill-Down Analysis) content with `<SituationRoom brandId={brandId} days={days} riskScore={riskScore} kpi={kpi} />`
- Keep the existing Drill-Down Analysis content as Screen 4 (re-number screens 4+)
- This adds one more snap screen to the container

---

## PHASE 3 — Investigation AI + Narrative Explorer + Board Mode
### Sessions 7–9 · Score: 60 → 82/120

**Phase 3 Goal:** Build the screens that transform data into deep intelligence — the Investigation Workspace gets AI reasoning, the Narrative Explorer gets a visual knowledge graph, and the Executive Board Mode makes the entire platform accessible to a CEO in 30 seconds.

---

### SESSION 7 — Investigation AI (Why This Happened + Entity Intel + Influence Tree)
**Score impact:** Screen 5 3→9 (+6.0) → **80.7/120**

#### [SEQ] Backend — `GET /dashboard/entity-intelligence/{brand_id}`

```python
class EntityItem(BaseModel):
    name: str
    entity_type: str    # "ceo" | "product" | "competitor" | "regulator" | "person" | "place"
    mention_count: int
    sentiment: str      # "positive" | "negative" | "neutral"
    articles: list[str] # top 3 article titles

class EntityIntelligenceResponse(BaseModel):
    entities: list[EntityItem]
    brand_id: str
    period_days: int

@router.get("/entity-intelligence/{brand_id}", response_model=EntityIntelligenceResponse)
def get_entity_intelligence(brand_id: str, days: int = Query(30), _user=Depends(...)):
    # Fetch articles, explode entities JSON array
    # Group by entity name, count mentions, compute dominant sentiment
    # Classify entity type by keyword matching (CEO/MD → ceo, competitor brand → competitor, etc.)
    # Sort by mention_count DESC, return top 20
```

#### [A1] Frontend — `EntityIntelligencePanel.tsx`

**File:** `frontend/src/components/DrillDown/EntityIntelligencePanel.tsx`

```tsx
// Props: { brandId: string; days: number; onEntityClick?: (entity: string) => void }
// Calls GET /dashboard/entity-intelligence/{brandId}
// Grouped sections: CEO | Products | Competitors | Regulators | Others
// Each entity row: entity name + mention count + sentiment dot + "→ drill" link
// Collapsed by default per section, expandable
// CSS: bg-[#1a2744] border border-white/10 rounded-xl px-4 py-3
// Section headers: text-[10px] uppercase tracking-wider text-white/40
```

#### [A2] Frontend — `InfluenceTree.tsx`

**File:** `frontend/src/components/DrillDown/InfluenceTree.tsx`

```tsx
// Props: { articles: ArticleItem[] }
// Builds a 3-level tree from articles:
//   Root = dominant source portal (highest reach)
//   Level 2 = other portals that published the same story (same keywords/title similarity)
//   Level 3 = audience/comments (youtube_comment source_type articles)
// Renders as recharts TreeMap (horizontal tree view)
//   OR simple CSS nested indented list (simpler, no D3 needed):
//     Root portal (large box, red/amber border)
//       ↳ Amplifying portals (medium boxes)
//           ↳ Consumer reactions (small boxes)
// CSS: bg-[#1a2744] border border-white/10 rounded-xl px-4 py-3
```

#### [A3] Update `DrillDownScreen.tsx` with all Investigation AI panels

**File:** `frontend/src/components/DrillDown/DrillDownScreen.tsx`

- Import and add `AIExplainerInline` (already exists — wire it as first content block, `autoLoad=true`)
- Import and add `EntityIntelligencePanel` below AIExplainerInline
- Import and add `InfluenceTree` in a collapsible section titled "Influence Tree"
- Layout: 3-panel view when article list is not selected:
  ```
  [AIExplainerInline "Why This Happened"  — full width]
  [EntityIntelligencePanel  col-4] [InfluenceTree col-8]
  [MentionsList (article list) — full width, scrollable]
  ```

---

### SESSION 8 — Narrative Explorer Screen (Knowledge Graph + Narrative DNA)
**Score impact:** Screen 4 0.4→7 (+6.6) → **87.3/120**

#### [SEQ] Backend — `GET /dashboard/narrative-graph/{brand_id}` + `GET /dashboard/narrative-dna/{brand_id}`

```python
class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str      # "brand" | "entity" | "issue" | "source" | "person"
    size: int           # 10–60 (node radius)
    sentiment: str      # "positive" | "negative" | "neutral"
    mention_count: int

class GraphEdge(BaseModel):
    source: str         # node id
    target: str         # node id
    weight: int         # co-occurrence count

class NarrativeGraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    brand_id: str

@router.get("/narrative-graph/{brand_id}", response_model=NarrativeGraphResponse)
def get_narrative_graph(brand_id: str, days: int = Query(30), _user=Depends(...)):
    # Fetch articles, extract entities and issue_categories
    # Create one node per unique entity/issue (top 15 by mention count)
    # Add brand as center node (size=60, type="brand")
    # Create edges: entity → brand (weight=mention_count)
    #               entity → entity if co-appear in same article (weight=co_count)
    # Return nodes + edges

class NarrativeDNAResponse(BaseModel):
    emotion: float      # 0-100 (fear/anger = high negative sentiment intensity)
    intent: float       # 0-100 (criticism = high neg editorial tone %)
    controversy: float  # 0-100 (divergent sentiment % × 100)
    urgency: float      # 0-100 (virality flag count / total articles × 100)
    reach: float        # 0-100 (total_reach / max_possible_reach, normalized)

@router.get("/narrative-dna/{brand_id}", response_model=NarrativeDNAResponse)
def get_narrative_dna(brand_id: str, days: int = Query(30), _user=Depends(...)):
    # Compute each dimension from existing article/KPI data
    # No Gemini call needed — pure computation
```

#### [A1] Frontend — `EntityKnowledgeGraph.tsx`

**File:** `frontend/src/components/NarrativeExplorer/EntityKnowledgeGraph.tsx`

```tsx
// recharts ScatterChart in radial layout — brand at center, entities orbiting
// Position computation (pure math, no D3 needed):
//   Brand node: center (cx, cy)
//   Entity/Issue nodes: polar coords at radius 120 (tier 1) or 200 (tier 2)
//   Angle = (index / tier_count) * 2π
// Render: recharts <Scatter> + custom <circle> shapes via <Cell>
// Edge lines: recharts <ReferenceLine> or SVG <line> connecting nodes
// Node colors: red=negative, green=positive, amber=neutral; size=node.size
// Hover: recharts <Tooltip> showing label + mention_count + sentiment
// Click: triggers onNodeClick(node) → drill into entity articles
// CSS wrapper: bg-[#1a2744] border border-white/10 rounded-xl p-4 h-[400px]
```

#### [A2] Frontend — `NarrativeDNAChart.tsx` + `NarrativeExplorer.tsx`

**File:** `frontend/src/components/NarrativeExplorer/NarrativeDNAChart.tsx`
```tsx
// recharts RadarChart with 5 axes: Emotion / Intent / Controversy / Urgency / Reach
// Props: { data: NarrativeDNAResponse }
// Dark theme: fill="rgba(59,130,246,0.2)" stroke="#3b82f6"
// Labels in text-[10px] text-white/60
// Size: 200×200 (compact widget)
```

**File:** `frontend/src/components/NarrativeExplorer/NarrativeExplorer.tsx`
```tsx
// Parent screen component — assembles Narrative Explorer
// Layout: [EntityKnowledgeGraph — left 60%] [NarrativeDNAChart + metadata — right 40%]
// Right panel: Narrative DNA chart + 5 dimension labels + scores
// Bottom: "Click a node to see evidence" hint text
// onNodeClick → calls onDrillDown(entity, { entity: node.label })
```

#### [A3] Add Narrative Explorer as new snap screen in Overview.tsx

- Add `NarrativeExplorer` import + render as a new `<div className="h-full snap-start ...">` between Screen 2 and Screen 3
- This makes the sequence: S1 Executive Copilot → S2 Intelligence Feed → S3 Narrative Explorer → S4 Situation Room → S5 Drill-Down → S6 Review Sites → S7 Drill-Down Explorer
- Update scroll hint text between screens accordingly

---

### SESSION 9 — Executive Board Mode
**Score impact:** Screen 9 0→9 (+9.0) → **96.3/120**

#### [SEQ] Backend — `GET /dashboard/board-briefing/{brand_id}`

```python
class BoardBriefingResponse(BaseModel):
    top_5_things: list[str]         # ["Brand reputation increased 4 pts", ...]
    top_3_risks: list[str]          # ["Tamil Nadu negative coverage rising", ...]
    top_5_opportunities: list[str]  # ["South India sentiment improving", ...]
    competitor_movements: str        # "Competitor A gained 8% SoV this week"
    pending_actions_count: int       # count from generated_content where status='pending'
    ai_recommendation: str           # "Schedule media engagement within 48 hours"
    confidence_pct: int
    generated_at: str

@router.get("/board-briefing/{brand_id}", response_model=BoardBriefingResponse)
def get_board_briefing(brand_id: str, days: int = Query(7), _user=Depends(...)):
    # Fetch articles + KPI + competitor SoV + risk forecast
    # Single structured Gemini prompt:
    #   "You are a senior PR analyst briefing a CEO board.
    #    Given this brand data: [context]
    #    Respond in JSON ONLY with exactly these keys:
    #    top_5_things, top_3_risks, top_5_opportunities, competitor_movements,
    #    ai_recommendation"
    # Cache 2 hours (board briefing is slow to change)
```

#### [A1] Frontend — `BoardMode.tsx`

**File:** `frontend/src/components/BoardMode/BoardMode.tsx`

```tsx
// Props: { brandId: string; days: number }
// Calls GET /dashboard/board-briefing/{brandId}
// NO charts — text only (per reference vision)
// Layout (dark, clean, executive):
//
//   "EXECUTIVE BOARD BRIEFING" header + brand name + date
//
//   [Top 5 Things You Need To Know]           [Top 3 Risks]
//   1. Brand reputation increased 4 pts        ① Tamil Nadu coverage rising
//   2. South India sentiment improving          ② YouTube risk score elevated
//   3. Google reviews trend positive            ③ Competitor SoV gained 8%
//   4. One regulatory mention detected
//   5. No crisis signals this week
//
//   [Top 5 Opportunities]
//   1. Positive YouTube creator detected — engage now
//   ...
//
//   [Competitor Movements]
//   "Competitor A gained 8% Share of Voice this week..."
//
//   [AI Recommendation]               [Confidence: 91%]
//   "Schedule media engagement         ████████████░░░
//    within 48 hours."                  91%
//
//   [N Actions Awaiting Approval]
//
// CSS:
//   Container: bg-[#0d1626] p-8 h-full overflow-y-auto
//   Section headers: text-[11px] font-semibold text-white/40 uppercase tracking-widest mb-2
//   List items: text-sm text-white/85 py-1 border-b border-white/5
//   Risk items: text-sm text-red-300
//   Opportunity items: text-sm text-emerald-300
//   Recommendation box: bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 text-sm text-white
//   Confidence bar: h-2 bg-blue-400 rounded-full (width: {pct}%)
//   Pending count badge: text-amber-400 font-semibold
```

#### [A2] Frontend — Add Board Mode as final snap screen + sidebar navigation link

**Update `Overview.tsx`:**
- Add `BoardMode` import
- Add new snap screen div at the end of the scroll container:
  `<div className="h-full snap-start overflow-hidden shrink-0 bg-[#0d1626]"><BoardMode brandId={brandId} days={days} /></div>`

**Update `Sidebar.tsx`:**
- Add `{ id: "board", tab: "overview", label: "Board Mode" }` nav item pointing to a scroll anchor
- Clicking "Board Mode" scrolls the snap container to the last screen

#### [A3] Polish — loading skeletons + error boundaries for all Phase 3 components

- Add `<ErrorBoundary>` wrapper around NarrativeExplorer and BoardMode
- Add skeleton loaders for all new components (same pulse pattern as existing)
- Verify TypeScript (`tsc --noEmit`) passes before commit

---

## PHASE 4 — Response Studio + Advocacy Hub + Universal Widgets
### Sessions 10–12 · Score: 82 → 100/120

**Phase 4 Goal:** Close the remaining 18 points by building the action-oriented surfaces (content generation, advocacy intelligence) and completing the universal widget layer (universal Co-Pilot Drawer, auto-surfaced Insight Chips).

---

### SESSION 10 — Response Studio (Content Generator + Approval Workflow + Scenario Sim)
**Score impact:** Screen 6 0→9 (+9.0) → **105.3/120** *(buffer for rounding)*

#### [SEQ] Backend — `POST /dashboard/generate-content` + content CRUD

```python
class GenerateContentRequest(BaseModel):
    brand_id: str
    content_type: str   # "press_release" | "faq" | "tweet" | "linkedin" | "ceo_statement"
    context: dict = {}  # { "topic": "...", "tone": "formal", "article_id": "..." }

class GeneratedContentItem(BaseModel):
    id: str
    content_type: str
    content_text: str
    status: str
    created_at: str

@router.post("/generate-content", response_model=GeneratedContentItem)
def generate_content(req: GenerateContentRequest, _user=Depends(...)):
    # Build type-specific Gemini prompt:
    #   tweet: "140 chars, brand-positive, responding to [topic]"
    #   press_release: "Formal 3-paragraph release addressing [topic]"
    #   faq: "5 Q&A pairs addressing [topic]"
    #   linkedin: "Professional 150-word post about [topic]"
    #   ceo_statement: "Executive tone, 2 paragraphs, addresses concern directly"
    # Write to generated_content table (status="draft")
    # Return content item

@router.get("/generated-content/{brand_id}", response_model=list[GeneratedContentItem])
def list_generated_content(brand_id: str, _user=Depends(...)):
    # Return all content items ordered by created_at DESC

@router.patch("/generated-content/{content_id}")
def update_content_status(content_id: str, req: ContentStatusUpdate, _user=Depends(...)):
    # req: { status: "pending" | "approved" | "rejected" }
    # Update generated_content table
```

#### [A1] Frontend — `ContentGenerator.tsx`

**File:** `frontend/src/components/ResponseStudio/ContentGenerator.tsx`

```tsx
// Props: { brandId: string; contextArticle?: ArticleItem }
// Type selector: 5 buttons (Press Release / FAQ / Tweet / LinkedIn / CEO Statement)
// Context input: textarea "What should this address?" (maps to context.topic)
// Generate button → POST /dashboard/generate-content → loading spinner
// Output: text area (editable after generation) with copy-to-clipboard button
// "Save for Approval" button → POST to set status="pending"
// CSS: bg-[#1a2744] border border-white/10 rounded-xl p-4 space-y-3
//      Type buttons: flex-wrap gap-2, active=bg-blue-600 text-white
```

#### [A2] Frontend — `ApprovalWorkflow.tsx` + `ScenarioSimulator.tsx`

**File:** `frontend/src/components/ResponseStudio/ApprovalWorkflow.tsx`
```tsx
// Calls GET /dashboard/generated-content/{brandId}
// Lists pending/draft/approved content items
// Each item: content_type badge + truncated preview + [Approve] [Reject] buttons
// Status column: colored badge (draft=gray, pending=amber, approved=green, rejected=red)
// Approve → PATCH /generated-content/{id} status="approved"
```

**File:** `frontend/src/components/ResponseStudio/ScenarioSimulator.tsx`
```tsx
// Static UI (data-driven stubs for now)
// Two columns:
//   "If we respond now": risk arrow DOWN by estimated % (from risk_forecast slope)
//   "If we stay silent": risk arrow UP by estimated % (risk_forecast d7 value)
// Visual: two large cards with colored risk numbers and directional arrows
// "Simulate Response" button opens ContentGenerator
```

#### [A3] Frontend — `ResponseStudio.tsx` + add as snap screen

**File:** `frontend/src/components/ResponseStudio/ResponseStudio.tsx`
```tsx
// Assembles: ContentGenerator (left 60%) + ApprovalWorkflow (right 40%)
//            ScenarioSimulator (bottom, collapsible)
```

**Update `Overview.tsx`:**
- Add ResponseStudio as new snap screen (after NarrativeExplorer)
- Update all scroll-hint arrows to reflect new screen count

---

### SESSION 11 — Advocacy Hub (AI Scores + Suggested Engagements + Relationship Memory)
**Score impact:** Screen 7 0.6→7 (+6.4) → **111.7/120**

#### [SEQ] Backend — Extend top-advocates + `GET /dashboard/suggested-engagements/{brand_id}`

**Update `GET /dashboard/top-advocates/{brand_id}` response:**
Add computed fields to `BrandAdvocate` schema:
```python
class BrandAdvocate(BaseModel):
    name: str
    source_type: str
    article_count: int
    total_reach: float
    # NEW computed fields:
    affinity_score: int     # round(positive_pct * sentiment_consistency * 100) → 0-100
    influence_score: int    # round(log(total_reach+1) / log(max_reach+1) * 100)
    trust_score: int        # round(avg_source_credibility * 100)
    dominant_sentiment: str # most common sentiment_label
```

```python
class SuggestedEngagement(BaseModel):
    advocate_name: str
    engagement_type: str    # "podcast" | "review_request" | "event_invite" | "sample_send"
    reason: str             # "3rd consecutive positive video about brand"
    affinity_score: int

@router.get("/suggested-engagements/{brand_id}", response_model=list[SuggestedEngagement])
def get_suggested_engagements(brand_id: str, days: int = Query(30), _user=Depends(...)):
    # Fetch top advocates with scores
    # For advocates with affinity_score > 60: suggest "podcast" or "review_request"
    # For advocates with trust_score > 70: suggest "event_invite"
    # Call Gemini for the reason text
    # Return top 5 suggestions
```

#### [A1] Frontend — `AdvocateCard.tsx` (upgrade from table to card)

**File:** `frontend/src/components/AdvocacyHub/AdvocateCard.tsx`
```tsx
// Props: { advocate: BrandAdvocate (with scores); onEngage?: () => void }
// Layout: profile avatar placeholder + name + source badge + 3 score meters
//   Affinity ████░░░ 72%  (blue bar)
//   Influence ██████ 88%  (purple bar)
//   Trust ████░░░░ 65%    (green bar)
// "Engage →" button → calls API to log action (stub POST for now)
// CSS: bg-[#1a2744] border border-white/10 rounded-xl p-3
```

#### [A2] Frontend — `RelationshipMemory.tsx` + `SuggestedEngagements.tsx`

**File:** `frontend/src/components/AdvocacyHub/RelationshipMemory.tsx`
```tsx
// Calls GET /dashboard/advocate-actions/{brandId} (stub endpoint — returns empty [])
// If empty: shows "No past interactions recorded yet" with "Log Interaction" button
// If populated: timeline of past actions (sample sent / campaign / event)
// This is a lightweight CRM-like log
```

**File:** `frontend/src/components/AdvocacyHub/SuggestedEngagements.tsx`
```tsx
// Calls GET /dashboard/suggested-engagements/{brandId}
// Lists suggestions as action cards:
//   [📻 Podcast Invite] [Advocate Name] [reason text] [Schedule →]
//   [⭐ Review Request] [Advocate Name] [reason text] [Send →]
// Action buttons are stubs (show "Scheduled!" confirmation)
```

#### [A3] Frontend — `AdvocacyHub.tsx` + add as snap screen

**File:** `frontend/src/components/AdvocacyHub/AdvocacyHub.tsx`
```tsx
// Header: "Advocacy Hub — AI found {count} creators"
// Layout:
//   Top: flex-wrap grid of AdvocateCards (3 per row)
//   Bottom-left: RelationshipMemory
//   Bottom-right: SuggestedEngagements
```

**Update `Overview.tsx`:**
- Replace existing `TopBrandAdvocates` in Screen 2 with a small inline version
- Add `AdvocacyHub` as new full snap screen

---

### SESSION 12 — Universal Co-Pilot Drawer + Auto Insight Chips + Final Polish
**Score impact:** Co-Pilot Drawer 1.8→8 (+6.2), Insight Chips 2.4→7 (+4.6) → **~100/120**

#### [A1] Upgrade `AIExplainerDrawer.tsx` → Universal Co-Pilot

**File:** `frontend/src/components/DrillDown/explainer/AIExplainerDrawer.tsx` (modify existing)

Additions:
- When opened without a `metric` prop (metric=null): show freeform chat input
- The chat input connects to `POST /dashboard/chat` (same as AskBar)
- Add a persistent trigger button: `frontend/src/components/CopilotTrigger.tsx`
  ```tsx
  // Fixed-position bottom-right button (above AskBar): 🤖 Co-Pilot
  // CSS: fixed bottom-20 right-4 z-30 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center
  // Click: opens AIExplainerDrawer with metric=null (universal mode)
  ```
- Add action buttons row in universal mode: [Generate Report] [Translate] [Email Summary]
  - "Generate Report" → calls `POST /dashboard/generate-content` with content_type="ceo_statement"
  - "Translate" / "Email Summary" → show "Coming soon" toast
- Wire `CopilotTrigger` into `Overview.tsx` (renders above AskBar on all screens)

#### [A2] Auto-surfaced Insight Chips on all surfaces

Wire `AIExplainerChip` to additional surfaces (each with appropriate metric + context):

1. **`StoryFeedCard.tsx`** — add chip row below action buttons:
   `<AIExplainerChip metric="investigation_context" brandId={brandId} context={{ headline: story.title }} />`

2. **`IndiaStateMap.tsx`** — in the state hover tooltip/popup:
   `<AIExplainerChip metric="state_sentiment" brandId={brandId} context={{ state: stateName }} />`

3. **`RiskCopilot.tsx`** — auto-load chip:
   `<AIExplainerChip metric="risk_score" brandId={brandId} value={escalation_pct} autoLoad={false} />`
   *(placed next to "Show me why" button)*

4. **`EntityIntelligencePanel.tsx`** — chip per entity group:
   `<AIExplainerChip metric="investigation_context" brandId={brandId} context={{ entity: entityName }} />`

5. **`AIIssueRadar.tsx`** — chip in cluster hover tooltip:
   `<AIExplainerChip metric="investigation_context" brandId={brandId} context={{ issue: cluster.name }} />`

#### [A3] Final polish, TypeScript verification, deploy check

- Run `tsc --noEmit` on full frontend — fix any remaining type errors
- Add `<React.Suspense fallback={<Skeleton />}>` around heavy new screens (NarrativeExplorer, BoardMode)
- Add keyboard shortcut: `Esc` closes AskBar, CopilotTrigger, and any open Drawer
- Verify all new backend endpoints return correct shapes with a local test or Railway health check
- Git commit all Phase 4 work → push → verify Railway + Vercel deploy

---

## Database Migration Summary

| Migration | Table | Purpose | Session |
|-----------|-------|---------|---------|
| `030_story_actions.sql` | `story_actions` | Watch/Investigate/Ignore per article | Session 4 |
| `030_story_actions.sql` | `generated_content` | Response Studio drafts + approval | Session 4 |
| `031_advocate_actions.sql` | `advocate_actions` | Engagement log for CRM | Session 11 |

---

## New Backend Endpoints Summary

| Endpoint | Method | Session | Score Impact |
|----------|--------|---------|-------------|
| `POST /dashboard/chat` | POST (SSE stream) | S1 | Ask Bar 0→9 |
| `GET /dashboard/morning-brief/{brand_id}` | GET | S2 | Screen 1 +2pts |
| `GET /dashboard/regional-summary/{brand_id}` | GET | S3 | Screen 8 +4pts |
| `GET /dashboard/story-feed/{brand_id}` | GET | S4 | Screen 2 +3pts |
| `POST /dashboard/story-action` | POST | S4 | Screen 2 +1pt |
| `GET /dashboard/issue-radar/{brand_id}` | GET | S5 | Screen 2 +3pts |
| `GET /dashboard/risk-forecast/{brand_id}` | GET | S6 | Screen 3 +4pts |
| `GET /dashboard/crisis-timeline/{brand_id}` | GET | S6 | Screen 3 +3pts |
| `GET /dashboard/entity-intelligence/{brand_id}` | GET | S7 | Screen 5 +3pts |
| `GET /dashboard/narrative-graph/{brand_id}` | GET | S8 | Screen 4 +4pts |
| `GET /dashboard/narrative-dna/{brand_id}` | GET | S8 | Screen 4 +2pts |
| `GET /dashboard/board-briefing/{brand_id}` | GET | S9 | Screen 9 +9pts |
| `POST /dashboard/generate-content` | POST | S10 | Screen 6 +5pts |
| `GET /dashboard/generated-content/{brand_id}` | GET | S10 | Screen 6 +2pts |
| `PATCH /dashboard/generated-content/{id}` | PATCH | S10 | Screen 6 +2pts |
| `GET /dashboard/suggested-engagements/{brand_id}` | GET | S11 | Screen 7 +3pts |

---

## New Frontend Components Summary

| Component | File | Session |
|-----------|------|---------|
| `AskBar` | `components/AskBar.tsx` | S1 |
| `ChatThread` | `components/ChatThread.tsx` | S1 |
| `MorningBrief` | `components/MorningBrief.tsx` | S2 |
| `WhatChangedCards` | `components/WhatChangedCards.tsx` | S2 |
| `AIConfidenceMeter` | `components/AIConfidenceMeter.tsx` | S2 |
| `AIRegionalSummary` | `components/AIRegionalSummary.tsx` | S3 |
| `StoryFeedCard` | `components/StoryFeedCard.tsx` | S4 |
| `StoriesFeed` | `components/StoriesFeed.tsx` | S4 |
| `AIIssueRadar` | `components/AIIssueRadar.tsx` | S5 |
| `EmergingNarratives` | `components/EmergingNarratives.tsx` | S5 |
| `RiskCopilot` | `components/RiskCopilot.tsx` | S6 |
| `CrisisTimeline` | `components/CrisisTimeline.tsx` | S6 |
| `SituationRoom` | `components/SituationRoom.tsx` | S6 |
| `EntityIntelligencePanel` | `components/DrillDown/EntityIntelligencePanel.tsx` | S7 |
| `InfluenceTree` | `components/DrillDown/InfluenceTree.tsx` | S7 |
| `EntityKnowledgeGraph` | `components/NarrativeExplorer/EntityKnowledgeGraph.tsx` | S8 |
| `NarrativeDNAChart` | `components/NarrativeExplorer/NarrativeDNAChart.tsx` | S8 |
| `NarrativeExplorer` | `components/NarrativeExplorer/NarrativeExplorer.tsx` | S8 |
| `BoardMode` | `components/BoardMode/BoardMode.tsx` | S9 |
| `ContentGenerator` | `components/ResponseStudio/ContentGenerator.tsx` | S10 |
| `ApprovalWorkflow` | `components/ResponseStudio/ApprovalWorkflow.tsx` | S10 |
| `ScenarioSimulator` | `components/ResponseStudio/ScenarioSimulator.tsx` | S10 |
| `ResponseStudio` | `components/ResponseStudio/ResponseStudio.tsx` | S10 |
| `AdvocateCard` | `components/AdvocacyHub/AdvocateCard.tsx` | S11 |
| `SuggestedEngagements` | `components/AdvocacyHub/SuggestedEngagements.tsx` | S11 |
| `RelationshipMemory` | `components/AdvocacyHub/RelationshipMemory.tsx` | S11 |
| `AdvocacyHub` | `components/AdvocacyHub/AdvocacyHub.tsx` | S11 |
| `CopilotTrigger` | `components/CopilotTrigger.tsx` | S12 |

---

## Score Progression Chart

```
Session  Score   Delta   What ships
──────────────────────────────────────────────────────────────────
Start    17.2    —       Current baseline (post AI Explainer)
S1       26.2    +9.0    AI Ask Bar streaming chat (all screens)
S2       30.5    +4.3    Morning Brief + What Changed + Confidence Meter
S3       40.5    +10.0   Screen 8 AI Regional Summary + Wire Inline to DrillDown
S4       43.9    +3.4    Stories That Matter feed + story_actions migration
S5       47.4    +3.5    AI Issue Radar (animated topic clusters)
S6       54.7    +7.3    Situation Room: Risk Copilot + Crisis Timeline + Forecast
S7       60.7    +6.0    Investigation AI: Why block + Entity Intel + Influence Tree
S8       67.3    +6.6    Narrative Explorer: Knowledge Graph + Narrative DNA
S9       76.3    +9.0    Executive Board Mode screen (complete)
S10      85.3    +9.0    Response Studio: Content Gen + Approval + Scenario Sim
S11      91.7    +6.4    Advocacy Hub: AI scores + Engagements + Memory
S12      100.0   +8.3    Universal Co-Pilot + Auto Insight Chips + Polish
```

---

## Dependency Graph

```
[S1: AI Ask Bar]
    └─► [S3: Wire to AskBar polish] (minor)

[S4: story_actions migration] ─────► [S10: generated_content migration]
    └─► [S4: StoriesFeed]               └─► [S10: ContentGenerator]
         └─► [S5: AIIssueRadar]              └─► [S11: AdvocacyHub]

[S6: RiskForecast endpoint]
    └─► [S6: RiskCopilot]
         └─► [S6: SituationRoom]
              └─► [S9: BoardMode uses forecast data]

[S7: EntityIntelligencePanel]
    └─► [S8: EntityKnowledgeGraph] (shares entity data model)

[AIExplainerChip — existing] ─► [S12: wire to 5 new surfaces]
[AIExplainerDrawer — existing] ─► [S12: upgrade to universal Co-Pilot]
[AIExplainerInline — existing] ─► [S3: wire to DrillDownScreen] [S7: auto-load in DrillDown]
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Gemini quota exhaustion on high-traffic board-briefing calls | Medium | Low | 2-hour cache; fallback to data-driven text generation |
| recharts knowledge graph performance with 20+ nodes | Low | Medium | Cap at 15 nodes; lazy-load edges; use `React.memo` on nodes |
| story_actions migration breaking existing article queries | Low | High | Migration adds new table only; no existing columns altered |
| SSE streaming blocked by Railway proxy/timeout | Medium | High | Use 30-second token-by-token chunks; add `Transfer-Encoding: chunked` header |
| TypeScript errors from new component props across 27 new files | High | Low | Run `tsc --noEmit` before each session commit; fix immediately |
| Vercel build failure on new imports | Medium | Medium | Check `VITE_API_URL` env var is set; verify all imports resolve |

---

## Verbatim "Next Prompt" for Each Session

Copy-paste these at the start of each session to carry full context forward.

### Session 1 Prompt
```
BrandPulse 2.0 — Session 1 of Phase 1.
Goal: Build AI Ask Bar (streaming SSE chat). Score: 17.2 → 26.2/120.

[SEQ] Backend first: POST /dashboard/chat in backend/app/dashboard/router.py
  - New schemas ChatRequest + ChatMessage in dashboard/schemas.py
  - StreamingResponse with text/event-stream
  - System prompt injects brand context (articles last 7d, KPI summary)
  - Gemini: generate_content → split response into word-by-word SSE tokens
  - SSE format: data: {"token": "word ", "done": false}\n\n
  - Final: data: {"token": "", "done": true}\n\n
  - Auth: require_brand_role(*READ_ROLES)
  - Commit + push → verify Railway

[PARALLEL after SEQ commit]:
  [A1] Create frontend/src/components/AskBar.tsx
       - Fixed-bottom bar, all screens, brandId+days props
       - Two modes: collapsed (input row ~48px) + expanded (chat thread above)
       - Reads stream with ReadableStream/getReader pattern
       - Example chips: "Why did sentiment drop?" | "What's the top risk?"
       - Esc collapses
  [A2] Create frontend/src/components/ChatThread.tsx
       - User/AI message bubbles, streaming cursor, auto-scroll
  [A3] Wire AskBar into Overview.tsx
       - Import + render as fixed-position overlay
       - Verify TypeScript: tsc --noEmit

Push all → verify Vercel deploys → acceptance: streaming chat answers brand-specific questions.
```

### Session 2 Prompt
```
BrandPulse 2.0 — Session 2 of Phase 1.
Goal: Morning Brief + What Changed + Confidence Meter. Score: 26.2 → 30.5/120.

[SEQ] Backend: GET /dashboard/morning-brief/{brand_id} in router.py
  - Schema MorningBriefResponse: greeting, score_change, score_direction, highlights[], confidence_pct
  - Fetch current + prior KPI; compute score_change; build 3-4 highlights
  - Single Gemini call for the greeting sentence; 60-min cache
  - Commit + push → verify Railway

[PARALLEL]:
  [A1] frontend/src/components/MorningBrief.tsx
       - Large card; greeting + bullets; score badge; speaker+expand stubs
  [A2] frontend/src/components/WhatChangedCards.tsx
       - Horizontal swipeable cards from existing AI summary data
       frontend/src/components/AIConfidenceMeter.tsx
       - SVG arc meter, 180-degree, colored zones
  [A3] Update Overview.tsx Screen 1 layout:
       - Row order: MorningBrief full-width → [AIConfidenceMeter + WhatChangedCards] → [AIExecutiveSummary | SentimentTrend] → [MentionsBySource | TopHeadlines]

Push → verify Vercel → tsc --noEmit clean.
```

### Session 3 Prompt
```
BrandPulse 2.0 — Session 3 of Phase 1.
Goal: Screen 8 AI Regional Summary + wire AIExplainerInline to DrillDown. Score: 30.5 → 40.5/120.

[SEQ] Backend: GET /dashboard/regional-summary/{brand_id} in router.py
  - Schema: RegionalSummaryResponse { summary, state_highlights[], confidence_pct }
  - Group articles by states_mentioned, compute improving/declining per region
  - Gemini for the summary text; 60-min cache
  - Commit + push → verify Railway

[PARALLEL]:
  [A1] frontend/src/components/AIRegionalSummary.tsx
       - Text block + state highlight pills (🟢/🔴 per state direction)
       - "Explain →" per state calls onStateExplain(state)
  [A2] Update IndiaStateMap.tsx:
       - Add onExplain?: (state: string) => void prop
       - State click popup gets "🧠 Explain" button
       Update Overview.tsx Screen 2 map section:
       - Wrap IndiaStateMap + AIRegionalSummary below it
  [A3] Wire AIExplainerInline into DrillDownScreen.tsx:
       - Import from ../explainer/AIExplainerInline
       - Add as first content block between breadcrumb and article list
       - metric="investigation_context", autoLoad=false

Push → verify Vercel → tsc --noEmit clean.
```

*(Sessions 4–12 prompts follow the same pattern — see Phase 2–4 session descriptions above for exact technical spec to paste into each prompt.)*

---

## Sidebar Navigation → Screen Mapping (as of 2026-06-24)

**File:** `frontend/src/components/Sidebar.tsx` — `NAV_ITEMS` array
**Custom scroll events** dispatched in `App.tsx` `onNavAction` → handled in `Overview.tsx` `useEffect`.

| Sidebar Nav Item | `id` | Behavior | Event / Tab |
|---|---|---|---|
| Executive Overview | `overview` | Sets `tab = "overview"`, scrolls to top (Screen 1) | `tab="overview"` |
| Board Intelligence | `board` | Sets `tab = "board"` — opens `BoardMode.tsx` full-page | `tab="board"` |
| Geo Intelligence | `geo-intel` | Sets `tab = "overview"`, scrolls to **Screen 8** (Geo Intelligence) | `brandpulse:scroll-geo` → `screen8Ref` |
| Mentions Monitor | `mentions-monitor` | Sets `tab = "mentions-monitor"` — opens `MentionsMonitor.tsx` | `tab="mentions-monitor"` |
| Reports | `topics` | Sets `tab = "topics"` — opens `TopicsView.tsx` | `tab="topics"` |
| News & RSS | `sources-rss` | Sets `tab = "sources"` — opens `SourceBreakdown.tsx` | `tab="sources"` |
| Blogs & Portals | `blogs` | Sets `tab = "sources"` — opens `SourceBreakdown.tsx` | `tab="sources"` |
| YouTube Analytics | `youtube` | Sets `tab = "overview"` *(stub — soon badge)* | `tab="overview"` |
| Review Sites | `review-sites` | Sets `tab = "overview"`, scrolls to **Screen 4** (ReviewSitesDashboard) | `brandpulse:scroll-review-sites` → `screen4Ref` |
| Response Studio | `response-studio` | Sets `tab = "overview"`, scrolls to **Screen 6** (ContentGenerator) | `brandpulse:scroll-response-studio` → `screen6Ref` |
| Narrative Explorer | `narrative-explorer` | Sets `tab = "overview"`, scrolls to **Screen 7** (EntityGraph + NarrativeDNA) | `brandpulse:scroll-narrative` → `screen7Ref` |
| Social & Forums | `social` | Sets `tab = "sources"` *(stub — soon badge)* | `tab="sources"` |
| Competitor Intel | `competitors` | Sets `tab = "overview"` *(stub — soon badge)* | `tab="overview"` |
| Influencers | `influencers` | Sets `tab = "overview"` *(stub — soon badge)* | `tab="overview"` |
| Settings | `brand-config` | Sets `tab = "brand-config"` — opens `BrandConfig.tsx` (adminOnly) | `tab="brand-config"` |
| Review Queue | `review-queue` | Sets `tab = "review-queue"` — opens `ReviewQueue.tsx` (adminOnly) | `tab="review-queue"` |
| User Management | `users` | Sets `tab = "users"` — opens `UserManagement.tsx` (adminOnly) | `tab="users"` |

### Overview Screen Map

| Ref | Snap Screen | `Ref` variable | Sidebar trigger |
|---|---|---|---|
| Screen 1 | Executive Overview (KPIs + AI Summary) | *(top / scrollTo 0)* | `overview` |
| Screen 2 | Media Intelligence (Issues, Sources, Stories, Risk Gauge, State Map) | — | *(scroll down)* |
| Screen 3 | Drill-Down Analysis (News/Reviews + Competitor + Situation Room) | — | *(scroll down)* |
| Screen 4 | Review Sites Intelligence (`ReviewSitesDashboard`) | `screen4Ref` | `review-sites` |
| Screen 5 | Drill-Down Explorer (`DrillDownScreen`) | `screen5Ref` | *(widget click)* |
| Screen 6 | Response Studio (`ContentGenerator` + `TopBrandAdvocates`) | `screen6Ref` | `response-studio` |
| Screen 7 | Narrative Explorer (`EntityGraph` + `NarrativeDNA`) | `screen7Ref` | `narrative-explorer` |
| Screen 8 | Geo Intelligence (Full `IndiaStateMap` + `GeoStateRankings` + `AIRegionalSummary`) | `screen8Ref` | `geo-intel` |

---

*Plan authored 2026-06-23. Implementation tracks commit `7a65071`. Target: 100/120 by end of Session 12.*
