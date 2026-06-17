# Competitor Deliverables Deep-Dive & Gap Analysis

*Rewritten 2026-06-16 — previous version of this file was corrupted (truncated terminal output). This version is grounded in fresh web research (competitor sites/reviews, June 2026) and direct verification against the current MediaSense codebase — not PRD aspirations.*

*Updated 2026-06-16 (later same day) — Phase 1 shipped: tenant isolation, mention filters (date/portal/topic/text), Source Breakdown page, Topics View page, last-processed timestamp. Sections 2–4 revised to match current code, not the original gap list.*

---

## 1. Competitor deep-dive: what they actually deliver

| Competitor | Core deliverable | Vernacular reality (2026) | Pricing | Where they actually win |
|---|---|---|---|---|
| **Locobuzz** (Mumbai) | Unified CX platform: social listening + omnichannel digital care (chat/email/calls) + review monitoring + ticketing/CRM routing + crisis alerts | Now markets sentiment across Hindi, Tamil, Marathi, Bengali, Telugu, etc. (incl. Hinglish/Tanglish) via "ContextualPulse™," plus vague "region-level insight" — but scope is social posts/reviews/forums; no evidence of curated Tamil **news-portal** RSS coverage or credibility weighting | ₹20K–80K/mo | CX/ticketing for large consumer brands; established Indian enterprise support |
| **Konnect Insights** (Pune) | Omnichannel suite: social listening + ORM + social CRM + analytics + publishing + BI dashboards + crisis management | Markets Hindi/regional sentiment as a selling point against "English-only undercounts regional sentiment" — same pain point MediaSense targets — but no published Tamil NLP benchmark, engine appears rule/ML-hybrid | $29/user/mo+ | Engagement workflow tooling, cheap per-seat entry |
| **Meltwater** (SF) | Global media + social monitoring, 100+ languages, customizable dashboards, GenAI Lens (brand mentions across LLMs) | "100+ languages" = generic multilingual NLP, not Indian-vernacular-tuned; no Tamil-specific claims found | ₹5–15L/yr | Largest global news index, enterprise reporting, LLM-mention tracking (new in 2025) |
| **Brandwatch / Cision** (UK) | Consumer intelligence: conversation tracking, crisis monitoring, share-of-voice, "Iris AI" chat assistant + AI dashboards | 44+ supported languages; vernacular Indian languages not named; 2026 roadmap focuses on APAC data + video/image analysis, not Indian regional depth | $800–3,000+/mo | Social data depth, AI-assisted querying ("Ask Iris"), enterprise/PR integration via Cision |
| **Hootsuite Listening (formerly Talkwalker)** (acquired by Hootsuite) | Boolean-query brand/competitor tracking, AI-powered emotion/topic classification, image-in-content brand recognition, now bundled into Hootsuite plans | 187 languages claimed historically; vernacular Indian sentiment depth unconfirmed; 2026 updates focus on TikTok/platform coverage, not language depth | Bundled in Hootsuite plans; standalone Talkwalker was $9,600+/yr | Visual/image brand recognition — a real deliverable MediaSense doesn't have at all |
| **Mention** | Web/social mention tracking, sentiment analysis, competitive benchmarking, influencer ID | Multi-language monitoring claimed but only basic 3-class sentiment; no Indian-vernacular sentiment claims found; retired Publish & Respond (Jan 2026) after Agorapulse acquisition — now listening/analytics only | $41–599+/mo | Cheapest entry price, simplest UX, fast crisis alerting |

> **Correction to MediaSense's original pitch:** The PRD's competitor section (and the prior version of this doc) assumed *zero* competitor vernacular coverage. That's no longer true — Locobuzz and Konnect Insights both now market Indian-vernacular sentiment. The "only Tamil sentiment tool in the market" claim is not defensible as-is.

**★ Insight ─────────────────────────────────────**
Every competitor's vernacular claim is scoped to *social/review/forum text*, not curated, credibility-weighted long-form news article text. That's a structural difference, not just a feature gap — they're built for short-form social text (slang, emoji, code-mixing); MediaSense is built for long-form news prose with per-source credibility weighting (e.g., a tuned `news_tamil` model vs. generic social-text models). That's the part of the claim that's still real and defensible — just narrower than "we're the only one with Tamil sentiment."
**─────────────────────────────────────────────────**

---

## 2. What MediaSense actually ships today (verified against code, not PRD copy)

| PRD claim | Verified reality |
|---|---|
| Credibility-weighted perception score | ✅ Shipped — `backend/app/pipeline/perception.py`: `score = credibility × (0.6 + 0.4 × log10(reach+1)/log10(10001))`, blended into a 0–100 scale |
| Tamil + English AI sentiment | ✅ Shipped — Gemini `gemini-2.0-flash` primary, Groq `llama-3.1-8b-instant` fallback (PRD text says "Gemma 2 9B" — **PRD is wrong**, that model isn't in the code) |
| Hourly ingestion pipeline | ✅ Shipped — APScheduler + Redis queue + 4-way thread pool, runs immediately on startup |
| Entities / topics / keywords per article | ✅ Shipped, returned per-article in `OverviewResponse`/`ArticleItem` |
| Sentiment trend (7/30-day) | ✅ Shipped via InfluxDB (`query_sentiment_trend`) |
| Mention Explorer filters (sentiment, language, date, portal, topic, text search) | ✅ **Shipped** — `dashboard/router.py::get_mentions` + `MentionsList.tsx` now implement all 5: sentiment, language, date range, portal, topic, and free-text search |
| Dedicated Source Breakdown page | ✅ Shipped — `SourceBreakdown.tsx` + `GET /dashboard/sources/{brand_id}`, sortable, all sources (not capped at 5) |
| Dedicated Topics View | ✅ Shipped — `TopicsView.tsx` + `GET /dashboard/topics/{brand_id}`, sortable, all topics with sentiment breakdown (not capped at 10) |
| Row-level tenant isolation | ✅ **Fixed** — `tenants/router.py::GET /brands` now filters by the caller's `user_roles` (agency-level and brand-level grants), no longer returns every brand to every user |
| Last-processed timestamp in UI | ✅ Shipped — `Overview.tsx` shows "Last updated Xm/h/d ago", derived from the most recent `collected_at` |
| Role-based access (agency_admin / analyst / brand_admin / brand_viewer) | ⚠️ **Partial** — `require_role()` exists and gates the brand-config write endpoint (`PUT /brands/{id}/config` requires `agency_admin`/`brand_admin`), but read endpoints (overview/mentions/sources/topics) only check brand *access*, not role — a `brand_viewer` currently has the same read capability as an `agency_admin` |
| State/region-level filtering | ❌ Not built — `brand_configs.states` field exists in the schema (added alongside RBAC work) but isn't populated, surfaced, or filterable anywhere yet |
| Dead-letter queue + retry (max 3 attempts) | ❌ Not built — no retry/DLQ logic found in `backend/app/pipeline` |
| Annotation support on trend chart | ❌ Not built |

---

## 3. Tools × Deliverables comparison matrix

✅ full capability · ⚠️ partial / social-only · ❌ absent

| Deliverable | MediaSense | Locobuzz | Konnect Insights | Meltwater | Brandwatch/Cision | Hootsuite (Talkwalker) | Mention |
|---|---|---|---|---|---|---|---|
| Curated Tamil **news-portal** monitoring (RSS) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Tamil/vernacular AI sentiment | ✅ | ⚠️ social-only | ⚠️ social-only | ❌ | ❌ | ❌ | ❌ |
| English news-portal monitoring | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| Source-credibility-weighted scoring | ✅ | ❌ | ❌ | ⚠️ | ✅ | ❌ | ❌ |
| Social media monitoring | ❌ (Phase 2) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Visual/image brand recognition | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ❌ |
| State/region-level sentiment filtering | ❌ | ⚠️ (marketing claim, unverified) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Role-based multi-tenant access (RBAC) | ⚠️ partial (write-gated, reads not role-checked) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Mention search/filter depth (date, portal, topic, text) | ✅ 5 of 5 filters | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dedicated topic-trend analytics view | ✅ (sortable, no time-series yet) | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Agency / multi-brand workspace | ✅ (tenant-isolated, partial roles) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| India mid-market pricing (₹1–3L/yr) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |

---

## 4. Bottom line

1. **The "only Tamil sentiment tool" claim needs updating.** Locobuzz and Konnect Insights both now market vernacular sentiment. What's still differentiated — narrower but real — is curated, credibility-weighted **news-portal** monitoring (not social/review text) at mid-market pricing. Use this framing in the pitch, not the old absolute claim.
2. **Most of the "internal, not competitive" gaps are now closed.** Tenant isolation on `/brands` is fixed, all 5 promised Mention Explorer filters are shipped, and Source Breakdown / Topics View / last-processed timestamp all exist. What's left internally is narrower: finishing RBAC enforcement on read endpoints (currently only writes are role-gated) and state/region filtering (schema field exists, nothing built on top of it yet).
3. **Nobody — including MediaSense — has cracked reliable state/region-level sentiment.** Locobuzz's "region-level insight" language is marketing copy without a verifiable feature behind it. That row is genuinely open ground if MediaSense builds it first, and it's now the most differentiated thing left to build (more so than finishing RBAC, which is hygiene, not a sales point).
4. **Social media monitoring is the one deliverable everyone else has and MediaSense doesn't.** It's explicitly Phase 2 — the single largest row of ❌ on the matrix and the most consequential gap in a sales conversation, but the highest-effort item too (new ingestion source + short-form/code-mixed NLP profile).

## 5. Prioritized build order (next up)

1. **State/region-level sentiment filtering** — open competitive ground, schema half-built already (`brand_configs.states`)
2. **Finish RBAC enforcement** — apply `require_role()` to read endpoints, not just the config-write endpoint; cheap, closes an internal liability
3. **Dead-letter queue + retry** — silent data loss risk in the pipeline today; not a sales feature but a reliability one
4. **Social media monitoring (Phase 2)** — biggest competitive gap, biggest lift; do after the cheaper internal fixes above
5. **Annotations on trend chart** — low effort, no urgency, good filler between bigger items
6. **Visual/image brand recognition** — real moat for Hootsuite/Talkwalker only; big computer-vision lift for a niche win, lowest priority
