# Product Requirements Document
## MediaSense — Phase 1.5: Differentiation & Architecture Hardening

**Version:** 1.0
**Date:** 2026-06-16
**Status:** Draft for Review
**Owner:** Product Team
**Related:** `docs/product/PRD.md` (Phase 1/2/3 roadmap), `docs/competitor comparision.md` (gap analysis vs. Locobuzz/Konnect/Meltwater/Brandwatch/Hootsuite/Mention), `references/Brand24_SaaS_Architecture_Reference_v1.md` & `v2.md` (competitor SaaS architecture teardown)
**Implementation status:** Not started — this document defines requirements only.

---

## Table of Contents

1. [Why Phase 1.5 Exists](#1-why-phase-15-exists)
2. [Inputs to This PRD](#2-inputs-to-this-prd)
3. [Current State (Verified Against Code, 2026-06-16)](#3-current-state-verified-against-code-2026-06-16)
4. [Goals & Non-Goals](#4-goals--non-goals)
5. [Feature Requirements](#5-feature-requirements)
6. [Explicitly Out of Scope](#6-explicitly-out-of-scope)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Suggested Sequencing](#8-suggested-sequencing)
9. [Success Metrics](#9-success-metrics)
10. [Risks & Mitigations](#10-risks--mitigations)

---

## 1. Why Phase 1.5 Exists

The original PRD (`docs/product/PRD.md`) defines a clean two-phase jump: Phase 1 (English + Tamil news portals) → Phase 2 (social media monitoring). In practice, two things have happened since Phase 1 shipped that justify an interim phase before Phase 2 begins:

1. **The competitive landscape moved.** `docs/competitor comparision.md` (rewritten 2026-06-16 from fresh research) found that Locobuzz and Konnect Insights now both market vernacular sentiment, weakening the original "only Tamil sentiment tool" claim. The remaining genuinely open ground — state/region-level sentiment — is unbuilt by anyone, MediaSense included. Closing that gap *before* Phase 2 (social) is now more valuable competitively than it was when the original roadmap was written, because it's a differentiator with no competitor pressure yet, whereas Phase 2 (social monitoring) is a category where MediaSense would simply be catching up to seven competitors who already have it.
2. **Phase 2 will be materially harder to bolt on if the current data model and pipeline-visibility gaps aren't addressed first.** The `articles` table and `ArticleItem` API contract are news-portal-shaped (`portal_id`, `url`, single `author` string, no per-mention engagement/influence metrics). Adding Twitter/Instagram/YouTube mentions later means either forcing social data into a news-shaped schema (technical debt) or a breaking schema migration mid-Phase-2. Phase 1.5 is the place to generalize this *before* the cost of getting it wrong multiplies.

Phase 1.5 is therefore scoped as: **finish the cheap, high-value gaps identified in the competitor analysis, and harden the architecture for Phase 2 — without starting Phase 2's actual ingestion work.**

---

## 2. Inputs to This PRD

This PRD is grounded in three sources, each used for a different purpose:

| Source | Used for |
|---|---|
| `docs/product/PRD.md` (original Phase 1/2/3 PRD) | Confirming what Phase 1.5 must *not* duplicate or contradict, and which Phase 2/3 commitments (state heatmap, multi-vernacular, social platforms) Phase 1.5 explicitly defers |
| `docs/competitor comparision.md` (competitor gap analysis, verified against code 2026-06-16) | The prioritized list of remaining internal gaps: state/region filtering, RBAC completion, DLQ (shipped `36ad90c`, prior to this PRD), social media (Phase 2, not 1.5) |
| `references/Brand24_SaaS_Architecture_Reference_v1.md` / `v2.md` (Brand24 product teardown) | A reference architecture for a *mature* social-listening SaaS, used to borrow specific, low-risk patterns (data model shape, filter-state management, progressive loading UX, AI quick-actions) — **not** to copy Brand24's feature set wholesale. MediaSense's differentiation is curated, credibility-weighted news-portal text, not social feed breadth; Brand24 patterns are adopted only where they generalize MediaSense's *own* architecture forward, not where they'd dilute the news-credibility positioning. |

Every feature below cites which of these three inputs motivated it.

---

## 3. Current State (Verified Against Code, 2026-06-16)

For traceability, this is what's actually shipped as of commit `36ad90c` (dead-letter queue), the most recent backend change:

| Capability | Status |
|---|---|
| Tenant isolation (`/brands` filtered by `user_roles`) | ✅ Shipped |
| Mention Explorer filters (sentiment, language, date, portal, topic, text) | ✅ Shipped — `dashboard/router.py::get_mentions`, no URL/state persistence |
| Source Breakdown / Topics View pages | ✅ Shipped, sortable, uncapped |
| Trend chart annotations | ✅ Shipped |
| Dead-letter queue + retry | ✅ Shipped (`app/pipeline/dead_letter.py`, max 5 retries) |
| RBAC — write endpoint | ✅ Shipped — `PUT /brands/{id}/config` requires `agency_admin`/`brand_admin` via `require_role()` |
| RBAC — read endpoints | ❌ **Not enforced** — `overview`, `mentions`, `sources`, `topics` only check `require_brand_access` (brand membership), not role. A `brand_viewer` has identical read capability to an `agency_admin`. |
| RBAC — role-to-brand binding | ⚠️ **Latent gap** — `require_role()` checks whether the user holds an allowed role *anywhere*, not whether they hold it *for this specific brand_id*. A `brand_admin` on Brand A and `require_brand_access`'d into Brand B (e.g. via an agency-level grant) currently passes the role check using their Brand-A role. Not yet exploitable in production data (roles are narrowly assigned today) but is a correctness gap, not just a missing feature. |
| State/region sentiment filtering | ❌ **Not built** — `brand_configs.states` column exists (added during RBAC work) but is never populated, surfaced, or queryable. No location signal is extracted from article text. |
| `Mention`/`Article` data model | ⚠️ News-portal-shaped — `articles` table has `portal_id`, `url`, `author TEXT`, no engagement/influence metrics, no `source_platform` discriminator. Will not extend cleanly to social sources without migration. |
| Mention Explorer UX | ⚠️ Dense table, no URL query-param sync (filters lost on refresh, not shareable/bookmarkable), full in-place refetch with no skeleton state |
| AI usage beyond per-article sentiment | ❌ None — Gemini/Groq are only called per-article during ingestion; no user-facing "summarize" or digest feature exists despite the original PRD's Persona 2 (agency owner) explicitly wanting auto-generated reports |
| Pipeline progress visibility | ❌ None — adding/reconfiguring a brand triggers a pipeline run with no user-visible progress; the user only sees results once the next scheduled `/overview` poll picks up new data |

---

## 4. Goals & Non-Goals

### Goals
1. Ship the **state/region-level sentiment filtering** capability — the most differentiated open gap identified in the competitor analysis.
2. **Close the RBAC gap completely** — both the missing read-endpoint role checks and the role-to-brand binding correctness issue.
3. **Generalize the Mention data model** to a platform-agnostic shape, so Phase 2 social ingestion is additive, not a migration.
4. Adopt a small number of **high-value, low-risk UX/architecture patterns from Brand24** that improve the existing news-portal product on its own merits (URL-synced filters, progressive loading, AI quick-actions) — not patterns that only make sense for a social-feed product (e.g. influence-score sliders tuned for follower counts, multi-platform source checkboxes).
5. Leave the system in a state where Phase 2 (social media monitoring) can start immediately after Phase 1.5, without backtracking.

### Non-Goals
- Phase 1.5 does **not** add any new ingestion source (no Twitter/Instagram/YouTube/Reddit — that is Phase 2, unchanged).
- Phase 1.5 does **not** add new languages beyond English/Tamil (Phase 3, unchanged).
- Phase 1.5 does **not** build the India sentiment heatmap *visualization* promised for Phase 2 — only the underlying state-tagging and filtering data layer it depends on (see §5.1).
- Phase 1.5 does **not** adopt Brand24's social-specific UI elements (influence sliders, multi-platform source checkboxes, follower-count badges) — these don't map to a single-platform, credibility-weighted news product and would misrepresent what MediaSense measures.

---

## 5. Feature Requirements

### 5.1 — State/Region-Level Sentiment Filtering
**Motivated by:** competitor comparison §5 priority #1 ("open competitive ground... most differentiated thing left to build"); original PRD §3.1 Pain Point 5 (no state-level granularity); original PRD §8.2 Phase 2 goal (state heatmap) — this feature builds the data layer that heatmap will eventually sit on top of.

**Requirements:**
- Extend the NLP extraction step (currently producing `entities`, `topics`, `keywords` per article) to also extract **Indian state/region mentions** from article text (e.g. "Chennai", "Tamil Nadu", "Coimbatore" → `Tamil Nadu`). This is an additive field on the existing structured NLP output, not a new pipeline stage.
- Store extracted states as `states_mentioned TEXT[]` on `articles` (mirrors the existing `topics`/`entities` array columns).
- Add a `state` query parameter to `GET /mentions/{brand_id}` and surface state breakdown in `GET /overview/{brand_id}` (analogous to the existing `top_sources`/`top_topics` aggregates).
- Add a state filter control to the Mention Explorer UI, populated from `brand_configs.states` (the brand's relevant states) when set, falling back to all states observed in the data when not set.
- `brand_configs.states` becomes a genuinely-used field for the first time — brand admins can scope which states are relevant to highlight (e.g. a Tamil Nadu FMCG brand cares about Tamil Nadu/Puducherry; a pan-India telecom cares about all states).
- **Explicitly deferred:** the map-based heatmap visualization itself stays in Phase 2 per the original PRD. Phase 1.5 ships the extraction, storage, and list/filter UX only — the data foundation a heatmap needs, not the heatmap.

**Open question for stakeholder input:** state extraction accuracy depends on whether article text reliably names a state/city (often it doesn't — a generic "Amul launches new product" article may have zero location signal). Should articles with no extractable state be labeled `"unspecified"` and shown as a distinct filter bucket, or excluded from state-filtered views entirely? This affects how "complete" the feature feels and should be confirmed before implementation.

---

### 5.2 — Complete RBAC Enforcement
**Motivated by:** competitor comparison §5 priority #2 ("cheap, closes an internal liability"); current-state gap in §3 above (read endpoints unchecked; role-to-brand binding gap).

**Requirements:**
- Apply role checks to the four read endpoints (`/overview`, `/mentions`, `/sources`, `/topics`) so that, at minimum, a `brand_viewer` role is sufficient (i.e., the floor role) and the dependency is explicit rather than absent — today these endpoints simply have no role dependency at all.
- Fix the role-to-brand binding gap: `require_role()` must be combined with `require_brand_access()` such that the *specific* role being checked is the one the user holds *for that brand_id* (directly or via the owning agency), not merely a role the user holds for any brand/agency. This likely means replacing the two independent `Depends()` checks on `PUT /brands/{id}/config` (and the new read-endpoint checks) with a single dependency that resolves the user's role scoped to the requested `brand_id`.
- Add test coverage proving a `brand_admin` on Brand A cannot use that role to satisfy a role check on Brand B, even if they separately have *any* access (e.g. agency-level) to Brand B.

---

### 5.3 — Platform-Agnostic Mention Data Model
**Motivated by:** Brand24 architecture reference v2 §2.B (the `Mention` JSON contract: `source_platform`, structured `author` object, structured `metrics` object) — adopted here specifically because Phase 2 (social monitoring) is on the roadmap and will need exactly this shape; current-state gap in §3 above.

**Requirements:**
- Add a `source_platform` field to the article/mention model, defaulting to `"news"` for all existing and new news-portal articles. This is the discriminator Phase 2 will use to distinguish `"news"` from `"twitter"`, `"instagram"`, etc., without needing a separate table per platform.
- Restructure the API response shape (`ArticleItem` in `dashboard/schemas.py`) so author and engagement data are represented in a way that degrades gracefully for sources that don't have them, rather than being news-specific fields. News articles today have a single flat `author` string and no engagement metrics; Brand24's contract models these as nested, optional objects (`author: {username, display_name, avatar_url, follower_count}`, `metrics: {influence_score, estimated_reach, engagement_count}`) precisely so a platform without follower counts (a news article) and a platform with them (a tweet) can share one schema. MediaSense should adopt this shape now, populating only the fields that apply to news (e.g. `metrics.estimated_reach` ← existing `reach_score`), so Phase 2 sources populate the same contract instead of requiring a new one.
- This is a **schema/contract generalization, not a rename of `articles`→`mentions`** — recommend keeping the `articles` table name (avoids a disruptive migration) but generalizing the *columns and API shape* it exposes. The PRD intentionally leaves the choice of "alter `articles` in place" vs. "introduce a new `mentions` view/table" as an implementation-time decision, not a product requirement.
- No behavior change for existing users — this is purely a forward-compatibility data-shape change, verified by the existing Mention Explorer continuing to render identically.

---

### 5.4 — Mention Explorer UX Upgrade
**Motivated by:** Brand24 architecture reference v2 §3 Frame 3 (URL synchronization, skeleton loading over full-screen-white refetch) and §5 (zero-state empty-filter handling); current-state gap in §3 above (filters are React-state-only, lost on refresh, not shareable).

**Requirements:**
- **URL query-param synchronization:** all active Mention Explorer filters (sentiment, language, portal, topic, state, date range, search text) should round-trip through the browser URL, so a filtered view is bookmarkable and shareable between teammates (e.g. an agency analyst sending a colleague a link to "negative Tamil mentions this week" instead of describing how to recreate the filter state).
- **Non-destructive refetch:** when filters change, the existing result set should remain visible with a subtle loading indicator overlaid, rather than the table clearing to a loading state — matching Brand24's explicit recommendation to never wipe the screen during a filtered refetch.
- **Zero-state empty-filter handling:** the existing "No mentions found" + "Clear filters" pattern already exists (`MentionsList.tsx`) and should be kept — Brand24's Edge Cases section (§5.4) independently validates this as a best practice already implemented here. No change needed beyond confirming state-filter and date-filter combinations also hit this path correctly.

---

### 5.5 — AI-Generated Mention Digest ("Summarize with AI")
**Motivated by:** Brand24 architecture reference v1 §2 State C ("Quick AI Actions: Summarize with AI") and v2 §1 (`QuickActions buttons={['Summarize AI', 'Generate Report']}`); original PRD Persona 2 ("Rajan", agency founder) explicit want: *"auto-generated weekly perception reports... something impressive to show in new business pitches."* This was a named goal in the original PRD that was never built.

**Requirements:**
- Add a digest/summary action, scoped per brand, that takes the current filtered mention set (or a fixed recent window, e.g. last 7 days) and produces a short natural-language executive summary — e.g. "Sentiment was net positive (62% positive, 18% negative) driven by coverage of the new product launch in Tamil Nadu press; one notable negative cluster around delivery delays in Chennai (Vikatan, Polimer News)."
- This reuses the **existing Gemini integration** already in the stack (`app/nlp/gemini_handler.py`) — no new AI provider or infrastructure is required, only a new prompt/endpoint that feeds it aggregated mention data instead of single-article text.
- Output should be exportable/copyable (plain text at minimum) so an agency user can paste it directly into a client report or pitch deck — directly serving the original PRD's "something impressive to show in new business pitches" goal.
- **Explicitly smaller than Brand24's version:** Brand24 pairs this with a full PDF "Generate Report" pipeline. Phase 1.5 ships only the text digest; a formatted/branded PDF export is a candidate for Phase 2+ if the digest proves valuable, not a Phase 1.5 commitment.

---

### 5.6 — Pipeline Progress Visibility
**Motivated by:** Brand24 architecture reference v1 §2 State A ("Loading mentions... it'll take a few moments") and v2 §3 Frame 2 (SSE/WebSocket progress events: `{"status": "scraping_twitter", "progress": 20}`); current-state gap in §3 above (no feedback when a brand is added/reconfigured).

**Requirements:**
- When a brand is newly onboarded or its keyword/portal/state config is changed, the very next pipeline run for that brand should be visible to the user as in-progress, not silent. At minimum this means surfacing a status (e.g. "collecting", "analyzing", "done", with article counts) rather than the dashboard simply showing stale/empty data until the next scheduled poll happens to land.
- Brand24's pattern uses SSE/WebSockets for live progress; MediaSense's existing architecture is poll-based (`react-query` with `staleTime`), so the **lighter-weight implementation** — a status field returned by the existing `/overview` endpoint (e.g. `pipeline_status: "running" | "idle"`, last-run article/error counts) that the frontend polls more frequently right after a config change — should be evaluated before committing to a new SSE/WebSocket transport. This PRD requires the *user-visible outcome* (no more silent waiting); the transport mechanism is an implementation decision, not a requirement.
- This becomes more valuable, not less, once Phase 2 lands — social-platform first-runs will be slower and noisier than news RSS, making "is anything happening right now" an even more important question to answer than it is today.

---

### 5.7 — Source Breakdown Polish (Optional / Nice-to-Have)
**Motivated by:** Brand24 architecture reference v1 §2 State C ("Sources Table" with favicon + domain + visits column).

**Requirements:**
- Add portal favicons/domain icons to the existing Source Breakdown table (`SourceBreakdown.tsx`) for visual scannability — a cosmetic parity item, not a functional gap.
- This is explicitly the lowest-priority item in this PRD; include it only if 5.1–5.6 are complete with capacity remaining.

---

## 6. Explicitly Out of Scope

To avoid scope creep disguised as "architecture hardening," the following are **not** part of Phase 1.5, regardless of how easy any individual piece might look in isolation:

- Any social media ingestion source (Twitter/X, Instagram, Facebook, LinkedIn, YouTube, Reddit) — remains Phase 2 per the original PRD.
- Any new language beyond English/Tamil — remains Phase 3.
- The India state-sentiment **heatmap visualization** — §5.1 ships the data layer it needs, not the map itself (Phase 2 per original PRD §8.2).
- Visual/image brand recognition — explicitly deferred in the competitor comparison's priority list (#6, lowest priority, "real moat for Hootsuite/Talkwalker only").
- Influence-score sliders, multi-platform source checkboxes, or any other Brand24 UI pattern that is specifically about *social* mentions rather than news mentions — adopting these now would misrepresent the product's current single-source-type (news) reality.
- A full PDF report-generation pipeline (only a text digest is in scope — see §5.5).

---

## 7. Non-Functional Requirements

| Requirement | Target | Notes |
|---|---|---|
| Zero regression on existing Mention Explorer filters | All 6 current filters (sentiment, language, portal, topic, date, text) continue to work after URL-sync and data-model changes | Verified by existing + new tests |
| RBAC fix introduces no false-positive lockouts | Existing `brand_viewer`/`brand_admin`/`agency_admin` users retain at least their current read access after the role-to-brand binding fix | Requires a migration/backfill check against current `user_roles` data before rollout |
| State extraction does not block the NLP pipeline's throughput | Adding state extraction to the existing Gemini/Groq structured-output call should not require an additional model call per article (extend the existing prompt/schema rather than adding a second call) | Directly relevant given the NLP daily-quota constraints already encountered in production |
| AI digest reuses existing provider quota responsibly | Digest generation should be an explicit user action (on-demand), not a background/scheduled job, to avoid competing with per-article NLP calls for the same daily Gemini/Groq quota | Learned from the recent quota-exhaustion incident (commit `2b20e01`) |
| Mention data-model change is backward compatible | Existing stored articles must populate correctly under the generalized schema (e.g. `source_platform = "news"` backfilled, not null) | No data loss on migration |

---

## 8. Suggested Sequencing

Ordered by a combination of risk-reduction, dependency, and the competitor comparison's own prioritization:

1. **§5.2 RBAC completion** — cheapest, fixes a real correctness gap, no dependencies on anything else here.
2. **§5.3 Platform-agnostic data model** — do this before §5.1 and §5.4 so state-extraction and UX work land on the final schema shape rather than needing rework when Phase 2 eventually forces the migration anyway.
3. **§5.1 State/region filtering** — the highest competitive-value item; builds on the now-generalized schema.
4. **§5.4 Mention Explorer UX upgrade** — naturally bundled with §5.1 since the state filter is a new addition to the same filter bar.
5. **§5.6 Pipeline progress visibility** — independent of the above, can be parallelized.
6. **§5.5 AI digest** — independent, lowest technical risk, good candidate to ship whenever capacity opens up.
7. **§5.7 Source breakdown polish** — only if time remains.

---

## 9. Success Metrics

| Metric | Target |
|---|---|
| State/region filter usage | Used in ≥30% of Mention Explorer sessions within 30 days of release (proxy for whether the differentiation feature is actually valuable, not just shipped) |
| RBAC correctness | Zero reported cross-brand role-leakage incidents; 100% of read endpoints have an explicit role dependency (verifiable by code, not just intent) |
| Mention data-model migration | Zero data-loss incidents; 100% of historical articles backfilled with `source_platform = "news"` |
| AI digest adoption | ≥1 digest generated per active agency-tier brand per week (validates the original PRD's "weekly report" persona need) |
| Pipeline progress visibility | Reduction in support questions of the form "why is my new brand showing no data" (qualitative, tracked manually until volume justifies a dashboard metric) |

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| State extraction has low recall (most articles don't name a specific state/city) | High | Medium | Resolve the open question in §5.1 (label as "unspecified" rather than silently dropping); set expectations that this is a coverage-building feature, not 100%-complete on day one |
| RBAC role-to-brand binding fix breaks existing legitimate access for some users | Medium | High | Run the fixed logic against a snapshot of current `user_roles` data in a dry run before enabling enforcement, comparing old vs. new access decisions for every existing user/brand pair |
| Mention data-model generalization is treated as "just a rename" and under-scoped at implementation time | Medium | Medium | This PRD explicitly frames it as a contract/shape change, not a table rename (§5.3) — implementation should be reviewed against the Brand24 reference contract shape, not against convenience |
| AI digest competes with per-article NLP for daily provider quota, recreating the quota-exhaustion incident from commit `2b20e01` | Medium | High | NFR in §7 mandates on-demand-only generation, not scheduled; consider a separate, smaller daily quota carve-out if usage grows |
| Brand24-inspired patterns get over-applied (e.g. someone adds an influence slider meant for social follower counts) | Low | Medium | §6 explicitly lists which Brand24 patterns are out of scope and why |

---

*Document ends. This is a requirements document only — no implementation has been started. For the original Phase 1/2/3 roadmap, see `docs/product/PRD.md`. For the gap analysis this PRD responds to, see `docs/competitor comparision.md`.*
