# MediaSense — Competitive Analysis & Pricing Strategy

> **Last updated:** 2026-06-21 (Phase 2.1 Reddit live; Phase 3.2 structured issue taxonomy + YouTube creator vs audience split)
> **Based on:** Live codebase audit + competitor research (June 2026)
> Update this document when major features ship (social media, export, alerts, billing).

---

## 1. What Is Live in MediaSense Today (Verified Against Code)

| Feature | Status | Notes |
|---|---|---|
| News portal ingestion — English | ✅ Live | 17 portals (The Hindu, TOI, NDTV, India Today, ET, Indian Express, Deccan Chronicle, Hindustan Times, Mint, Deccan Herald, The Quint, News18, The Wire, Scroll, Firstpost, LiveMint, Business Standard) |
| News portal ingestion — Tamil | ✅ Live | 12 portals (Hindu Tamil, Vikatan, Samayam, Polimer, Maalaimalar, Daily Thanthi, Tamil Murasu, Oneindia Tamil, News Tamil, Puthiyathalaimurai, Sathiyam TV, Dinamalar) |
| News portal ingestion — Hindi | ✅ Live | 11 portals (Navbharat Times, Amar Ujala, Jagran, NDTV India, Hindustan, Dainik Bhaskar, Prabhat Khabar, Hari Bhoomi, Jansatta, Patrika, Zee News Hindi) |
| News portal ingestion — Bengali | ✅ Live | 4 portals (Ei Samay, Ananda Bazar, Sangbad Pratidin, ABP Ananda) |
| News portal ingestion — Kannada | ✅ Live | 9 portals (Prajavani, Vijaya Karnataka, Udayavani, Kannada Prabha, TV9 Kannada, Public TV, Suvarna News, Vartha Bharati, Vijayavani) |
| News portal ingestion — Gujarati | ✅ Live | 4 portals (Divya Bhaskar, Gujarat Samachar, Chitralekha, Sandesh) |
| **YouTube video monitoring** | ✅ Live | Keyword search (YouTube Data API v3, 100 units/search) + brand channel RSS (free, no quota). Skips Shorts (≤61s). Up to 10 videos per brand per run |
| **YouTube channel RSS (brand-owned channels)** | ✅ Live | Free — no API quota used. Up to 15 latest uploads per channel per run. Configured per brand via `youtube_channel_ids` |
| **YouTube comment monitoring** | ✅ Live | Top comments by relevance, up to 50 per brand per run. Each comment is a separate NLP-scored article with `source_type=youtube_comment` |
| **YouTube credibility scoring** | ✅ Live | Tiered: verified brand channel 0.90 · >1M subs 0.75 · 100K–1M subs 0.65 · <100K subs 0.50 · comments 0.45 |
| **YouTube reach metadata** | ✅ Live | View count, like count, comment count, subscriber count, duration stored in `reach_metadata` JSONB. Shown as "1.5M views" / "42 likes" in Mention Explorer |
| **YouTube-aware NLP** | ✅ Live | Separate LLM prompt path for `youtube_comment` (emoji signals, slang, code-switching) vs `youtube_video` (description > clickbait title) vs `news` (journalistic framing) |
| **YouTube quota manager** | ✅ Live | 10,000 units/day budget; circuit breaker on 403 quota exhausted; resets midnight Pacific |
| AI sentiment analysis (Gemini primary, Groq fallback) | ✅ Live | 3-class: positive/negative/neutral with confidence score |
| Entity extraction (brand, person, org, location) | ✅ Live | Per-article, returned in API and dashboard |
| Topic extraction | ✅ Live | Per-article, used in Topics View |
| Keyword extraction | ✅ Live | Aggregated in overview |
| Credibility-weighted Perception Score (0–100) | ✅ Live | Weighted by source credibility × reach; not raw mention count |
| Sentiment trend chart (7-day / 30-day) | ✅ Live | InfluxDB time-series, hourly granularity |
| Mention Explorer with 8 filters | ✅ Live | Sentiment, language, **source type** (news/YT video/YT comment), portal, topic, state, date range, free-text search |
| Source Breakdown page | ✅ Live | Per-portal mention count + sentiment split; YouTube icon on youtube_ portals |
| Topics View page | ✅ Live | Per-topic count + sentiment split, sortable |
| State-level mention tagging | ✅ Live | NLP extracts Indian states from article content |
| State filter in Mention Explorer | ✅ Live | URL-synced, click-to-drill |
| State breakdown on Overview | ✅ Live | Top states by mention volume + sentiment |
| India state sentiment grid | ✅ Live | Chip grid per state, color-coded by sentiment ratio; hover tooltip; click-to-drill to filtered mentions |
| CSV export (Mention Explorer) | ✅ Live | Respects all active filters including source_type; streams up to 2,000 rows; includes source_type column |
| Email alert system | ✅ Live | 3 alert types: perception_score_below, negative_pct_above, mention_spike; per-brand; 4h rate-limit |
| Self-serve brand onboarding | ✅ Live | **4-step wizard** (name → keywords → languages → YouTube toggle + channel ID); agency_admin / master_admin only |
| **YouTube config in brand wizard** | ✅ Live | Step 4: toggle switch + channel ID tag input. `youtube_enabled` and `youtube_channel_ids` stored in `brand_configs`. Editable via `PUT /brands/{id}/config` |
| User invite & management | ✅ Live | Magic-link invite via Supabase; role assignment at brand or agency scope |
| Delete brand | ✅ Live | master_admin only; inline confirm; cascades all articles, configs, user_roles, dedupe hashes |
| Remove user role | ✅ Live | agency_admin+ can remove brand-scoped user access |
| Language filter (Mention Explorer) | ✅ Live | Dropdown: EN, TA, HI, GU, BN, KN; URL-synced |
| **Source type filter (Mention Explorer)** | ✅ Live | Dropdown: All / News / YT Videos / YT Comments; URL-synced; respected by CSV export |
| **YouTube Mentions KPI card** | ✅ Live | Red card on Overview; shows count of youtube_video + youtube_comment articles; conditional (hidden when 0) |
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
| **Wire-service syndication deduplication** | ✅ Live | PTI/ANI articles republished across N portals counted once via story-hash (first 8 significant title tokens); `syndication_count` tracks spread. Prevents mention inflation. |
| **Headline vs. body sentiment (separate scores)** | ✅ Live | Every news article carries `headline_sentiment_score`, `body_sentiment_score`, and a `sentiment_divergence` flag (abs diff ≥ 0.4). Zero extra API cost — same Gemini call. |
| **Editorial tone classification** | ✅ Live | Every news article tagged as `factual \| positive_frame \| negative_frame \| critical`. Added alongside headline/body scoring at no cost. |
| **Author/journalist name extraction** | ✅ Live | RSS `<author>`, `dc:creator`, `author_detail.name` tried in priority order. Foundation for journalist-beat tracking. |
| **Regulatory/government source flag** | ✅ Live | `is_regulatory_source` auto-set when article URL is `.gov.in` domain or title contains SEBI / RBI / Ministry of / Parliament / Supreme Court / Enforcement Directorate etc. (14 domains + keyword list). Critical for PSU/government client reporting. |
| **Reddit monitoring (Phase 2.1)** | ✅ Live | Public JSON API (no OAuth, no app registration). Keyword × subreddit search — 3 keywords × 5 subreddits × 10 posts + 5 top comments = up to 225 items/run. `source_type = reddit_post / reddit_comment`. reach_metadata: {upvotes, upvote_ratio, comment_count, subreddit}. r/ orange badge in Mention Explorer. Per-brand toggle + subreddit list in Channel Settings (brand wizard Step 4). Migration 015. |
| **Structured issue taxonomy (Phase 3.2)** | ✅ Live | Every article/comment classified into 12 predefined issue categories (Financial Performance, Regulatory & Compliance, Product Quality, Leadership & Governance, Crisis & Controversy, Awards & Recognition, CSR & Sustainability, Policy & Government, Competitive Landscape, Customer Experience, Brand Advocacy, Market Opportunity) — single Gemini/Groq call, zero extra API cost. `issue_category` stored on articles (migration 016). `/dashboard/issue-categories/{brand_id}` endpoint. TopIssuesTable has Clusters\|Categories toggle with color-coded severity accents. |
| **YouTube Creator vs Audience sentiment split (Phase 3.2)** | ✅ Live | `youtube_video` (creator) and `youtube_comment` (audience) sentiment displayed separately — two-column stacked bars (positive/neutral/negative %) + divergent video list (creator positive, audience negative) surfaced via portal_id grouping. `/dashboard/youtube-sentiment-split/{brand_id}` endpoint. |
| **Journalist Coverage page (Tier 1)** | ✅ Live | Table of journalists sorted by negative article count; avatar initial; stacked sentiment bar; negative% color-coded; expandable recent article rows. Powered by `/dashboard/journalist-coverage/{brand_id}` endpoint (Counter on author field). |
| **Editorial Tone analytics (Tier 1)** | ✅ Live | Recharts donut (factual/positive_frame/negative_frame/critical) + 4-row % bars; 8-week ISO trend; compact + expanded modes. `/dashboard/tone-breakdown/{brand_id}` endpoint. |
| **Divergent Headlines panel (Tier 1)** | ✅ Live | Top articles where headline sentiment diverges sharply from body sentiment (|diff| ≥ 0.4). `/dashboard/divergence-summary/{brand_id}` endpoint. |
| **Channel Settings page** | ✅ Live | Edit YouTube + Reddit config for existing brands (wizard is create-only). `GET/PUT /brands/{id}/config` endpoints. "Channel Settings" in sidebar (adminOnly). |
| Mobile responsive UI | ✅ Live | |
| **Compact single-screen dashboard (no scroll)** | ✅ Live | All 9 sections fit in one viewport — `h-screen overflow-hidden` root layout; `flex-[N] min-h-0` proportional row heights; compact prop variants for all section components |
| **Click-to-detail panel navigation** | ✅ Live | Every dashboard section and KPI card is clickable — opens a full second-screen detail with breadcrumb `← Executive Overview | [Section Name]`; back navigation returns to compact grid |
| **Full dashboard redesign (Phase 3)** | ✅ Live | Dark navy sidebar (BrandPulse brand, nav, brand selector, last-updated timestamp); light main area with card-based layout; Sentiment Trend area chart (indigo/amber/red gradient fills); Mentions by Source donut; Top Headlines 3-tab panel (Top Positive / Top Negative / Trending); Review Sites Summary (star rating + distribution bars + themes); Top Issues Table (topic + bar + net sentiment %); Sentiment by Source Table (stacked bar + score); Competitor Share of Voice donut; Alerts & Risks cards |
| **Mention Explorer — light theme + numbered pagination** | ✅ Live | `1–10 of 10+` counter; numbered paginator (← 1 2 →); 10 results per page |

### Not Yet Live (Planned)

| Feature | Phase | Priority |
|---|---|---|
| Twitter/X, Instagram, Facebook monitoring | Phase 3 | Critical — crisis channels |
| ~~Reddit monitoring~~ | ~~Phase 2.1~~ | ✅ Live — public JSON API, no approval required |
| Real-time / near-real-time ingestion (< 15 min) | Phase 3 | High |
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
| Indian news portal monitoring (curated RSS) | ✅ **43 portals** | ⚠️ Basic | ⚠️ Basic | ✅ Large index but generic | ✅ Generic | ⚠️ Web crawl | ⚠️ Web crawl |
| Social media (Twitter/X, Facebook, Instagram) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **YouTube video + comment monitoring** | ✅ **Live Phase 2.0** | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ⚠️ |
| Reddit monitoring | ✅ **Live Phase 2.1** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Print / TV / radio clipping | ❌ | ⚠️ | ❌ | ✅ | ⚠️ | ❌ | ❌ |
| **Language & NLP** | | | | | | | |
| English NLP sentiment | ✅ AI (Gemini) | ✅ | ✅ | ✅ | ✅ | ⚠️ Basic | ⚠️ Basic |
| Tamil NLP sentiment (news prose) | ✅ AI (Gemini) | ⚠️ Social-only | ⚠️ Claims only | ❌ | ❌ | ❌ | ❌ |
| Hindi NLP sentiment | ✅ AI (Gemini) | ⚠️ Social-only | ⚠️ Keyword-based | ❌ | ❌ | ❌ | ❌ |
| Bengali / Gujarati / Kannada NLP | ✅ AI (Gemini) | ⚠️ Social only | ❌ | ❌ | ❌ | ❌ | ❌ |
| Hinglish / Tanglish detection | ⚠️ Partial (langdetect; social-text NLP for YouTube) | ✅ ContextualPulse™ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| Source-type aware NLP (news vs. social text) | ✅ Live | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| **Analytics** | | | | | | | |
| Credibility-weighted perception score | ✅ | ❌ | ❌ | ⚠️ | ✅ | ❌ | ❌ |
| State / region-level filtering | ✅ (NLP-extracted) | ⚠️ Marketing claim, unverified | ❌ | ❌ | ❌ | ❌ | ❌ |
| Topic extraction + sentiment per topic | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Entity extraction (people, orgs, locations) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| Sentiment trend (time-series) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **YouTube reach analytics** (views, likes, subscribers) | ✅ Live | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ |
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
No competitor maintains a hand-verified list of 43 Indian regional RSS feeds with credibility scores, per-portal keyword filtering, and skip_keyword_filter logic for non-English scripts. Meltwater has a larger news index globally, but India-specific regional portals (Vikatan, Prajavani, Divya Bhaskar, Prabhat Khabar, Sathiyam TV, Dinamalar) are not well-indexed. This is a real and structural advantage — it takes months to build and verify this portal list.

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

**7. YouTube monitoring at zero marginal cost**
YouTube Data API v3 gives 10,000 units/day free — enough to monitor 12 brands for videos and comments at no cost. MediaSense uses the hybrid approach: free channel RSS for brand-owned channels (no quota cost) + keyword search for competitor mentions. YouTube credibility is tiered by subscriber count and flows into the same perception score formula as news. Competitors charge premium tier prices for YouTube coverage; MediaSense includes it at all price tiers.

**8. Source-type-aware NLP pipeline (news + social in one system)**
YouTube comments require different NLP than news prose — emoji carry sentiment weight, slang is intentional, mixed scripts (Hinglish, Tanglish) are the norm. MediaSense uses separate LLM prompt paths per `source_type`, with a short-text guard for <4-word comments (default neutral, avoids noise). This is the same inference pipeline — no separate social NLP stack, no separate data schema — which keeps the architecture simple and the cost low.

### Where MediaSense Trails Critically

**1. Twitter/X, Instagram, Facebook — crisis channels still missing**
YouTube has shipped (Phase 2.0), but Twitter/X, Instagram, and Facebook remain absent. In a brand crisis, the first 30 minutes of spread happen on Twitter. MediaSense captures the YouTube dimension of public opinion (long-form video reactions, comment threads) but misses the fastest-moving signal. This is the most important remaining gap. Phase 3 priority.

*Note: This is a smaller gap now. YouTube comments represent a meaningful share of Indian brand sentiment — especially for sectors like banking, FMCG, telecom — where YouTube is the primary platform for consumer video reviews.*

**2. Hourly batch vs near-real-time**
The fastest competitor delivers alerts in 5–15 minutes. MediaSense delivers data up to 60 minutes stale. For a PR crisis, the difference between 15 minutes and 60 minutes is significant.

**3. ~~No alerts~~ ✅ Fixed (Wave 3)**
Email alerts: perception_score_below, negative_pct_above, mention_spike — per-brand, 4h rate-limit via Resend. Remaining gap: alerts are email-only (no Slack/WhatsApp) and fire after hourly batch, not near-real-time.

**4. ~~No export~~ ✅ Fixed (Wave 3)**
CSV export live — respects all active filters including source_type, up to 2,000 rows. Remaining gap: PDF/PPT branded reports not yet available.

**5. ~~No self-serve onboarding~~ ✅ Fixed (Wave 3 + Phase 2.0)**
4-step wizard (name → keywords → languages → YouTube config), user invite, UserManagement, delete brand, remove user role. Remaining gap: billing/payment flow — cannot charge without Razorpay/Stripe (Wave 4).

**6. Hinglish / Tanglish mixed-script detection**
Locobuzz's ContextualPulse™ specifically markets Hinglish/Tanglish social text handling. MediaSense's YouTube NLP path handles it better than the news path (social-text prompt is emoji and slang-aware), but fasttext langdetect still misclassifies some code-mixed text. Lower priority now that YouTube NLP is handling it gracefully in practice.

---

## 4. Defensible Positioning Statement

> *MediaSense is the only monitoring platform built specifically for Indian regional media — tracking brands across 43 English, Tamil, Hindi, Bengali, Gujarati, and Kannada news portals and YouTube, with state-level sentiment filtering and credibility-weighted perception scoring, at mid-market pricing.*

**What to avoid claiming:**
- "The only vernacular sentiment tool" — Locobuzz and Konnect now claim this (for social)
- "Real-time monitoring" — hourly batch is not real-time
- "Complete brand monitoring solution" — Twitter/X, Instagram, Facebook still missing

**What to lean into:**
- News + YouTube intelligence in one unified dashboard (news NLP + social NLP, same pipeline)
- Regional India depth (43 curated portals, not generic web crawl)
- State-level granularity (live feature, no competitor has it verifiably)
- YouTube reach analytics (view/like counts visible alongside sentiment)
- Agency-grade multi-brand architecture at mid-market price

**Best-fit buyer:** PR and communications teams in brands with significant regional/South India presence; digital agencies wanting to win vernacular monitoring mandates; brands in telecom, banking, FMCG sectors where YouTube reviews are a meaningful signal.

**Weakest-fit buyer:** Brand teams looking for a single tool replacing their current social listening setup (Twitter/Instagram-heavy).

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
- **YouTube monitoring included** (keyword search + comments)
- 5 dashboard users
- 90-day article history
- Dashboard only (no CSV export)

*Justification:* Undercuts manual clipping services (₹5,000–15,000) while delivering AI-grade analysis, a live dashboard, and YouTube monitoring. Accessible entry point for first-time buyers.

---

#### Tier 2 — News Professional *(₹14,000/month per brand)*
Target: Mid-market brands with pan-India or multi-state presence; PR managers
- 1 brand
- All 6 languages (EN/TA/HI/GU/BN/KN)
- All 43 portals
- **YouTube monitoring included** (search + channel RSS + comments)
- State-level filtering
- 10 dashboard users
- 12-month article history
- CSV export ✅
- Email alerts (3 types) ✅
- Monthly PDF summary report (Wave 4 — not yet available)

*Justification:* Positioned against Konnect/Locobuzz entry tier (₹15,000–20,000/month) but with far superior language depth and YouTube coverage included at no premium. Brands currently paying Meltwater ₹40,000+/month for English-only news will find this compelling.

---

#### Tier 3 — Agency *(₹45,000/month for up to 5 brands)*
Target: Digital agencies managing multiple brand accounts
- Up to 5 brands (= ₹9,000/brand/month — agency margin opportunity vs Tier 2)
- All 6 languages, all 43 portals
- **YouTube monitoring included per brand** (with per-brand channel ID configuration)
- State filtering
- 25 users (agency staff + client read-only logins)
- White-label PDF reports (Wave 4)
- CSV bulk export
- Priority pipeline (brands run before standard tier)
- Dedicated account manager

*Justification:* Agency economics: buy at ₹9,000/brand, resell at ₹15,000–25,000/brand = 67–178% margin. Locobuzz agency plans start at ₹40,000–60,000/month for comparable brand counts with basic YouTube. MediaSense is price-competitive with better vernacular depth and YouTube analytics at all tiers.

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

#### Now — Phase 2.0 complete ✅ (news + YouTube monitoring fully featured)
Export, alerts, self-serve onboarding, RBAC management, and YouTube monitoring are all live. MediaSense is now feature-complete for news + YouTube monitoring. **Move to full pricing.** The Founder Pricing window has passed.

**Current recommended pricing:**

| Tier | Price | Ready to sell? |
|---|---|---|
| News + YouTube Essentials | ₹6,500/month | ✅ Yes — pending billing integration |
| News + YouTube Professional | ₹14,000/month | ✅ Yes — pending billing integration |
| Agency (5 brands, news + YouTube) | ₹45,000/month | ✅ Yes — pending billing integration |

**Only blocker before first invoice:** Razorpay / Stripe billing integration (Wave 4). Can currently be handled manually (bank transfer / invoice) for the first 2–3 customers.

#### After Phase 2.1 (Reddit added)
Add Reddit to existing tiers at no price increase. Update positioning to "news + YouTube + Reddit" — the three free-API social channels. This completes the picture for brand discovery and public opinion tracking.

#### After Phase 3 (Twitter/X, Instagram, Facebook added)
Reprice significantly upward. Add a **Full Social + News** tier at ₹30,000–45,000/month per brand — this directly competes with Locobuzz/Konnect's core offering at a comparable price but with better language depth.

| Tier | Price (post-Twitter/Instagram/Facebook) |
|---|---|
| News + YouTube Professional | ₹16,000/month |
| Full Social + News Standard (1 brand) | ₹35,000/month |
| Full Social + News Pro (6 languages) | ₹50,000/month |
| Agency (5 brands, all channels) | ₹1,40,000/month |

---

## 6. Revenue Projections

### Conservative (news + YouTube, full pricing)

| Customers | Mix | MRR |
|---|---|---|
| 5 News Pro brands | ₹14,000 × 5 | ₹70,000 |
| 2 Agency (5 brands each) | ₹45,000 × 2 | ₹90,000 |
| 5 News Essentials | ₹6,500 × 5 | ₹32,500 |
| **Total MRR** | | **₹1,92,500** |
| **ARR** | | **₹23,10,000** |

### Target for Phase 3 gate (Twitter/X, Instagram) — ₹3L MRR

| Customers | Mix | MRR |
|---|---|---|
| 10 News + YouTube Pro | ₹14,000 × 10 | ₹1,40,000 |
| 4 Agency (5 brands each) | ₹45,000 × 4 | ₹1,80,000 |
| **Total MRR** | | **₹3,20,000** |

*At this MRR, Phase 3 (Twitter/Instagram) development is self-funded.*

### Post-full-social (complete platform)

| Customers | Mix | MRR |
|---|---|---|
| 20 Full Social + News Standard | ₹35,000 × 20 | ₹7,00,000 |
| 10 Agency (5 brands each, all channels) | ₹1,40,000 × 10 | ₹14,00,000 |
| 5 Enterprise | ₹1,75,000 avg × 5 | ₹8,75,000 |
| **Total MRR** | | **₹29,75,000** |
| **ARR** | | **~₹3.57 crore** |

At this scale, MediaSense is genuinely competing with Locobuzz for mid-market agency mandates.

---

## 7. Go-to-Market Priorities Before First Sale

| Blocker | Status | Why it matters |
|---|---|---|
| ~~Self-serve brand + user onboarding~~ | ✅ Done | 4-step wizard, user invite, delete brand, remove user role — all shipped |
| ~~Export (CSV minimum)~~ | ✅ Done | CSV export live; filter-respecting, source_type aware, up to 2,000 rows |
| ~~Alert / email notification~~ | ✅ Done | 3 alert types, 4h rate-limit, Resend email delivery |
| ~~Auth on `/pipeline/trigger`~~ | ✅ Done | Requires master_admin JWT; unauth requests return 403 |
| ~~YouTube monitoring~~ | ✅ Done | Phase 2.0 complete — video search, channel RSS, comments, NLP, dashboard UI |
| **Billing integration (Razorpay / Stripe India)** | ❌ Not started | **Critical — cannot charge customers without payment flow** |
| **Stable Vercel production URL** | ⚠️ In progress | Add canonical domain alias in Vercel dashboard — current URL changes on each deploy |
| Terms of service + privacy policy | ❌ Not started | Required for any paid SaaS |
| Supabase row limits | ⚠️ Monitor | Free tier caps at 50,000 rows; YouTube + news at 12 brands accelerates this |

---

## Update Log

| Date | Update | Features added / changed |
|---|---|---|
| 2026-06-17 | Initial document | News monitoring, 6 languages, 29 portals, 12 brands, RBAC, state filtering, pipeline visibility, DLQ, circuit breaker, rejection learning |
| 2026-06-17 | Wave 3 shipped | CSV export, email alerts (3 types, 4h rate-limit), self-serve brand wizard, user invite/management, India state chip grid; competitor matrix updated |
| 2026-06-17 | Wave 3 admin + map fix | Delete brand, remove user role, language filter expanded, pipeline trigger auth fixed; Go-to-Market blockers updated (4 of 7 resolved) |
| 2026-06-17 | Portal expansion | 29 → 43 portals (+5 EN, +3 HI, +1 TA, +1 BN, +3 KN, +1 GU); competitor matrix portal count updated |
| 2026-06-18 | Phase 2.0 YouTube integration | YouTube video search, channel RSS, comment monitoring, YouTube-aware NLP, quota manager, reach metadata, source_type filter, YouTube KPI card, YouTube badges in Mention Explorer, SourceBreakdown YouTube icons, 4-step brand wizard with YouTube config; competitor matrix YouTube row updated ❌→✅; "Where We Lead" item 7+8 added; social media gap updated (YouTube now live, Twitter/Instagram/Facebook remaining); positioning statement updated; portal count 43 everywhere; pricing updated to "News + YouTube" branding; revenue projections updated to full pricing; Go-to-Market table updated |
| 2026-06-20 | Phase 3 — full dashboard redesign + compact single-screen layout | Compact no-scroll layout (all 9 sections in one viewport); click-to-detail panel for every section and KPI card; dark navy sidebar; 5 KPI cards; sentiment trend area chart (indigo/amber/red fills, F08 annotation); mentions donut; top headlines 3-tab panel; review sites summary; top issues table; sentiment by source table; competitor SoV donut; alerts & risks cards; Mention Explorer light theme + 10/page numbered pagination; "What Is Live" table updated with 4 new UI rows |
| 2026-06-20 | NLP quality improvements (5 priorities) | Confidence gate (confidence < 0.3 excluded from KPI); YouTube low-signal filter (Nice/emoji comments skipped, saves API quota); recency decay in perception score; engagement rate multiplier in Brand Risk Score; Review Sites widget connected to real `/review-summary` API (star rating from sentiment, themes from NLP topics) |
