# Media Perception & Sentiment Analysis System — Design Spec
**Date:** 2026-06-15
**Status:** Approved

---

## 1. Product Overview

A multi-tenant SaaS platform that monitors brand mentions across news portals (Phase 1), social media, and the web (Phase 2+) — in English and Tamil — and presents media perception and sentiment insights through an interactive web dashboard.

**Primary users:**
- Brand teams managing their own workspace
- Agencies managing multiple brand clients from a single account

**Languages:** English + Tamil (brand-configurable; additional languages added via plugin interface in later phases)

### Phased Rollout

| Phase | Sources | Languages | Infrastructure |
|---|---|---|---|
| **Phase 1 (current)** | English + Tamil news portals (RSS only) | English, Tamil | Free tier stack |
| **Phase 2** | + Social media (Twitter/X, Facebook, Instagram, LinkedIn, YouTube, Reddit) | English, Tamil | Upgrade compute as needed |
| **Phase 3** | + Web mentions, Google Alerts, GDELT | English, Tamil + new languages | Paid tiers, multi-region |

---

## 2. Architecture — Hybrid Pipeline

Six layers, each independently scalable:

```
[Multi-tenant SaaS Layer]
        ↓  brand config scopes collection & NLP
[Data Ingestion Layer]   — hourly scheduled collectors
        ↓  raw content → dedup → normalise
[Job Queue]              — AWS SQS, brand-scoped queues
        ↓  workers pull and process
[NLP Processing Layer]   — language detection → model router
        ↓  enriched content
[Data Storage Layer]     — PostgreSQL + TimescaleDB + S3
        ↓  served via FastAPI
[Web Dashboard]          — React SPA
```

**Deployment:** Fully API-based free-tier stack — Gemini API (primary NLP) + Groq API (fallback NLP) + Supabase + Cloudflare R2 + InfluxDB Cloud + Railway/Vercel. No self-hosted model infrastructure in Phase 1. Designed to migrate to AWS ap-south-1 when scale requires paid tiers.

---

## 3. Multi-Tenant Data Model

### Entity Hierarchy
```
Agency
  └── Brand  (1 agency : N brands)
        ├── BrandConfig  (keywords, states, languages)
        ├── User         (agency-level or brand-level)
        └── Mention → SentimentResult
```

### BrandConfig fields
- `keywords`: list of brand name variants, product names, campaign hashtags, spokesperson names
- `languages`: `["en", "ta"]` for MVP
- `states`: e.g., `["Tamil Nadu", "Puducherry"]`
- `competitors`: optional list for comparative tracking

### User Roles
| Role | Access |
|---|---|
| `agency_admin` | Full access across all managed brands |
| `agency_analyst` | Read-only across all managed brands |
| `brand_admin` | Full access to their brand workspace |
| `brand_viewer` | Read-only on their brand |

### Tenant Isolation
Every content row carries a `brand_id` foreign key. All queries are scoped by `brand_id` — no cross-tenant data exposure is possible at the query level.

---

## 4. Data Ingestion Layer

### Phase 1 Sources — News Portals Only (RSS, fully free)

**English News Portals**
| Portal | RSS Feed | Coverage |
|---|---|---|
| The Hindu | `thehindu.com/rss/` | National, South India focus |
| Times of India | `timesofindia.indiatimes.com/rss*` | National |
| NDTV | `feeds.feedburner.com/ndtvnews-*` | National |
| India Today | `indiatoday.in/rss/home` | National |
| Economic Times | `economictimes.indiatimes.com/rss*` | Business/economy |
| The News Minute | `thenewsminute.com/rss` | South India focused |
| Deccan Herald | `deccanherald.com/rss` | South India |
| The Wire | `thewire.in/rss` | National |

**Tamil News Portals**
| Portal | RSS Feed | Coverage |
|---|---|---|
| Dinamalar | `dinamalar.com/rss*` | Tamil Nadu statewide |
| Dinamani | `dinamani.com/rss*` | Tamil Nadu statewide |
| Dina Thanthi | `dinathanthi.com/feed/` | Tamil Nadu statewide |
| Vikatan | `vikatan.com/rss*` | Tamil Nadu, magazines |
| Puthiya Thalaimurai | `puthiyathalaimurai.tv/rss` | Tamil Nadu, news channel |
| Kalakkal Cinema (if applicable) | `kalakkal.com/rss` | Entertainment vertical |
| Tamil Murasu | `tamilmurasu.com.sg/feed/` | Tamil diaspora |

All sources use RSS/Atom feed parsing — zero API cost, no authentication required.

**Phase 2 Sources (deferred):** Twitter/X, Facebook, Instagram, LinkedIn, YouTube, Reddit, Google Alerts RSS, GDELT, NewsAPI.org

### Collection Schedule
- Hourly cron job per brand
- Each run collects only articles matching the brand's configured keywords, from portals relevant to the brand's configured states

### Deduplication
SHA-256 hash of `(source_domain + article_url)` stored in a dedupe table. Articles already processed in a prior run are skipped before entering the queue.

### Rate Limiting
Polite crawl delay of 2–5 seconds between requests per domain to respect portal servers.

---

## 5. NLP Processing Layer

### Language Detection
`fasttext` lid.176 model — detects 176 languages, runs locally, no API cost. Routes each content item to the correct NLP model.

### Model Routing (Phase 1)

All NLP is API-based — no self-hosted model infrastructure required in Phase 1.

| Language | Primary Model | Fallback Model | Notes |
|---|---|---|---|
| English | Gemini 2.0 Flash (Google AI API) | Groq — Gemma 2 9B | Both excellent for English sentiment |
| Tamil | Gemini 2.0 Flash (Google AI API) | Groq — Gemma 2 9B | Gemini trained on Tamil corpus; Gemma 2 9B is the strongest Groq option for Tamil |
| Mixed / Tanglish | Gemini 2.0 Flash | Groq — Gemma 2 9B | Gemini handles code-switching natively |

**Fallback trigger:** Groq is invoked when Gemini returns a 429 (rate limit) or 5xx error. The NLP router retries once on Gemini, then falls back to Groq. Results from both are tagged with `model_used` in the output schema.

**Batching strategy:** Group 2–3 short articles (≤800 tokens each) into a single Gemini request using structured JSON output. This multiplies effective throughput within the 1,500 req/day free tier — supporting up to ~4,500 articles/day per brand before hitting limits.

**Free tier limits:**
- Gemini 2.0 Flash: 1,500 requests/day, 1M tokens/minute (Google AI Studio key)
- Groq Gemma 2 9B: 6,000 requests/day, 15K tokens/minute

**Plugin interface:** Adding a new language = registering a new `LanguageHandler(lang_code, primary_model, fallback_model)`. No changes to pipeline core.

### Output Schema (per processed item)
```json
{
  "content_id": "sha256-hash",
  "brand_id": "uuid",
  "source": "twitter",
  "language": "ta",
  "language_confidence": 0.97,
  "original_text": "...",
  "sentiment_score": -0.72,
  "sentiment_label": "negative",
  "entities": ["BrandName", "ProductX", "Chennai"],
  "topics": ["customer_service", "product_quality"],
  "keywords": ["delay", "refund", "worst"],
  "hashtags": [],
  "source_credibility": 0.85,
  "reach_score": 1240,
  "processed_at": "2026-06-15T10:00:00Z"
}
```

### Perception Score
Composite 0–100 metric calculated per brand per time window:
- Sentiment score weighted by `source_credibility × reach_score`
- A negative tweet from a 50-follower account has minimal impact vs. a negative article in The Hindu
- Stored as hourly aggregate in TimescaleDB

**source_credibility** (0–1): pre-seeded lookup per source domain/handle — national newspapers score ~0.9, verified brand accounts ~0.85, unknown blogs ~0.3, anonymous social accounts ~0.2. Editable by brand admins.

**reach_score**: log-scaled follower count or estimated article readership, normalised to 0–10000.

---

## 6. Data Storage Layer

| Store | Purpose | Free Tier Technology | Free Tier Limits |
|---|---|---|---|
| **PostgreSQL** | Brands, users, config, article metadata, tenant isolation | **Supabase Free** | 500MB DB, 2 projects, includes Auth + Row-level security |
| **Time-series** | Sentiment timeseries, hourly aggregates, trend queries | **InfluxDB Cloud Free** | 10GB writes/month, 30-day retention, unlimited reads |
| **Object Storage** | Raw article archive, model inputs, audit trail | **Cloudflare R2 Free** | 10GB storage, 1M writes, 10M reads/month, zero egress fees |
| **Job Queue** | Hourly batch job coordination, brand-scoped queues | **Upstash Redis Free** | 10,000 commands/day, 256MB — sufficient for Phase 1 RSS volumes |

### Free Tier Capacity Assessment for Phase 1
- ~15 news portals × ~50 articles/hour × 24 hours = ~18,000 articles/day per brand
- Average article ~500 tokens → Claude Haiku cost ~$0.07/day per brand (very low)
- Storage: ~10KB per article × 18,000 = ~180MB/day → well within Cloudflare R2 free tier
- InfluxDB: 1 sentiment write per article = ~540K points/month per brand → within 10GB free limit

---

## 7. Web Dashboard

**Stack:** React (frontend) + FastAPI (backend API)

**Hosting (free tier):**
- Frontend → **Vercel Free** (unlimited hobby deployments, global CDN)
- Backend API → **Railway Free** ($5 credit/month, sufficient for Phase 1 traffic) or **Google Cloud Run Free** (2M requests/month)
- NLP inference → fully API-based (Gemini + Groq), no server to host

### Screens
1. **Overview** *(main screen)*
   - KPI row: Perception Score, Total Mentions, Positive %, Negative %, Neutral %
   - Sentiment trend line chart (7-day, hourly granularity) with campaign event annotations
   - Source breakdown (horizontal bar chart)
   - Language split (English / Tamil)
   - Recent mentions feed (original text, sentiment badge, source, timestamp)
   - Trending topics & hashtags (colour-coded by sentiment direction)
   - Last processed timestamp + next run countdown

2. **Mention Explorer** — filterable, searchable list of all mentions with full content, sentiment, source, language, and entity tags

3. **Sources** — deep drill-down by platform with sentiment breakdown per source

4. **Topics** — topic and hashtag trend analysis over time

5. **Languages** — English vs Tamil sentiment comparison, code-switching volume

### Navigation
Top nav with brand switcher (agency users see a dropdown of all their managed brands), section tabs, and date range picker.

---

## 8. Tech Stack Summary

### Phase 1 — Fully Free Stack (no self-hosted infrastructure)

| Layer | Technology | Free Tier Provider | Free Limit | Monthly Cost |
|---|---|---|---|---|
| Backend API | Python / FastAPI | Railway or Google Cloud Run | $5 credit/month or 2M req/month | **Free** |
| Frontend | React + TypeScript | Vercel | Unlimited hobby deployments | **Free** |
| NLP Primary — English + Tamil | Gemini 2.0 Flash | Google AI API (existing key) | 1,500 req/day, 1M tokens/min | **Free** |
| NLP Fallback — English + Tamil | Gemma 2 9B | Groq API | 6,000 req/day, 15K tokens/min | **Free** |
| Language Detection | `fasttext` lid.176 | Runs in-process | — | **Free** |
| RSS Parsing | `feedparser` Python lib | In-process | — | **Free** |
| Job Queue | Redis | Upstash Free | 10K commands/day | **Free** |
| Primary DB | PostgreSQL + Row-level security | Supabase Free | 500MB, 2 projects | **Free** |
| Time-series DB | InfluxDB | InfluxDB Cloud Free | 10GB writes/month, 30-day retention | **Free** |
| Object Storage | Cloudflare R2 | Cloudflare R2 Free | 10GB, zero egress | **Free** |
| Auth | Supabase Auth (JWT) | Included in Supabase Free | 50K MAU | **Free** |

**Total Phase 1 cost: $0/month** — all services are within permanent free tiers. No Oracle Cloud VM needed; no self-hosted models.

**Cost beyond free tiers** (if brand volume grows):
- Gemini 2.0 Flash: $0.075/M input tokens, $0.30/M output tokens
- Groq: $0.20/M tokens (pay-as-you-go)
- Upstash Redis: $0.20/100K commands beyond free tier

### Phase 2+ Migration Path
When scale exceeds free tiers: Supabase → AWS RDS, InfluxDB → TimescaleDB on RDS, Cloudflare R2 stays (best egress pricing), Railway → AWS ECS. NLP stays on Gemini/Groq APIs unless fine-tuned models are needed.

---

## 9. Out of Scope

### Phase 1 (deferred to Phase 2+)
- Social media sources (Twitter/X, Facebook, Instagram, LinkedIn, YouTube, Reddit)
- Web mentions (Google Alerts, GDELT, NewsAPI.org, general web scraping)
- Email / WhatsApp / PDF report delivery (dashboard only)
- Real-time streaming (hourly batch is sufficient)
- Languages beyond English and Tamil
- WhatsApp / Telegram scraping
- Competitor analysis module
- On-premise deployment option

---

## 10. Open Questions / Future Decisions

- **Gemini Tamil accuracy validation:** Before launch, benchmark Gemini 2.0 Flash against 100 Tamil news snippets with known sentiment labels. If F1 score < 0.75, consider adding `ai4bharat/indic-bert` as a third Tamil-specific option hosted on a free VM.
- **Gemini free tier per-brand scaling:** 1,500 req/day is a shared quota per API key. If multiple brands are onboarded simultaneously, implement per-brand rate tracking and graceful Groq fallback before the daily quota is hit — not after.
- **Groq Tamil quality floor:** Gemma 2 9B on Groq is acceptable for Tamil fallback but not ideal. Tag all Groq-processed Tamil results with `model_used: "groq-gemma2-9b"` so analysts can filter and spot-check for accuracy drift.
- **InfluxDB 30-day retention:** Trend queries beyond 30 days need a data rollup strategy — aggregate daily summaries into PostgreSQL before InfluxDB purges raw hourly data.
- **Upstash free limit:** 10K Redis commands/day is sufficient for Phase 1 (RSS only). Monitor as brands are onboarded; upgrade to Upstash Pay-as-you-go (~$0.20/100K commands) when needed.
- **Supabase 500MB limit:** Each brand's articles + metadata will grow over time. Monitor DB size; archive articles older than 90 days to Cloudflare R2 to keep PostgreSQL lean.
