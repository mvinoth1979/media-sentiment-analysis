# Product Requirements Document
## MediaSense — Media Perception & Sentiment Analysis Platform

**Version:** 1.0
**Date:** 2026-06-15
**Status:** Draft for Review
**Owner:** Product Team
**Related:** `docs/superpowers/specs/2026-06-15-media-sentiment-design.md`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Customer Pain Points](#3-customer-pain-points)
4. [Market Opportunity](#4-market-opportunity)
5. [Competitor Analysis](#5-competitor-analysis)
6. [Target Users & Personas](#6-target-users--personas)
7. [Product Vision & Goals](#7-product-vision--goals)
8. [Feature Requirements](#8-feature-requirements)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Success Metrics](#10-success-metrics)
11. [Phased Roadmap](#11-phased-roadmap)
12. [Risks & Mitigations](#12-risks--mitigations)

---

## 1. Executive Summary

Indian brands operating in regional markets are flying blind. The majority of media monitoring and sentiment analysis tools available today were built for English-speaking markets. For a brand with significant operations in Tamil Nadu — where 60–75% of brand mentions appear in Tamil-language media — existing tools offer an incomplete and dangerously misleading picture of public perception.

**MediaSense** is a multi-tenant SaaS platform that collects brand mentions from news portals, social media, and the web in **both English and vernacular Indian languages**, analyses sentiment using AI models trained on Indian language data, and delivers media perception reports through an interactive dashboard — at a price point accessible to Indian mid-market brands and digital agencies.

**Phase 1** focuses on English and Tamil news portals, built entirely on free-tier infrastructure to validate the core value proposition with zero operational cost.

---

## 2. Problem Statement

### The Vernacular Blind Spot in Indian Brand Monitoring

India has 900 million internet users. Over 600 million of them consume digital content primarily in languages other than English. Tamil Nadu alone has 75+ million internet users, the majority reading news in Tamil. Yet the brand monitoring tools that Indian marketing and communications teams use today were designed for English-first markets.

The result is a systematic blind spot: brand crises that start in vernacular media are missed until they cross into English coverage — often hours or days later, by which time reputation damage is already done. Positive sentiment in regional media goes uncaptured, making it impossible to measure the ROI of regional campaigns.

This is not a niche problem. It affects every FMCG brand, telecom company, financial institution, healthcare brand, and political organisation operating across Indian states.

---

## 3. Customer Pain Points

### 3.1 For Brand Teams (In-House Marketing / Communications / PR)

#### Pain Point 1 — The Vernacular Blind Spot
> *"We know something is being said about us in Tamil newspapers but we have no idea what. Our agency sends us English clips only."*

Brands in Tamil Nadu, Kerala, Andhra Pradesh, and Maharashtra generate the majority of their media coverage in vernacular languages. Current monitoring tools index only English content, meaning:
- A damaging article in *Dinamalar* (Tamil, 2M+ daily readers) goes undetected
- A viral positive campaign in *Vikatan* (Tamil magazine, 600K+ subscribers) is not measured
- Sentiment scores are calculated only on English mentions, which are unrepresentative of actual public perception

**Frequency:** Affects every brand with regional presence. Acute for brands in South India, Maharashtra, Bengal, and Gujarat.

#### Pain Point 2 — Delayed Crisis Detection
> *"By the time we found out about the negative campaign on Twitter in Tamil, it had already reached mainstream English news. We lost 36 hours."*

Manual media monitoring (agency sends morning clips via email) means brands discover crises after they have already escalated. No tool currently provides:
- Hourly monitoring of Tamil news portals
- Automated sentiment spike detection
- Early warning before English media picks up a vernacular-originated story

**Business impact:** A 36-hour delay in crisis response can mean the difference between a managed issue and a reputation crisis requiring executive-level intervention.

#### Pain Point 3 — Fragmented Tooling
> *"We use one tool for social media, our agency uses a media clipping service for news, and we export everything to Excel to compile the weekly report. It takes our analyst 4 hours every Friday."*

Brand teams currently operate with a patchwork of tools:
- Social listening tool (e.g., Sprout Social, Hootsuite) for social media
- Media clipping service or Google Alerts for news
- Manual export and Excel compilation for consolidated reporting
- No single source of truth for brand perception across all channels

**Cost:** 3–5 analyst hours per week per brand, plus subscription costs for multiple tools.

#### Pain Point 4 — Prohibitive Cost of Enterprise Tools
> *"Meltwater wanted ₹12 lakh a year. We're a mid-sized brand. That's half our digital marketing budget."*

Enterprise-grade media monitoring tools (Meltwater, Brandwatch, Talkwalker) are priced for Fortune 500 companies. Indian mid-market brands — with annual digital marketing budgets of ₹50–200 lakh — cannot justify ₹6–20 lakh/year for a monitoring tool, particularly one that doesn't even support Tamil.

**Market gap:** No affordable tool exists that combines English + Tamil (or other vernacular) monitoring for the Indian mid-market segment.

#### Pain Point 5 — No State-Level Granularity
> *"We need to understand sentiment in Tamil Nadu separately from Delhi. Our product positioning is different in each market."*

National brands run different campaigns in different states. Current tools aggregate sentiment nationally, making it impossible to:
- Compare sentiment in Tamil Nadu vs. Maharashtra vs. Delhi
- Attribute a regional campaign to a local sentiment shift
- Identify which states are driving positive or negative coverage

#### Pain Point 6 — Source Credibility Not Weighted
> *"A tweet from a 20-follower account and an article in The Hindu both show up as 'mentions'. How are we supposed to make decisions from that?"*

Raw mention counts treat all sources equally. A negative tweet from an anonymous account should not have the same weight as a critical editorial in a national newspaper. No tool in the mid-market segment offers credibility-weighted sentiment scoring.

---

### 3.2 For Digital Agencies (Managing Multiple Brand Clients)

#### Pain Point 7 — Multi-Brand Reporting Overhead
> *"We have 14 brand clients. Every Monday morning my team spends the whole day pulling reports from three different tools and compiling them into PowerPoint. It's not sustainable."*

Agencies managing 10–20 brand clients face compounding versions of all the above pain points. They need:
- A single login to monitor all clients simultaneously
- Automated report generation, not manual compilation
- Alerts that notify account managers of client-specific issues without logging in

#### Pain Point 8 — Inability to Win Regional Brand Clients
> *"We lost a pitch to a Tamil Nadu FMCG brand because we couldn't demonstrate Tamil media monitoring. The competitor agency had a local tool."*

Agencies pitching to regional brands are at a disadvantage because they cannot offer vernacular media monitoring. This is a direct revenue loss — regional brands (Tamil Nadu, Kerala, Maharashtra, Bengal) represent a significant and growing segment of Indian digital marketing spend.

#### Pain Point 9 — No Unified Perception Score for Client Presentations
> *"Our client asks 'what is our brand health this month?' and I have to give them a spreadsheet. I want to give them a single number they can track over time."*

Agencies need a client-friendly, single-metric perception score that can be trended over time and presented in board-level reports — without requiring the client to understand the underlying methodology.

---

## 4. Market Opportunity

### Indian Digital Marketing & Media Monitoring Landscape

| Metric | Value | Source / Notes |
|---|---|---|
| Indian internet users | 900M+ (2025) | TRAI |
| Non-English internet users | 600M+ | Google KPMG India Report |
| Tamil internet users | 75M+ | State-level estimates |
| Indian digital ad spend | $7.5B (2025), 28% CAGR | Dentsu India |
| Brand monitoring / social listening market (India) | ~$180–220M (2025) | Industry estimates |
| Mid-market brands with digital presence | 50,000+ | MSME + listed company count |
| Digital agencies in India | 5,000+ | IAMAI |
| Average agency manages | 8–15 brand clients | Primary research estimate |

### The Vernacular Gap as a Market Driver

- Existing players cover English well; vernacular coverage is the unserved gap
- Tamil is the highest-priority vernacular: 4th most-spoken language in India, significant diaspora (Singapore, Malaysia, Sri Lanka), strong digital media ecosystem
- Post-Phase 1, expansion to Telugu (90M speakers), Kannada (55M), Malayalam (35M), Marathi (95M), Bengali (100M) represents a large addressable market

### Pricing Opportunity

| Segment | Willingness to Pay | Current Options |
|---|---|---|
| Large enterprise brands | ₹8–20L/year | Meltwater, Brandwatch (poor vernacular) |
| Mid-market brands | ₹1.5–5L/year | Under-served — no good option |
| Digital agencies (per-brand seat) | ₹50K–1.5L/brand/year | Fragmented tools, no vernacular |
| Regional brands (Tamil Nadu focus) | ₹75K–2L/year | No vernacular tool available |

**MediaSense target segment:** Mid-market brands + digital agencies at ₹1–3L/brand/year — a price point that is 70–85% cheaper than enterprise tools while offering superior vernacular coverage.

---

## 5. Competitor Analysis

### 5.1 Indian / Regional Competitors

#### Locobuzz
- **HQ:** Mumbai, India
- **Founded:** 2015
- **Coverage:** Social media monitoring (Twitter, Facebook, Instagram), basic news monitoring
- **Languages:** English only; no Tamil/vernacular
- **Pricing:** ₹20,000–₹80,000/month
- **Strengths:** CRM integration, Indian customer support, established brand
- **Weaknesses:** Zero vernacular language support; social-heavy, weak news portal coverage; no state-level filtering; UI considered outdated by users
- **Verdict:** Direct competitor for English social monitoring; zero overlap on vernacular news — our biggest differentiator

#### Konnect Insights
- **HQ:** Pune, India
- **Founded:** 2013
- **Coverage:** Social listening, mentions, basic sentiment
- **Languages:** English primary; limited Hindi (keyword matching only, not NLP)
- **Pricing:** ₹15,000–₹60,000/month
- **Strengths:** Good social API coverage, omnichannel routing
- **Weaknesses:** No Tamil/South Indian vernacular; sentiment analysis is rule-based (keyword matching), not AI-driven; limited news portal coverage
- **Verdict:** Competes on social monitoring; no vernacular sentiment capability

#### Simplify360
- **HQ:** Bengaluru, India
- **Founded:** 2012
- **Coverage:** Social media analytics, mentions, customer experience
- **Languages:** English only
- **Pricing:** ₹12,000–₹50,000/month
- **Strengths:** Customer experience focus, ticketing integration
- **Weaknesses:** No vernacular; focused on customer service use case more than brand perception/PR; limited news monitoring
- **Verdict:** Partially overlapping; primarily a customer service tool, not a brand perception tool

#### Unbox Social
- **HQ:** Gurugram, India
- **Founded:** 2017
- **Coverage:** Social media analytics (owned channels focus)
- **Languages:** English only
- **Pricing:** ₹5,000–₹25,000/month
- **Strengths:** Affordable, easy to use, good for owned channel analytics
- **Weaknesses:** Primarily owned channel analytics (not brand mention monitoring); no news monitoring; no vernacular; no agency multi-brand feature
- **Verdict:** Different use case (owned analytics vs. earned media monitoring); low overlap

---

### 5.2 Global Competitors Operating in India

#### Meltwater
- **HQ:** San Francisco, USA
- **Coverage:** News monitoring (global), social listening, print clipping
- **Languages:** English primary; some language detection but no Tamil NLP
- **Pricing:** ₹5–15L/year (enterprise contracts)
- **Strengths:** Largest news database globally, strong English coverage, polished UI, good reporting
- **Weaknesses:** Prohibitively expensive for Indian mid-market; no Tamil/South Indian vernacular analysis; India-specific news portal coverage is inconsistent; no state-level filtering
- **Verdict:** Enterprise-only price; vernacular gap; our primary aspirational competitor to unseat in mid-market

#### Brandwatch (now part of Cision)
- **HQ:** Brighton, UK
- **Coverage:** Social listening, consumer research, news monitoring
- **Languages:** 27 languages — no Indian vernacular languages
- **Pricing:** $800–$3,000+/month
- **Strengths:** Excellent social data depth, AI-powered insights, strong analytics
- **Weaknesses:** No Tamil/Indian vernacular; India pricing is very high; limited Indian news portal indexing
- **Verdict:** Global leader but India-irrelevant for vernacular; enterprise pricing

#### Sprout Social
- **HQ:** Chicago, USA
- **Coverage:** Social media management + listening
- **Languages:** English only for sentiment
- **Pricing:** $249–$999/month
- **Strengths:** Excellent UX, strong social media management features
- **Weaknesses:** No news portal monitoring; no vernacular sentiment; social-only; not India-specific
- **Verdict:** Social management tool, not a brand perception platform; different primary use case

#### Mention
- **HQ:** Paris, France
- **Coverage:** Web mentions, basic social monitoring
- **Languages:** 42 languages for detection, English-only sentiment
- **Pricing:** $41–$149/month
- **Strengths:** Affordable entry point, good web crawling
- **Weaknesses:** No Tamil/Indian vernacular sentiment; no Indian news portal depth; no state-level filtering; sentiment is basic (positive/negative/neutral only)
- **Verdict:** Closest to our price point but zero vernacular capability; shallow sentiment

#### Talkwalker
- **HQ:** Luxembourg
- **Coverage:** Social listening, news, blogs, TV/radio monitoring
- **Languages:** 187 languages detected; limited Indian language NLP
- **Pricing:** $9,000+/year
- **Strengths:** Comprehensive data sources, AI-powered Visual Intelligence
- **Weaknesses:** Very expensive; Indian vernacular NLP is weak despite language detection; no Indian state-level granularity
- **Verdict:** Enterprise-tier competitor; strong globally but weak on Indian vernacular

---

### 5.3 Competitor Gap Analysis Matrix

| Capability | MediaSense (P1) | Locobuzz | Konnect | Meltwater | Brandwatch | Mention |
|---|---|---|---|---|---|---|
| Tamil news monitoring | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Tamil sentiment (AI NLP) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| English news portals | ✅ | ⚠️ Partial | ⚠️ Partial | ✅ | ✅ | ⚠️ Partial |
| Social media monitoring | ❌ Phase 2 | ✅ | ✅ | ✅ | ✅ | ✅ |
| State-level filtering | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Credibility-weighted score | ✅ | ❌ | ❌ | ⚠️ Partial | ✅ | ❌ |
| Agency multi-brand view | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| India mid-market pricing | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Indian customer support | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ |

**Key insight:** No competitor offers Tamil-language AI sentiment analysis at any price point. This is our primary and defensible differentiator.

---

### 5.4 Our Differentiation

1. **Tamil + English news portal monitoring** — the only product to do this with AI-grade NLP
2. **State-level filtering** — brand perception by state, not just nationally
3. **Credibility-weighted Perception Score** — a single, investable metric, not raw mention counts
4. **Affordable for Indian mid-market** — ₹1–3L/year vs. ₹5–20L for enterprise tools
5. **Agency-first multi-brand architecture** — designed for how Indian digital agencies actually work
6. **Expandable vernacular architecture** — Tamil first, then Telugu, Kannada, Malayalam as Phase 2+

---

## 6. Target Users & Personas

### Persona 1 — Priya, Head of Communications, FMCG Brand (Chennai)

- **Role:** Head of PR and Communications at a mid-sized South Indian FMCG brand (₹500 Cr revenue)
- **Team:** 3 people — herself, a digital analyst, and a PR executive
- **Tools currently used:** Google Alerts + a WhatsApp group where the agency sends morning clips + Sprout Social for owned social
- **Pain:** "I have no idea what the Tamil press is saying about us until my PR agency calls. By then, it's usually already a problem."
- **Goal:** Know about brand mentions in Tamil and English news within 1 hour of publication; see a consolidated perception score to share with CMO in weekly meetings
- **What she'll pay:** ₹1.5–2.5L/year if it genuinely covers Tamil news

### Persona 2 — Rajan, Founder, Digital Agency (Coimbatore)

- **Role:** Founder of a 12-person digital marketing agency serving 10 brand clients (mix of Tamil Nadu local brands and pan-India brands with TN presence)
- **Pain:** "My team spends every Monday compiling reports. I've lost two Tamil-language brand pitches because I couldn't show Tamil monitoring capability."
- **Goal:** Single dashboard for all 10 brands; auto-generated weekly perception reports; something impressive to show in new business pitches
- **What he'll pay:** ₹40,000–80,000/brand/year (agency margin model — charges clients ₹60K–1L/brand/year)

### Persona 3 — Meenakshi, Digital Marketing Manager, Telecom Brand (Pan-India)

- **Role:** Digital marketing manager at a pan-India telecom with strong South India market
- **Tools:** Meltwater (for English/national) + nothing for Tamil
- **Pain:** "Meltwater costs us ₹12L a year and doesn't even cover Tamil media. I need a supplementary tool or a better alternative."
- **Goal:** Replace or supplement Meltwater for Tamil and English news monitoring at a fraction of the cost
- **What she'll pay:** ₹3–5L/year for comprehensive English + Tamil coverage

---

## 7. Product Vision & Goals

### Vision
*Every Indian brand, regardless of size or budget, should be able to hear what is being said about them in the language their customers actually speak.*

### Mission
Provide the most accurate, affordable, and vernacular-inclusive brand perception monitoring platform for the Indian market.

### Phase 1 Goals (English + Tamil News Portals)
1. Collect and analyse brand mentions from 15 curated English + Tamil news portals hourly
2. Deliver AI-grade sentiment analysis (Gemini 2.0 Flash primary, Groq fallback)
3. Present results in a polished multi-tenant dashboard (brand + agency workspaces)
4. Achieve F1 ≥ 0.80 on Tamil sentiment classification
5. Operate at $0/month infrastructure cost within free-tier limits

### Phase 2 Goals (Social Media Added)
1. Add Twitter/X, Facebook, Instagram, LinkedIn, YouTube, Reddit
2. Maintain Tamil + English NLP quality across social content (shorter, noisier text)
3. Launch state-level sentiment heatmap
4. Support 3+ additional vernacular languages (Hindi, Telugu, Kannada)

---

## 8. Feature Requirements

### 8.1 Phase 1 — News Portal Monitoring (Must Have)

#### F1.1 — Brand Workspace Setup
- Brand admin can create a workspace with brand name, keyword list (variants, products, hashtags, spokespeople), state/region list, and language selection
- Support for Tamil-script keywords (நடிகர், product names in Tamil)
- Agency admin can create and manage multiple brand workspaces from a single login

#### F1.2 — RSS Feed Collection Engine
- Collect articles hourly from 15 pre-configured news portals (8 English, 7 Tamil)
- Filter articles by brand keyword match before processing
- Deduplicate articles across runs using URL hash
- Store raw article text, title, author, publication date, portal name, URL in object storage

#### F1.3 — Language Detection
- Detect article language using `fasttext` lid.176 model
- Tag each article with detected language and confidence score
- Route to correct NLP model based on language

#### F1.4 — Sentiment Analysis (English)
- Use Gemini 2.0 Flash to classify English articles as positive / negative / neutral
- Extract named entities (brand, product, person, location)
- Extract key topics (product quality, pricing, customer service, leadership, campaign)
- Extract top keywords
- Return structured JSON output with confidence scores

#### F1.5 — Sentiment Analysis (Tamil)
- Use Gemini 2.0 Flash for Tamil sentiment classification
- Same output schema as English
- Groq (Gemma 2 9B) as automatic fallback on rate limit or error
- Tag result with `model_used` field for quality tracking

#### F1.6 — Credibility-Weighted Perception Score
- Calculate per-brand perception score (0–100) each hour
- Weight sentiment by source credibility (pre-seeded per portal) × reach score
- Store hourly aggregate in InfluxDB time-series
- Expose 7-day, 30-day trend

#### F1.7 — Dashboard — Overview Screen
- KPI row: Perception Score, Total Mentions, Positive %, Negative %, Neutral %
- Sentiment trend line chart (7-day, hourly granularity) with annotation support
- Source breakdown (by portal)
- Language split (English vs Tamil)
- Recent mentions feed (article title, excerpt, sentiment badge, portal, timestamp)
- Trending keywords and topics
- Last processed timestamp + next scheduled run countdown

#### F1.8 — Dashboard — Mention Explorer
- Full list of all collected articles matching brand keywords
- Filters: date range, sentiment, language, portal, topic
- Search by keyword within collected content
- Expandable article view with full sentiment breakdown

#### F1.9 — Dashboard — Source Breakdown
- Per-portal mention volume, sentiment distribution, average credibility score
- Sortable table + bar chart

#### F1.10 — Dashboard — Topics View
- Topic cluster view showing volume and sentiment per topic
- Trend over time per topic (e.g., "product_quality" mentions trending negative this week)

#### F1.11 — Multi-Tenant Access Control
- Agency accounts with sub-brand workspaces
- Role-based access: agency_admin, agency_analyst, brand_admin, brand_viewer
- Row-level security: brand users cannot see other brands' data
- JWT-based auth via Supabase Auth

#### F1.12 — Hourly Job Pipeline
- Cron-triggered hourly collection per brand
- Job queue (Upstash Redis) for brand-scoped processing
- Dead-letter queue for failed jobs with retry (max 3 attempts)
- Job completion logged with article count, processing time, error count

---

### 8.2 Phase 2 — Social Media (Should Have, Post-Phase 1)

- Twitter/X API v2 integration (brand keyword search)
- Facebook Page mentions (OAuth per brand)
- Instagram brand mentions (OAuth per brand)
- LinkedIn company page mentions
- YouTube comment monitoring on brand videos
- Reddit keyword monitoring
- Hashtag tracking across social platforms
- State-level sentiment heatmap (India map)

### 8.3 Phase 3 — Web Mentions + Expanded Vernacular (Nice to Have)

- Google Alerts RSS, GDELT, NewsAPI.org web mention aggregation
- Hindi, Telugu, Kannada, Malayalam, Marathi, Bengali language support
- Competitor brand monitoring (configurable per workspace)
- Campaign tagging (annotate events on sentiment timeline)
- WhatsApp Business API integration (brand-owned channels)

---

## 9. Non-Functional Requirements

| Requirement | Target | Notes |
|---|---|---|
| **Collection latency** | Articles collected within 60 min of publication | Hourly batch window |
| **NLP processing time** | < 30 min to process all brand articles per hourly run | Must complete before next run starts |
| **Dashboard load time** | Overview screen < 2 seconds | React + FastAPI + cached aggregates |
| **Tamil sentiment F1** | ≥ 0.80 on news text | Benchmark before launch |
| **English sentiment F1** | ≥ 0.88 on news text | Gemini 2.0 Flash baseline |
| **Uptime** | 99% monthly | Acceptable for Phase 1 (free tier) |
| **Data retention** | Raw articles: 90 days in PostgreSQL, then archived to R2; Sentiment timeseries: 30 days in InfluxDB, daily rollups to PostgreSQL indefinitely | |
| **Tenant isolation** | Zero cross-brand data exposure at query level | Row-level security on all content tables |
| **API security** | JWT auth on all endpoints; rate limiting per tenant | |
| **Scalability** | Architecture supports 50+ brands within free-tier limits | ~360–900 relevant articles/day per brand |

---

## 10. Success Metrics

### Phase 1 Launch Metrics (First 90 Days)

| Metric | Target |
|---|---|
| Brands onboarded | 5 (3 direct brands, 2 agencies each with 2–3 brands) |
| NLP accuracy — Tamil F1 | ≥ 0.80 |
| NLP accuracy — English F1 | ≥ 0.88 |
| Collection reliability | ≥ 95% of hourly runs complete within 45 min |
| Dashboard NPS | ≥ 40 |
| Weekly active users per brand | ≥ 3 sessions/user/week |

### Product-Market Fit Signals

| Signal | Threshold |
|---|---|
| Users who would be "very disappointed" without the product (Sean Ellis test) | ≥ 40% |
| Agencies who use it in a new business pitch | 2+ within 60 days |
| Brands who cite Tamil coverage as primary reason for signing up | ≥ 60% |
| Monthly churn rate | < 5% |

### Business Metrics (Phase 1 → Phase 2 Gate)

| Metric | Target |
|---|---|
| Monthly Recurring Revenue | ₹2L+ MRR before Phase 2 development starts |
| Paying brand workspaces | 10+ |
| Net Promoter Score | ≥ 45 |

---

## 11. Phased Roadmap

```
Phase 1 — Foundation (Weeks 1–12)
├── Data Ingestion: RSS collector for 15 news portals (English + Tamil)
├── NLP: Gemini 2.0 Flash primary + Groq fallback
├── Storage: Supabase + InfluxDB + Cloudflare R2
├── Dashboard: Overview, Mention Explorer, Sources, Topics, Languages
├── Auth: Multi-tenant (brand + agency) via Supabase Auth
└── Infra: Railway (backend) + Vercel (frontend) + Upstash Redis (queue)

Phase 2 — Social Media (Weeks 13–22, after PMF validation)
├── Social collectors: Twitter/X, Facebook, Instagram, LinkedIn, YouTube, Reddit
├── Expanded NLP: Hindi, Telugu support
├── State-level heatmap
└── Upgrade infrastructure as volume grows

Phase 3 — Vernacular Expansion + Web (Weeks 23–36)
├── Web mentions: Google Alerts RSS, GDELT, NewsAPI
├── Languages: Kannada, Malayalam, Marathi, Bengali
├── Competitor tracking module
├── Campaign annotation and correlation
└── API tier for BI tool integration (Power BI, Tableau)
```

---

## 12. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Gemini 2.0 Flash Tamil accuracy below F1 0.80 threshold | Medium | High | Pre-launch benchmark; fallback to `ai4bharat/indic-bert` self-hosted if needed |
| News portal RSS feeds breaking or changing structure | High | Medium | Automated RSS health checks; manual fallback scraper per portal; alert on < 5 articles/hour from active portal |
| Gemini free tier (1,500 req/day) insufficient at scale | Medium | Medium | Batching (2–3 articles/request); Groq fallback absorbs overflow; upgrade to Gemini paid at ₹6/M tokens if needed |
| Supabase 500MB limit hit as brands accumulate data | Medium | Medium | Article archival to Cloudflare R2 after 90 days; store only metadata + NLP outputs in PostgreSQL |
| Tamil news portals blocking automated RSS fetching | Low | Medium | Polite crawl delays (2–5s); rotate User-Agent; respect robots.txt; direct RSS is explicitly intended for consumption |
| Competitor (Locobuzz / Konnect) launches Tamil support | Low | High | Speed to market is the moat; establish brand before they catch up; deepen to 5+ vernacular languages |
| Brand keyword false positive rate too high (unrelated mentions) | Medium | Medium | Configurable keyword exclusion lists; minimum keyword match threshold; user-reported false positive feedback loop |

---

*Document ends. For technical architecture details see `docs/superpowers/specs/2026-06-15-media-sentiment-design.md`.*
