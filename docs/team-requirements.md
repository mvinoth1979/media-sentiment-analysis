# MediaSense — Team Requirements & Cost Analysis

> **Last updated:** 2026-06-17
> **Scope:** MVP to production-grade SaaS (news monitoring, 6 Indian languages, 12 brands, RBAC)
> **Update this document** whenever a major feature (social media, alerts, export, billing, etc.) is added.
> **See also:** `docs/competitive-analysis-and-pricing.md` for feature comparison and pricing tiers.

---

## Current Feature Baseline (as of last update)

- Multi-brand: 12 brands (CIPET, Reliance, Bank of Baroda, Canara Bank + 8 others)
- Multi-language ingestion & NLP: EN, TA, HI, GU, BN, KN
- Portals: 29 (7 EN, 10 TA, 5 HI, 2 BN, 3 KN, 2 GU)
- RBAC: 5 roles across 3 tiers (platform / agency / brand)
- Dashboard: KPIs, sentiment trend, source breakdown, topics, state filtering, mention explorer
- Pipeline: Google News RSS + static portals, hourly batch, DLQ, circuit breaker, rejection learning, bootstrap priority
- Infrastructure: Vercel (frontend) + Railway (backend) + Supabase (DB/auth) + Upstash Redis + Cloudflare R2

---

## Critical Gaps (honest assessment)

### Security — High Severity
- `POST /pipeline/trigger` has no auth guard — anyone with the Railway URL can exhaust NLP quota
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
- No export (CSV / PDF reports for client decks)
- No alert system (sentiment threshold notifications)
- No full-text search across mentions
- No billing / subscription management (cannot charge customers)
- No self-serve brand or user onboarding (every new brand requires SQL migrations)

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

**What they didn't buy:** Security audit, performance engineering, social media coverage, formal QA suite, billing, self-serve onboarding, SLA guarantees, HA architecture.

---

## Incremental Cost to Close Key Gaps

| Gap | Additional resource | Estimated cost (INR) | Notes |
|---|---|---|---|
| Security fixes (auth on trigger, rate limiting, audit log) | 0.5 Backend Engineer × 1 month | ₹1,25,000 | Can be done now without new hires |
| Performance fixes (SQL aggregation, connection pooling) | 0.5 Backend Engineer × 1 month | ₹1,25,000 | Can be done now |
| Export (CSV + PDF reports) | 1 Frontend + 0.5 Backend × 1.5 months | ₹4,50,000 | Wave 3 priority |
| Alerts system | 0.5 Backend × 1 month | ₹1,25,000 | Wave 3 priority |
| Full-text search | 0.5 Backend × 0.5 months | ₹62,500 | Wave 3 priority |
| CI/CD + staging env | 1 DevOps × 1 month | ₹2,50,000 | Should be done before scaling |
| Test suite (unit + integration) | 1 QA Engineer × 2 months | ₹2,40,000 | Technical debt |
| Social media (Phase 2) | +1 Data Engineer + API costs | ₹15,00,000+ | Requires platform API agreements |
| Billing / self-serve onboarding | 1 Full-stack + 1 PM × 2 months | ₹9,00,000 | Needed before commercialisation |
| HA architecture (multi-instance Railway/K8s) | 1 DevOps × 1 month + infra | ₹5,00,000+ | Needed before enterprise SLA |

**Realistic 2-person team to competitive MVP:** 4 months, ~₹28–35L — closes all gaps except social media.

---

## Update Log

| Date | Update | Features added |
|---|---|---|
| 2026-06-17 | Initial document | News monitoring, 6 languages, 29 portals, 12 brands, RBAC, state filtering, pipeline visibility, DLQ, circuit breaker, rejection learning, bootstrap priority |
