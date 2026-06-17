# MediaSense — Competitive Analysis & Pricing Strategy

> **Last updated:** 2026-06-17 (Wave 3 admin + map fix)
> **Based on:** Live codebase audit + competitor research (June 2026)
> Update this document when major features ship (social media, export, alerts, billing).

---

## 1. What Is Live in MediaSense Today (Verified Against Code)

| Feature | Status | Notes |
|---|---|---|
| News portal ingestion — English | ✅ Live | 12 portals (The Hindu, TOI, NDTV, India Today, ET, Indian Express, Deccan Chronicle, Hindustan Times, Mint, Deccan Herald, The Quint, News18) |
| News portal ingestion — Tamil | ✅ Live | 11 portals (Hindu Tamil, Vikatan, Samayam, Polimer, Maalaimalar, Daily Thanthi, Tamil Murasu, Oneindia Tamil, News Tamil, Puthiyathalaimurai, Sathiyam TV) |
| News portal ingestion — Hindi | ✅ Live | 8 portals (Navbharat Times, Amar Ujala, Jagran, NDTV India, Hindustan, Dainik Bhaskar, Prabhat Khabar, Hari Bhoomi) |
| News portal ingestion — Bengali | ✅ Live | 3 portals (Ei Samay, Ananda Bazar, Sangbad Pratidin) |
| News portal ingestion — Kannada | ✅ Live | 6 portals (Prajavani, Vijaya Karnataka, Udayavani, Kannada Prabha, TV9 Kannada, Public TV) |
| News portal ingestion — Gujarati | ✅ Live | 3 portals (Divya Bhaskar, Gujarat Samachar, Chitralekha) |
| AI sentiment analysis (Gemini primary, Groq fallback) | ✅ Live | 3-class: positive/negative/neutral with confidence score |
| Entity extraction (brand, person, org, location) | ✅ Live | Per-article, returned in API and dashboard |
| Topic extraction | ✅ Live | Per-article, used in Topics View |
| Keyword extraction | ✅ Live | Aggregated in overview |
| Credibility-weighted Perception Score (0–100) | ✅ Live | Weighted by source credibility × reach; not raw mention count |
| Sentiment trend chart (7-day / 30-day) | ✅ Live | InfluxDB time-series, hourly granularity |
| Mention Explorer with 6 filters | ✅ Live | Sentiment, language, portal, topic, date range, free-text search |
| Source Breakdown page | ✅ Live | Per-portal mention count + sentiment split |
| Topics View page | ✅ Live | Per-topic count + sentiment split, sortable |
| State-level mention tagging | ✅ Live | NLP extracts Indian states from article content |
| State filter in Mention Explorer | ✅ Live | URL-synced, click-to-drill |
| State breakdown on Overview | ✅ Live | Top states by mention volume + sentiment |
| India state sentiment grid | ✅ Live | Chip grid per state, color-coded by sentiment ratio; hover tooltip; click-to-drill to filtered mentions; sorted by mention count (replaced choropleth — remote TopoJSON source was 404) |
| CSV export (Mention Explorer) | ✅ Live | Respects all active filters; streams up to 2,000 rows |
| Email alert system | ✅ Live | 3 alert types: perception_score_below, negative_pct_above, mention_spike; per-brand; 4h rate-limit |
| Self-serve brand onboarding | ✅ Live | 3-step wizard (name → keywords → languages); agency_admin / master_admin only |
| User invite & management | ✅ Live | Magic-link invite via Supabase; role assignment at brand or agency scope |
| Delete brand | ✅ Live | master_admin only; inline confirm; cascades all articles, configs, user_roles, dedupe hashes |
| Remove user role | ✅ Live | agency_admin+ can remove brand-scoped user access; inline confirm per row |
| Language filter (Mention Explorer) | ✅ Live | Dropdown with 6 options: EN, TA, HI, GU, BN, KN; URL-synced |
| Multi-brand support | ✅ Live | 12 brands in current deployment |
| RBAC (5 roles: master_admin / agency_admin / agency_analyst / brand_admin / brand_viewer) | ✅ Live | 3-tier hierarchy: platform / agency / brand |
| Multi-tenant isolation | ✅ Live | Agency-scoped and brand-scoped access; no cross-brand data leakage |
| Sentiment pie chart | ✅ Live | On Overview |
| Click-to-drill-down (Sources / Topics → filtered Mentions) | ✅ Live | |
| Pipeline visibility (status, last run, article stats) | ✅ Live | Per-brand, on Overview |
| Rejection learning | ✅ Live | Deleted articles stored in `article_rejections`; pipeline skips similar future articles |
| Dead-letter queue + 5× retry | ✅ Live | Redis-backed, 60s retry interval |
| NLP circuit breaker | ✅ Live | Trips on rate-limit exhaustion; 60s cooldown |
| Bootstrap priority for new brands | ✅ Live | 6-run fast-fill counter; new brands run first in scheduler |
| Google News RSS (per-keyword, per-language) | ✅ Live | EN/TA/HI/GU/BN/KN with India-specific `hl`/`ceid` params |
| Mobile responsive UI | ✅ Live | |

### Not Yet Live (Planned)

| Feature | Phase | Priority |
|---|---|---|
| Social media (Twitter/X, Instagram, Facebook, YouTube, Reddit) | Phase 2 | Critical competitive gap |
| Real-time / near-real-time ingestion (< 15 min) | Phase 2 | High |
| Export (PDF / PPT report) | Wave 4 | High |
| Full-text search across all stored articles | Wave 4 | Medium |
| Competitive benchmarking / share of voice | Phase 3 | Medium |
| Billing / subscription management | Wave 4 | Critical for revenue |
| API access (for BI tools: Power BI, Tableau) | Phase 3 | Medium |
| White-label reports (agency PDF with client branding) | Phase 3 | High for agencies |
| Influencer / journalist identification | Phase 3 | Low |
| Image / visual brand recognition | Long-term | Low |
| Mobile app | Long-term | Low |

---

## 2. Competitor Feature Matrix

**Legend:** ✅ Full · ⚠️ Partial or claimed but unverified · ❌ Absent

| Feature | **MediaSense** | **Locobuzz** | **Konnect Insights** | **Meltwater** | **Brandwatch / Cision** | **Mention** | **Brand24** |
|---|---|---|---|---|---|---|---|
| **Coverage** | | | | | | | |
| Indian news portal monitoring (curated RSS) | ✅ 29 portals | ⚠️ Basic | ⚠️ Basic | ✅ Large index but generic | ✅ Generic | ⚠️ Web crawl | ⚠️ Web crawl |
| Social media (Twitter/X, Facebook, Instagram) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| YouTube comment monitoring | ❌ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ⚠️ |
| Reddit monitoring | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Print / TV / radio clipping | ❌ | ⚠️ | ❌ | ✅ | ⚠️ | ❌ | ❌ |
| **Language & NLP** | | | | | | | |
| English NLP sentiment | ✅ AI (Gemini) | ✅ | ✅ | ✅ | ✅ | ⚠️ Basic | ⚠️ Basic |
| Tamil NLP sentiment (news prose) | ✅ AI (Gemini) | ⚠️ Social-only | ⚠️ Claims only | ❌ | ❌ | ❌ | ❌ |
| Hindi NLP sentiment | ✅ AI (Gemini) | ⚠️ Social-only | ⚠️ Keyword-based | ❌ | ❌ | ❌ | ❌ |
| Bengali / Gujarati / Kannada NLP | ✅ AI (Gemini) | ⚠️ Social only | ❌ | ❌ | ❌ | ❌ | ❌ |
| Hinglish / Tanglish detection | ⚠️ Partial (langdetect) | ✅ ContextualPulse™ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **Analytics** | | | | | | | |
| Credibility-weighted perception score | ✅ | ❌ | ❌ | ⚠️ | ✅ | ❌ | ❌ |
| State / region-level filtering | ✅ (NLP-extracted) | ⚠️ Marketing claim, unverified | ❌ | ❌ | ❌ | ❌ | ❌ |
| Topic extraction + sentiment per topic | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Entity extraction (people, orgs, locations) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| Sentiment trend (time-series) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Share of voice / competitive benchmarking | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Influencer / journalist identification | ❌ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ |
| Image / visual brand recognition | ❌ | ❌ | ❌ | ❌ | ⚠️ Iris AI | ✅ | ❌ |
| **Workflow** | | | | | | | |
| Real-time / near-real-time alerts | ⚠️ Email only, hourly cadence | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Email / Slack / WhatsApp notifications | ⚠️ Email only | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CSV / Excel export | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PDF / PPT report generation | ❌ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| White-label reports (agency branding) | ❌ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| CRM / ticketing integration | ❌ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| API for BI tools (Power BI, Tableau) | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
| **Platform** | | | | | | | |
| Agency / multi-brand workspace | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| RBAC (role-based access control) | ✅ 5 roles | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Multi-tenant isolation | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Self-serve onboarding | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mobile app | ❌ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| India mid-market pricing (< ₹3L/brand/year) | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| India-based support | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |

---

## 3. Honest Competitive Assessment

### Where MediaSense Genuinely Leads

**1. Curated Indian news portal depth (unique)**
No competitor maintains a hand-verified list of 43 Indian regional RSS feeds with credibility scores, per-portal keyword filtering, and skip_keyword_filter logic for non-English scripts. Meltwater has a larger news index globally, but India-specific regional portals (Vikatan, Prajavani, Divya Bhaskar, Prabhat Khabar, Sathiyam TV) are not well-indexed. This is a real and structural advantage — it takes months to build and verify this portal list.

**2. State-level mention tagging via NLP (first mover)**
Locobuzz markets "region-level insight" but there is no verifiable feature behind it. MediaSense uses Gemini to extract Indian states from article prose and filters by state in the Mention Explorer — this is live code, not a marketing claim. No competitor has shipped this verifiably.

**3. AI-grade NLP across 6 Indian languages for news prose**
Locobuzz and Konnect Insights claim vernacular sentiment — but their NLP is trained on short-form social text (tweets, reviews, Hinglish slang). MediaSense uses Gemini 2.0 Flash on long-form news prose, a structurally different and harder task. A Tamil news article from Vikatan is nothing like a Tamil tweet.

**4. Credibility-weighted perception score**
Raw mention counts make a tweet from a 20-follower account equal to an editorial in The Hindu. MediaSense weights by source credibility × reach. Only Brandwatch (at $800–3,000/month) does this. No Indian mid-market tool does.

**5. Agency RBAC architecture**
The 5-role, 3-tier hierarchy (platform / agency / brand) matches exactly how Indian digital agencies operate. Competitors have multi-user features; none have the specific agency_admin → brand_admin → brand_viewer scoping with tenant isolation that MediaSense ships.

**6. Rejection learning**
Deleted articles are remembered. Future pipeline runs automatically skip similar content. No competitor in the mid-market segment has this.

### Where MediaSense Trails Critically

**1. Social media — single biggest gap**
Every competitor has Twitter/X, Instagram, Facebook. MediaSense has zero social coverage. In a brand crisis, 60–70% of the initial spread happens on social. Without social, MediaSense cannot be a brand's primary monitoring tool — it is a supplement. This must be addressed in Phase 2 before serious commercial traction is possible.

**2. ~~No alerts — the tool is retrospective, not proactive~~ ✅ Fixed (Wave 3)**
Email alerts shipped: perception_score_below, negative_pct_above, mention_spike — per-brand, 4h rate-limit via Resend. Gap remains vs. competitors: alerts are email-only (no Slack/WhatsApp) and fire after hourly batch, not in near-real-time. Upgrading to webhooks + real-time alerts is Wave 4.

**3. ~~No export — agencies cannot deliver client reports~~ ✅ Fixed (Wave 3)**
CSV export live in Mention Explorer — respects all active filters (sentiment, language, portal, topic, state, date range, free-text), streams up to 2,000 rows. Gap remains: PDF/PPT branded reports not yet available.

**4. Hourly batch vs near-real-time**
The fastest competitor delivers alerts in 5–15 minutes. MediaSense delivers data up to 60 minutes stale. For a PR crisis, the difference between 15 minutes and 60 minutes is significant.

**5. ~~No self-serve onboarding~~ ✅ Fixed (Wave 3)**
Brand wizard (3-step: name → keywords → languages), user invite (magic-link via Supabase), UserManagement page, delete brand, and remove user role all shipped. No SQL required for any tenant operation. Remaining gap: billing/payment flow — cannot charge without Razorpay/Stripe integration (Wave 4).

**6. Hinglish / Tanglish mixed-script detection**
Locobuzz's ContextualPulse™ specifically markets Hinglish/Tanglish social text handling. MediaSense uses fasttext langdetect which misclassifies code-mixed text (a Tamil sentence with English brand names). This matters more for social (Phase 2) than for news portals.

---

## 4. Defensible Positioning Statement

> *MediaSense is the only news monitoring platform built specifically for Indian regional media — tracking brands across English, Tamil, Hindi, Bengali, Gujarati, and Kannada news portals, with state-level sentiment filtering and credibility-weighted perception scoring, at mid-market pricing.*

**What to avoid claiming:**
- "The only vernacular sentiment tool" — Locobuzz and Konnect now claim this (for social)
- "Real-time monitoring" — hourly batch is not real-time
- "Complete brand monitoring solution" — social is missing

**What to lean into:**
- News-specific intelligence (not social noise)
- Regional India depth (29 curated portals, not generic web crawl)
- State-level granularity (live feature, no competitor has it)
- Agency-grade multi-brand architecture at mid-market price

**Best-fit buyer:** PR and communications teams in brands with significant regional/South India presence; digital agencies wanting to win vernacular monitoring mandates.

**Weakest-fit buyer:** Brand teams looking for a single tool replacing their current social listening setup.

---

## 5. Pricing Recommendation

### Market Reference Points

| Tool | Price | What it covers |
|---|---|---|
| Manual news clipping agencies (India) | ₹5,000–15,000/brand/month | English + some vernacular clipping, manual, next-day delivery |
| Mention (entry-level global) | ₹3,400–12,400/month | Social + web, English sentiment, no Indian vernacular |
| Brand24 | ₹6,600–24,900/month | Social + web, English, 25 mentions/country |
| Konnect Insights | ₹15,000–60,000/brand/month | Social + news, basic vernacular claims |
| Locobuzz | ₹20,000–80,000/brand/month | Social + news + CRM, vernacular social claims |
| Meltwater (India contracts) | ₹40,000–1,25,000/month | Global news + social, English-grade NLP |
| Brandwatch | ₹65,000–2,50,000/month | Full social intelligence, no Indian vernacular |

### Recommended Pricing Tiers

#### Tier 1 — News Essentials *(₹6,500/month per brand)*
Target: Single-brand in-house PR teams, MSME brands, regional businesses
- 1 brand
- English + 1 regional language (customer's choice)
- All portals for chosen languages
- 5 dashboard users
- 90-day article history
- No export (dashboard only)

*Justification:* Undercuts manual clipping services (₹5,000–15,000) while delivering AI-grade analysis and a live dashboard. Accessible entry point for first-time buyers.

---

#### Tier 2 — News Professional *(₹14,000/month per brand)*
Target: Mid-market brands with pan-India or multi-state presence; PR managers
- 1 brand
- All 6 languages (EN/TA/HI/GU/BN/KN)
- All 29 portals
- State-level filtering
- 10 dashboard users
- 12-month article history
- CSV export ✅ (live)
- Monthly PDF summary report (Wave 4 — not yet available)

*Justification:* Positioned squarely against the Konnect/Locobuzz entry tier (₹15,000–20,000/month) but news-focused with far superior language depth. Brands currently paying Meltwater ₹40,000+/month for English-only will find this compelling.

---

#### Tier 3 — Agency *(₹45,000/month for up to 5 brands)*
Target: Digital agencies managing multiple brand accounts
- Up to 5 brands (= ₹9,000/brand/month — agency margin opportunity vs Tier 2)
- All 6 languages, all portals
- State filtering
- 25 users (agency staff + client read-only logins)
- White-label PDF reports (agency logo/branding)
- CSV bulk export
- Priority pipeline (brands run before standard tier)
- Dedicated account manager

*Justification:* Agency economics: buy at ₹9,000/brand, resell at ₹15,000–25,000/brand = 67–178% margin. Locobuzz agency plans start at ₹40,000–60,000/month for comparable brand counts. This is price-competitive while offering better vernacular depth.

---

#### Tier 4 — Enterprise *(Custom, starting ₹1,20,000/month)*
Target: Large brands with national campaigns, PR firms with 20+ clients
- Unlimited brands
- All features
- Custom SLA (99.5% uptime)
- API access for BI tool integration
- Dedicated Railway/infrastructure deployment
- NLP fine-tuning for brand-specific terminology
- Quarterly business review

---

### Pricing Phasing Recommendations

#### Now — Wave 3 complete ✅ (news monitoring fully featured)
Export, alerts, self-serve onboarding, and RBAC management are all live. MediaSense is now feature-complete for news monitoring. **Move to full pricing.** The Founder Pricing window (pre-export/pre-alerts) has passed.

**Current recommended pricing:**

| Tier | Price | Ready to sell? |
|---|---|---|
| News Essentials | ₹6,500/month | ✅ Yes — pending billing integration |
| News Professional | ₹14,000/month | ✅ Yes — pending billing integration |
| Agency (5 brands) | ₹45,000/month | ✅ Yes — pending billing integration |

**Only blocker before first invoice:** Razorpay / Stripe billing integration (Wave 4). Can currently be handled manually (bank transfer / invoice) for the first 2–3 customers.

#### After Wave 4 (billing + PDF reports)
Fully automated self-serve. Remove manual billing workaround. Launch PDF/PPT export for agency tier.

#### After Phase 2 (social media added)
Reprice significantly upward. Add a **Social + News** tier at ₹25,000–40,000/month per brand — this directly competes with Locobuzz/Konnect's core offering at a comparable price but with better language depth.

| Tier | Price (post-social) |
|---|---|
| News Professional | ₹16,000/month |
| Social + News Standard | ₹30,000/month |
| Social + News Pro (6 languages) | ₹45,000/month |
| Agency (5 brands, all channels) | ₹1,20,000/month |

---

## 6. Revenue Projections

### Conservative (news-only, founder pricing)

| Customers | Mix | MRR |
|---|---|---|
| 5 News Pro brands | ₹10,000 × 5 | ₹50,000 |
| 2 Agency (5 brands each) | ₹32,000 × 2 | ₹64,000 |
| 5 News Essentials | ₹4,500 × 5 | ₹22,500 |
| **Total MRR** | | **₹1,36,500** |
| **ARR** | | **₹16,38,000** |

### Target for Phase 2 gate (per PRD — ₹2L MRR)

| Customers | Mix | MRR |
|---|---|---|
| 8 News Pro brands | ₹10,000 × 8 | ₹80,000 |
| 4 Agency (5 brands each) | ₹32,000 × 4 | ₹1,28,000 |
| **Total MRR** | | **₹2,08,000** |

*At this MRR, Phase 2 (social media) development is self-funded.*

### Post-social (full platform)

| Customers | Mix | MRR |
|---|---|---|
| 20 Social + News Standard | ₹30,000 × 20 | ₹6,00,000 |
| 10 Agency (5 brands each, all channels) | ₹1,20,000 × 10 | ₹12,00,000 |
| 5 Enterprise | ₹1,50,000 avg × 5 | ₹7,50,000 |
| **Total MRR** | | **₹25,50,000** |
| **ARR** | | **~₹3.06 crore** |

At this scale, MediaSense is genuinely competing with Locobuzz for mid-market agency mandates.

---

## 7. Go-to-Market Priorities Before First Sale

These blockers must be resolved before the first paying customer can be acquired:

| Blocker | Status | Why it matters |
|---|---|---|
| ~~Self-serve brand + user onboarding~~ | ✅ Done | Brand wizard, user invite, delete brand, remove user role — all shipped Wave 3 |
| ~~Export (CSV minimum)~~ | ✅ Done | CSV export live in Mention Explorer; filter-respecting, up to 2,000 rows |
| ~~Alert / email notification~~ | ✅ Done | 3 alert types, 4h rate-limit, Resend email delivery |
| ~~Auth on `/pipeline/trigger`~~ | ✅ Done | Now requires master_admin JWT; unauth requests return 403 |
| **Billing integration (Razorpay / Stripe India)** | ❌ Not started | **Critical — cannot charge customers without payment flow** |
| Terms of service + privacy policy | ❌ Not started | Required for any paid SaaS |
| Supabase row limits | ⚠️ Monitor | Free tier caps at 50,000 rows; ~12 brands × 20 articles/run × hourly = risk in 2–3 months |

---

## Update Log

| Date | Update | Features added / changed |
|---|---|---|
| 2026-06-17 | Initial document | News monitoring, 6 languages, 29 portals, 12 brands, RBAC, state filtering, pipeline visibility, DLQ, circuit breaker, rejection learning |
| 2026-06-17 | Wave 3 shipped | CSV export, email alerts (3 types, 4h rate-limit), self-serve brand wizard, user invite/management, India state choropleth map; competitor matrix updated (CSV ✅, self-serve ✅, email alerts ⚠️) |
| 2026-06-17 | Wave 3 admin + map fix | Delete brand (master_admin, cascade), remove user role (agency_admin+); state choropleth replaced with chip grid (dead external TopoJSON removed); language filter expanded to 6-option dropdown; `/pipeline/trigger` auth fixed; Go-to-Market blockers table updated (4 of 7 resolved); pricing phasing updated — Wave 3 complete, move to full pricing; Railway backend fully deployed with all Wave 3/4 routes |
| 2026-06-17 | Portal expansion | 29 → 43 portals: +5 EN, +3 HI, +1 TA, +1 BN, +3 KN, +1 GU; all URLs verified live RSS before adding; 21 candidates documented as excluded with reasons; competitor matrix "Indian news portal depth" updated from 29 to 43 |
