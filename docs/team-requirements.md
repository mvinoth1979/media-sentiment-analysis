# MediaSense — Team Requirements & Cost Analysis

> **Last updated:** 2026-06-20 (Phase 1 data quality: wire dedup, headline/body sentiment, editorial tone, regulatory flag; C1+C2 alerts)
> **Scope:** MVP to production-grade SaaS (news monitoring, 6 Indian languages, 12 brands, RBAC)
> **Update this document** whenever a major feature (social media, alerts, export, billing, etc.) is added.
> **See also:** `docs/competitive-analysis-and-pricing.md` for feature comparison and pricing tiers.

---

## Current Feature Baseline (as of last update)

- Multi-brand: 12 brands (CIPET, Reliance, Bank of Baroda, Canara Bank + 8 others)
- Multi-language ingestion & NLP: EN, TA, HI, GU, BN, KN
- Portals: 43 (12 EN, 11 TA, 8 HI, 3 BN, 6 KN, 3 GU) — all URLs verified working
- RBAC: 5 roles across 3 tiers (platform / agency / brand)
- Dashboard: **Phase 3 redesign live** — compact single-screen layout (no scroll, `h-screen overflow-hidden`); dark navy sidebar (BrandPulse brand, nav, brand selector, last-updated timestamp); light main area with card grid; 5 KPI cards (Total Mentions, Positive, Neutral, Negative, Reputation Index); Sentiment Trend area chart (indigo/amber/red fills, gradient opacity, F08 annotation system); Mentions by Source donut; Top Headlines 3-tab panel (Top Positive / Top Negative / Trending); Review Sites Summary (star rating + distribution bars + themes); Top Issues Table (topic + mention bar + net sentiment %); Sentiment by Source Table (stacked bar + perception score per source); Competitor Share of Voice donut; Alerts & Risks cards; click-to-detail panel for all 9 sections (breadcrumb `← Executive Overview | [Section]`, back navigation); sidebar static; State Map and All Mentions accessible from header
- Mention Explorer: light theme, 10/page, numbered pagination (← 1 2 →), `1–10 of 10+` counter; language filter dropdown (6 languages)
- NLP data quality (Phase 1): wire-service syndication dedup (story_hash + syndication_count — PTI/ANI cross-portal copies collapsed before NLP); separate headline/body sentiment scores (headline_sentiment_score, body_sentiment_score, sentiment_divergence flag); editorial tone classification (factual/positive_frame/negative_frame/critical); author/journalist extraction from RSS fields; regulatory source auto-flag (14 .gov.in domains + SEBI/RBI/Enforcement Directorate/Supreme Court keyword list)
- Alerts: email notifications (5 types: perception_score_below, negative_pct_above, mention_spike, syndication_spike, journalist_beat) — per-brand, 4h rate-limit; syndication_spike fires when a story spreads to ≥N portals in 24h; journalist_beat fires when same author publishes ≥N negative articles in 30d
- Self-serve: brand wizard (name/keywords/languages), user invite (magic-link via Supabase), UserManagement page, delete brand (master_admin, cascade), remove user role (agency_admin+)
- Pipeline: Google News RSS + static portals, hourly batch, DLQ, circuit breaker, rejection learning, bootstrap priority; `/pipeline/trigger` auth-gated (master_admin only)
- Infrastructure: Vercel (frontend) + Railway (backend) + Supabase (DB/auth) + Upstash Redis + Cloudflare R2

---

## Critical Gaps (honest assessment)

### Security — High Severity
- ~~`POST /pipeline/trigger` has no auth guard~~ **✅ Fixed — now requires master_admin JWT**
- No API rate limiting on dashboard endpoints
- JWT token refresh not handled in frontend (silent 401s after expiry)
- No audit log (required for enterprise contracts)

### Architecture / Reliability — High Severity
- Single Railway instance — one crash = full outage for all brands
- Circuit breaker state is process-local (resets on every redeploy)
- `get_kpi_summary()` loads all articles into Python to count — should be SQL aggregation; breaks at ~50K articles
- `get_overview()` fires 3 separate 500-row full-table scans per page load
- No staging environment — every deploy goes directly to production
- No CI/CD pipeline

### Coverage — Critical for Market Fit
- **News-only** — Twitter/X, Instagram, Facebook, Reddit, YouTube = 0 coverage
  - 60–70% of damaging brand mentions originate on social media
  - Largest single competitive gap vs Locobuzz / Konnect
- **Hourly batch** — PR crises escalate in minutes; no near-real-time ingestion
- No historical data backfill

### Product Completeness — Medium Severity
- ~~No export (CSV / PDF reports for client decks)~~ **✅ CSV export shipped (Wave 3)**
- ~~No alert system (sentiment threshold notifications)~~ **✅ Email alerts shipped (Wave 3) — 3 types, 4h rate-limit**
- No full-text search across mentions
- No billing / subscription management (cannot charge customers)
- ~~No self-serve brand or user onboarding~~ **✅ Brand wizard + user invite shipped (Wave 3)**
- ~~No delete brand / remove user~~ **✅ Delete brand (master_admin, cascade all articles) + remove user role (agency_admin+) shipped**
- No branded PDF report generation

### NLP Scalability — Medium-Long Term
- Gemini + Groq free tiers cap at ~1,500 calls/day combined
- At 12 brands × 20 articles × 6 languages = up to 1,440 calls/run — already at ceiling
- Adding 10+ more brands breaks quota without moving to paid NLP tiers

---

## Build Team — PRD to Deployment

### Phase Timeline

| Phase | Weeks | Activities |
|---|---|---|
| P0 — PRD & Discovery | 1–6 | User research, competitor analysis, information architecture, PRD, acceptance criteria |
| P1 — Architecture & Design | 4–9 (overlap) | System design, DB schema, API contracts, Figma wireframes + design system |
| P2 — Core Development | 8–18 | Auth, RBAC, ingestion pipeline, NLP router, basic dashboard |
| P3 — Feature Development | 16–24 | Multi-language, state filtering, drill-downs, export, alerts |
| P4 — QA & Security | 20–26 (overlap) | Test automation, penetration test, performance test |
| P5 — Staging & UAT | 24–26 | Staging environment, UAT sign-off, runbooks |
| P6 — Launch | 27–28 | Go-live, monitoring, on-call setup |

**Total calendar time: 28 weeks (~7 months) to production MVP**

---

### Full Team Roster with Cost

All figures use Indian senior-market rates (mid–senior band). USD column at ₹83 = $1.

| # | Role | Count | Duration | Rate (₹/mo) | Person-months | Total (₹) | Total (USD) |
|---|---|---|---|---|---|---|---|
| 1 | Product Manager | 1 | 7 mo | 2,50,000 | 7 | 17,50,000 | $21,100 |
| 2 | UX Researcher | 1 (contract) | 2 mo | 1,50,000 | 2 | 3,00,000 | $3,600 |
| 3 | UX / UI Designer | 1 | 6 mo | 1,80,000 | 6 | 10,80,000 | $13,000 |
| 4 | Business Analyst | 1 | 4 mo | 1,80,000 | 4 | 7,20,000 | $8,700 |
| 5 | Sr. Backend Engineer | 2 | 6 mo | 2,50,000 each | 12 | 30,00,000 | $36,100 |
| 6 | Sr. Frontend Engineer | 2 | 6 mo | 2,00,000 each | 12 | 24,00,000 | $28,900 |
| 7 | NLP / ML Engineer | 1 | 6 mo | 3,50,000 | 6 | 21,00,000 | $25,300 |
| 8 | Data Engineer | 1 | 5 mo | 2,50,000 | 5 | 12,50,000 | $15,100 |
| 9 | DevOps / SRE | 1 | 7 mo | 2,50,000 | 7 | 17,50,000 | $21,100 |
| 10 | Database Admin | 1 (contract) | 3 mo | 2,00,000 | 3 | 6,00,000 | $7,200 |
| 11 | QA Engineer | 2 | 3 mo | 1,20,000 each | 6 | 7,20,000 | $8,700 |
| 12 | Test Automation Engineer | 1 | 3 mo | 1,50,000 | 3 | 4,50,000 | $5,400 |
| 13 | Security Engineer | 1 (contract) | 2 mo | 3,00,000 | 2 | 6,00,000 | $7,200 |
| 14 | Technical Writer | 1 (contract) | 2 mo | 1,00,000 | 2 | 2,00,000 | $2,400 |
| 15 | Project Manager | 1 | 7 mo | 2,00,000 | 7 | 14,00,000 | $16,900 |
| | **People subtotal** | **~17 people** | | | | **₹1,83,20,000** | **$220,700** |

### Infrastructure & Tooling (7 months)

| Item | Monthly (₹) | 7-month total (₹) | USD |
|---|---|---|---|
| Cloud hosting (AWS/GCP, HA setup) | 1,50,000 | 10,50,000 | $12,700 |
| NLP APIs (Gemini/OpenAI paid tiers) | 80,000 | 5,60,000 | $6,700 |
| Managed DB + Redis | 40,000 | 2,80,000 | $3,400 |
| CI/CD + monitoring (GitHub Actions, Datadog) | 35,000 | 2,45,000 | $2,950 |
| Dev tools (Jira, Figma, Postman, Sentry) | 30,000 | 2,10,000 | $2,530 |
| Security scanning (Snyk, pen test vendor) | 20,000 | 1,40,000 | $1,690 |
| **Infrastructure subtotal** | | **₹24,85,000** | **$29,950** |

---

## Total Cost Summary

| Category | INR | USD |
|---|---|---|
| People (17 roles, 7 months) | ₹1,83,20,000 | $220,700 |
| Infrastructure & tooling | ₹24,85,000 | $29,950 |
| **MVP total (7 months)** | **₹2,08,05,000** | **~$251,000** |
| Post-launch team for 12 more months (scaled to 8 people) | ₹1,60,00,000 | $192,800 |
| **Year-1 total** | **~₹3,68,00,000** | **~$443,000** |

---

## AI-Assisted Development Comparison

| Metric | Traditional team | AI-assisted (this project) |
|---|---|---|
| Calendar time | 28 weeks | ~4 weeks |
| People | 17 | 1 |
| Cost | ₹2.08 crore | ~₹4,000 (subscription + free tiers) |
| Cost ratio | 1× | ~520× cheaper |
| Time ratio | 1× | ~7× faster |

**What the savings bought:** Full backend pipeline, RBAC, multi-language NLP, 29-portal ingestion, React dashboard, DLQ, circuit breaker, rejection learning, state filtering.

**What they didn't buy:** Security audit, performance engineering, social media coverage, formal QA suite, billing, SLA guarantees, HA architecture, PDF reports.

---

## Incremental Cost to Close Key Gaps

| Gap | Additional resource | Estimated cost (INR) | Notes |
|---|---|---|---|
| Security fixes (auth on trigger, rate limiting, audit log) | 0.5 Backend Engineer × 1 month | ₹1,25,000 | Can be done now without new hires |
| Performance fixes (SQL aggregation, connection pooling) | 0.5 Backend Engineer × 1 month | ₹1,25,000 | Can be done now |
| ~~Export (CSV + PDF reports)~~ | ~~1 Frontend + 0.5 Backend × 1.5 months~~ | ~~₹4,50,000~~ | ✅ CSV shipped Wave 3; PDF pending Wave 4 |
| ~~Alerts system~~ | ~~0.5 Backend × 1 month~~ | ~~₹1,25,000~~ | ✅ Email alerts shipped Wave 3 |
| Full-text search | 0.5 Backend × 0.5 months | ₹62,500 | Wave 3 priority |
| CI/CD + staging env | 1 DevOps × 1 month | ₹2,50,000 | Should be done before scaling |
| Test suite (unit + integration) | 1 QA Engineer × 2 months | ₹2,40,000 | Technical debt |
| Social media (Phase 2) | +1 Data Engineer + API costs | ₹15,00,000+ | Requires platform API agreements |
| ~~Self-serve onboarding~~ | ~~0.5 Full-stack × 1 month~~ | ~~₹2,50,000~~ | ✅ Brand wizard + user invite + delete brand/user shipped Wave 3 |
| Billing / subscription management | 1 Full-stack + 1 PM × 2 months | ₹9,00,000 | Wave 4 — blocks first paying customer |
| HA architecture (multi-instance Railway/K8s) | 1 DevOps × 1 month + infra | ₹5,00,000+ | Needed before enterprise SLA |

**Realistic 2-person team to competitive MVP:** 4 months, ~₹28–35L — closes all gaps except social media.

---

## Update Log

| Date | Update | Features added |
|---|---|---|
| 2026-06-17 | Initial document | News monitoring, 6 languages, 29 portals, 12 brands, RBAC, state filtering, pipeline visibility, DLQ, circuit breaker, rejection learning, bootstrap priority |
| 2026-06-17 | Wave 3 shipped | CSV export, email alerts (3 types), self-serve brand wizard, user invite/management, India state choropleth map; gap table updated |
| 2026-06-17 | Wave 3 admin + map fix | Delete brand (master_admin, cascade), remove user role (agency_admin+) with inline confirm; state choropleth replaced with chip grid (dead TopoJSON URL removed, zero external dependency); language filter → 6-option dropdown; `/pipeline/trigger` auth fixed; Railway backend fully re-deployed with all Wave 3/4 routes |
| 2026-06-17 | Portal expansion | 29 → 43 portals: +5 EN (HT, Mint, Deccan Herald, Quint, News18), +3 HI (Bhaskar, Prabhat Khabar, Hari Bhoomi), +1 TA (Sathiyam TV), +1 BN (Sangbad Pratidin), +3 KN (Kannada Prabha, TV9 Kannada, Public TV), +1 GU (Chitralekha); all 14 URLs verified working RSS; 21 candidates excluded with documented reasons |
| 2026-06-18 | Phase 2.0 YouTube integration | YouTube video search, channel RSS, comments, YouTube-aware NLP, quota manager, reach metadata (views/likes/subs/duration), source_type filter, YouTube KPI card, per-brand YouTube config (wizard Step 4) |
| 2026-06-20 | Phase 3 — full dashboard redesign + compact single-screen layout | Dark navy sidebar (BrandPulse brand, nav, brand selector, last-updated); 5 KPI cards with delta badges; sentiment trend area chart (indigo/amber/red fills, F08 annotations); mentions donut, top headlines 3-tab, review sites summary, top issues, sentiment by source, competitor SoV, alerts & risks cards; compact single-screen layout (no scroll, `h-screen overflow-hidden`); click-to-detail panel for all 9 dashboard sections with `← Executive Overview` breadcrumb and back navigation; sidebar static; Mention Explorer light theme + 10/page numbered pagination |
| 2026-06-20 | NLP quality improvements (5 priorities) | P1: confidence gate — articles with confidence < 0.3 excluded from KPI counts; P2: YouTube low-signal comment filter (Nice/Good/pure-emoji patterns skipped before NLP, saves quota); P3: recency decay in perception score (1.0→0.15 multiplier over 7/30/90 day buckets); P4: engagement rate (likes+comments÷views) adds 0.7–1.0× multiplier to perception weight; P5: `/dashboard/review-summary/{brand_id}` endpoint — ReviewSitesSummary widget connected to real pipeline data (star rating derived from sentiment score, distribution from sentiment bucketing, themes from top topics) |
| 2026-06-20 | Phase 1 data quality + C1/C2 alerts (commits a8bb04c, 5e9845f) | Wire-service syndication dedup: story_hash (sha256 first 8 significant title tokens), syndication_count field, filter_syndicated() in orchestrator before NLP runs; separate headline/body sentiment: headline_sentiment_score, body_sentiment_score, sentiment_divergence (|diff|≥0.4) via structured HEADLINE:/BODY: Gemini prompt — zero extra API cost; editorial tone: factual/positive_frame/negative_frame/critical added to same call; author extraction: RSS author/dc:creator/author_detail.name priority chain; regulatory source flag: is_regulatory_source bool on articles, 16 .gov.in domains + 20+ title keyword phrases; migration 013 (new article columns + indexes) + migration 014 (extends alert_type CHECK constraint); C1 syndication_spike alert type + C2 journalist_beat alert type added to alerts.py + Overview.tsx; total alert types now 5 |
