# Review Sites Integration Plan

**Status:** Planning  
**Date:** 2026-06-22  
**Scope:** MouthShut, JustDial, Trustpilot, Glassdoor, and allied platforms

---

## 1. Context — What Already Exists

The pipeline has one working review-site collector today:

| Component | File | What it does |
|---|---|---|
| Google Reviews collector | `backend/app/ingestion/google_reviews_collector.py` | Fetches up to 5 reviews via Google Places API v1 |
| Config columns | migration 019 | `brand_configs.google_places_id`, `google_reviews_enabled` |
| Source type | `"google_review"` | Stored on every article row |
| Category mapping | `router.py:_SOURCE_TYPE_CATEGORY` | `"google_review" → "google_review"` (own bucket) |
| UI | `ReviewSiteAnalysisPanel.tsx` | Shows count, avg rating, negative %, topics — Google only |
| Star → sentiment | `nlp/code_extractors.py:sentiment_from_star_rating()` | Maps 1–5 stars to score and label |

Every new collector must follow the same contract:
1. `collect_X_for_brand(brand: dict, config: dict) -> list[dict]` returns article dicts
2. Each article has `source_type: "X_review"`, `reach_metadata: {"rating": N}`
3. A `brand_configs` toggle `X_enabled: bool` guards the call in the orchestrator
4. An identifier column `X_slug / X_domain / X_company_id` holds the per-brand handle

---

## 2. Target Sites Overview

| Site | Primary Market | Review Type | Access Method | Reliability | Priority |
|---|---|---|---|---|---|
| **MouthShut** | India | Consumer products & services | Web scraping | Medium | Phase A |
| **JustDial** | India | Local businesses | Web scraping (JS-heavy) | Low–Medium | Phase A |
| **Trustpilot** | Global/India | B2C services, SaaS | Official API (free key) | High | Phase A |
| **Glassdoor** | Global/India | Employer brand | Web scraping (very hard) | Low | Phase C |
| **AmbitionBox** | India | Employer brand | Web scraping | Medium | Phase B |
| **Amazon Reviews** | India/Global | Product brands (FMCG) | Web scraping | Low (bot detect) | Phase B |
| **Flipkart Reviews** | India | Product brands (e-commerce) | Web scraping | Medium | Phase B |
| **IndiaMart** | India | B2B brands | Web scraping | Medium | Phase C |

---

## 3. Access Strategy Per Site

### 3.1 Trustpilot (Phase A — recommended first)

**Why first:** Official REST API available with a free developer key. No scraping. Most reliable source for international/SaaS brands.

- **API base:** `https://api.trustpilot.com/v1`
- **Key:** Free tier from [developer.trustpilot.com](https://developer.trustpilot.com) — no credit card
- **Brand lookup:** `GET /business-units/find?name={domain}&apikey={key}` → returns `businessUnitId`
- **Reviews:** `GET /business-units/{id}/reviews?apikey={key}&perPage=20&orderBy=createdat.desc`
- **Fields available:** `stars` (1–5), `text.review`, `createdAt`, `consumer.displayName`, `isVerified`
- **Rate limit:** 100 requests/minute on free tier
- **Cap per run:** 20 reviews (matching Google Reviews pattern)
- **Config columns needed:**
  - `trustpilot_enabled BOOLEAN DEFAULT FALSE`
  - `trustpilot_domain TEXT` — e.g. `"amul.com"`, resolved to business unit ID on first run
  - `trustpilot_business_unit_id TEXT` — cached after first lookup
- **Source type:** `"trustpilot_review"`
- **Source credibility:** `0.80` (verified purchase flag available)

### 3.2 MouthShut (Phase A — most important for Indian consumer brands)

**Why:** Largest Indian review platform for consumer goods. Amul, Jio, HDFC, Swiggy — all have large review bases. No official API.

- **URL pattern:** `https://www.mouthshut.com/product-reviews/{slug}-reviews-{numeric_id}`
  - Slug example for Amul Milk: `amul-milk-reviews-925925714`
- **Method:** `httpx.get()` + `BeautifulSoup` parsing
- **Parser targets (HTML):**
  - Rating: `div.rating span[itemprop="ratingValue"]` or JSON-LD `aggregateRating`
  - Individual reviews: `div.review-article` blocks — each has `.reviwer-content`, `.ratting-count`, `time[datetime]`
- **Rate limit:** 1 request every 8 seconds; max 10 reviews per run
- **User-Agent:** Rotate from a pool of 4–5 real browser UA strings
- **robots.txt:** Allows `/product-reviews/` paths as of 2025; check on implementation
- **Config columns needed:**
  - `mouthshut_enabled BOOLEAN DEFAULT FALSE`
  - `mouthshut_slug TEXT` — the full slug from the URL (set by admin in Channel Settings)
- **Source type:** `"mouthshut_review"`
- **Source credibility:** `0.65` — Indian consumer perspective, unverified accounts
- **Challenge:** Site structure changes without notice; parser will need maintenance

### 3.3 JustDial (Phase A — important for local/retail brands)

**Why:** Dominant Indian local business directory. Especially important for food, healthcare, retail brands.

- **URL pattern:** `https://www.justdial.com/{city}/{business-name}/{listing-id}`
  - JustDial uses dynamic routing; the listing ID is stable
  - Mobile/WAP URL (lighter): `https://wap.justdial.com/...` — preferred for scraping
- **Method:** httpx on WAP endpoint first; fall back to Playwright if JS rendering required
- **Rate limit:** Highly aggressive — 1 req / 15 seconds minimum; circuit-break on 429
- **Parser targets (WAP HTML):** `.ratingStyle`, `.rating-count`, `.jdrating`, review text in `p.jd_txt`
- **Config columns needed:**
  - `justdial_enabled BOOLEAN DEFAULT FALSE`
  - `justdial_listing_url TEXT` — the full JustDial listing URL (admin sets this)
- **Source type:** `"justdial_review"`
- **Source credibility:** `0.60` — lower reliability, unsigned reviews, business can respond/moderate
- **Challenge:** IP bans common at scale; Cloudflare protection on some pages
- **Mitigation:** Scrape WAP variant; implement exponential backoff; consider rotating Railway IPs via a proxy env var

### 3.4 AmbitionBox (Phase B — Indian employer brand)

**Why:** Indian equivalent of Glassdoor. Relevant for brands where employer reputation affects consumer trust (tech companies, banks, FMCG).

- **URL pattern:** `https://www.ambitionbox.com/reviews/{company-slug}-reviews`
- **Method:** httpx + BeautifulSoup
- **Data:** Overall company rating (1–5), review text, role of reviewer, pros/cons sections
- **Config columns needed:**
  - `ambitionbox_enabled BOOLEAN DEFAULT FALSE`
  - `ambitionbox_slug TEXT`
- **Source type:** `"ambitionbox_review"`
- **Source credibility:** `0.65`
- **Note:** Employer brand, not consumer brand. Label in UI as "Employer Brand" tab.

### 3.5 Amazon Reviews (Phase B — FMCG/product brands)

**Why:** Critical for consumer product brands (Amul, Nestle, P&G). Amazon India has the largest verified-purchase review base.

- **URL pattern:** `https://www.amazon.in/product-reviews/{ASIN}`
- **Method:** httpx with real browser UA; fallback Playwright
- **Data:** `span.a-icon-alt` (star rating), `span.review-text-content`, `span.review-date`, `span.a-profile-name`
- **Config columns needed:**
  - `amazon_enabled BOOLEAN DEFAULT FALSE`
  - `amazon_asin TEXT[]` — brands may have multiple ASINs (array)
- **Source type:** `"amazon_review"`
- **Source credibility:** `0.75` — verified purchase badge elevates trust
- **Challenge:** Amazon has aggressive bot detection; Selenium/Playwright likely required; proxy may be needed
- **Mitigation:** Limit to 5 reviews per ASIN per run; 15s between requests; honour `x-amzn-requestid`

### 3.6 Flipkart Reviews (Phase B — Indian e-commerce)

**Why:** Second-largest Indian e-commerce platform; important for FMCG and consumer electronics brands.

- **URL pattern:** `https://www.flipkart.com/.../{product-id}/product-reviews/`
- **Method:** httpx + BeautifulSoup (Flipkart renders server-side more than Amazon)
- **Data:** `._3LWZlK._1BLPMq span` (star), `._6K-7Co` (review text), `._2NsDsF` (date)
- **Config columns needed:**
  - `flipkart_enabled BOOLEAN DEFAULT FALSE`
  - `flipkart_product_url TEXT[]` — product page URLs (array, up to 3)
- **Source type:** `"flipkart_review"`
- **Source credibility:** `0.72`

### 3.7 Glassdoor (Phase C — deferred)

**Why deferred:** Glassdoor actively blocks scraping (Cloudflare, fingerprinting). Their API was retired in 2020. The reward/risk ratio is low.

- **Alternative path:** Glassdoor offers a "Glassdoor for Employers" data export if the brand is a paying employer account — explore as a manual upload flow rather than automated scraping
- **Source type (reserved):** `"glassdoor_review"`
- **Config columns:** Reserve `glassdoor_enabled`, `glassdoor_company_id` in a future migration

### 3.8 IndiaMart (Phase C — B2B brands)

**Why deferred:** B2B use case; smaller subset of MediaSense client brands.

- **Access:** `https://www.indiamart.com/{company-slug}/profile.html` — scrapeable
- **Source type (reserved):** `"indiamart_review"`

---

## 4. Database Migrations Required

All new columns go onto `brand_configs`. One migration per phase is the pattern.

### Migration 021 — Phase A platforms

```sql
ALTER TABLE brand_configs
  ADD COLUMN IF NOT EXISTS trustpilot_enabled          BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS trustpilot_domain           TEXT,
  ADD COLUMN IF NOT EXISTS trustpilot_business_unit_id TEXT,
  ADD COLUMN IF NOT EXISTS mouthshut_enabled           BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS mouthshut_slug              TEXT,
  ADD COLUMN IF NOT EXISTS justdial_enabled            BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS justdial_listing_url        TEXT;
```

### Migration 022 — Phase B platforms

```sql
ALTER TABLE brand_configs
  ADD COLUMN IF NOT EXISTS ambitionbox_enabled    BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS ambitionbox_slug       TEXT,
  ADD COLUMN IF NOT EXISTS amazon_enabled         BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS amazon_asins           TEXT[]  DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS flipkart_enabled       BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS flipkart_product_urls  TEXT[]  DEFAULT '{}';
```

### Migration 023 — Phase C reserved columns

```sql
ALTER TABLE brand_configs
  ADD COLUMN IF NOT EXISTS glassdoor_enabled     BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS glassdoor_company_id  TEXT,
  ADD COLUMN IF NOT EXISTS indiamart_enabled     BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS indiamart_slug        TEXT;
```

---

## 5. Source Type Taxonomy Changes

### 5.1 Router mapping update

Expand `_SOURCE_TYPE_CATEGORY` and `_SOURCE_CATEGORIES` in `backend/app/dashboard/router.py`:

```python
_SOURCE_TYPE_CATEGORY: dict[str, str] = {
    # ... existing entries ...
    "google_review":      "review_site",   # ← was "google_review" (own bucket)
    "trustpilot_review":  "review_site",
    "mouthshut_review":   "review_site",
    "justdial_review":    "review_site",
    "ambitionbox_review": "review_site",
    "amazon_review":      "review_site",
    "flipkart_review":    "review_site",
    "glassdoor_review":   "review_site",
    "indiamart_review":   "review_site",
}
_SOURCE_CATEGORIES = ("news", "youtube", "blog", "review_site", "reddit_post")
```

**Note:** This change renames the category key from `"google_review"` → `"review_site"`. The frontend `ReviewSiteAnalysisPanel` needs to read `bySourceType.review_site` instead of `bySourceType.google_review`. The granular `source_type` on each article row still identifies the exact platform.

### 5.2 Human review queue

`postgres.py:save_article()` already auto-enqueues for human review when `confidence < 0.5` on crisis/regulatory articles. No change needed — all `review_site` source types flow through the same save_article path.

### 5.3 NLP routing

All review-site articles have star ratings in `reach_metadata.rating`. The existing `sentiment_from_star_rating()` in `code_extractors.py` handles the star → score/label mapping. `analyse_article()` in `router.py` already checks for `has_star = bool(article.get("reach_metadata", {}).get("rating"))` to route to Tier 0 when the word count is low and a star rating exists — no NLP token spend for short reviews.

---

## 6. New Collector File Pattern

Each collector lives at `backend/app/ingestion/{platform}_collector.py` and follows this signature:

```python
def collect_{platform}_for_brand(brand: dict, config: dict) -> list[dict]:
    """
    Returns a list of article dicts (max N reviews).
    Returns [] when:
    - {platform}_enabled is False
    - Identifier (slug/domain) is not set
    - API/site returns error
    """
```

Each article dict must include:

| Field | Value |
|---|---|
| `brand_id` | `brand["id"]` |
| `content_hash` | `sha256(brand_id + author + publish_date)` |
| `story_hash` | `sha256(brand_id + platform + publish_date)` |
| `portal_id` | `"{platform}"` |
| `portal_name` | Display name e.g. `"MouthShut"` |
| `url` | Direct link to the review or listing page |
| `title` | `"{Platform} Review ★★★☆☆"` (stars from rating) |
| `body` | Review text, max 2000 chars |
| `author` | Reviewer display name or `"Anonymous"` |
| `published_at` | ISO 8601 string |
| `language` | `"en"` (or detect via FastText if non-English) |
| `source_type` | `"{platform}_review"` |
| `source_credibility` | Platform-specific constant (see §3) |
| `is_regulatory_source` | `False` |
| `reach_metadata` | `{"rating": N}` where N is 1–5 |

---

## 7. Orchestrator Changes

In `backend/app/pipeline/orchestrator.py`, inside `run_brand_pipeline()`, add a block for each platform following the existing Google Reviews pattern:

```python
if config.get("trustpilot_enabled", False):
    try:
        tp_raw  = collect_trustpilot_for_brand(brand, config)
        tp_new  = filter_new_articles(tp_raw, brand_id)
        tp_new  = [a for a in tp_new if not is_rejected(brand_id, a.get("url",""), a.get("title",""))]
        new_articles.extend(tp_new)
        stats["collected"] += len(tp_raw)
    except Exception as e:
        log.error("Trustpilot collection failed for brand %s: %s", brand_id[:8], e)
        stats["errors"] += 1
```

Cap per platform: 10 reviews/run (same sub-cap principle as YouTube and Reddit).

---

## 8. Frontend Changes

### 8.1 Channel Settings (`ChannelSettings.tsx` or settings page)

Add a new "Review Sites" section with toggles and identifier fields for each platform:

```
Review Sites
┌─────────────────────────────────────────────────────┐
│ ✓ Google Reviews    [Business ID: ChIJ...      ] [x]│
│   Trustpilot        [Domain: amul.com          ] [ ]│
│   MouthShut         [Slug: amul-dairy-reviews-…] [ ]│
│   JustDial          [Listing URL: justdial.com/…] [ ]│
│   AmbitionBox       [Slug:                      ] [ ]│
│   Amazon            [ASINs: B07..., B09...      ] [ ]│
│   Flipkart          [Product URLs: ...          ] [ ]│
└─────────────────────────────────────────────────────┘
```

### 8.2 ReviewSiteAnalysisPanel (`ReviewSiteAnalysisPanel.tsx`)

Upgrade from Google-only to multi-site aggregated view:

- **Top strip:** Total review count + aggregate avg rating across ALL enabled review sites
- **Per-site table:** One row per platform showing count, avg rating, negative%
  - Sort by `count` descending
  - Show platform logo icon or colored dot
- **Source key change:** Read from `bySourceType.review_site` instead of `bySourceType.google_review`

### 8.3 MentionsList (`MentionsList.tsx`)

Already shows `source_type` badge on each card. No change needed — new `source_type` values will render as unknown badges until explicit icon mappings are added. Add mappings:

```typescript
const SOURCE_ICONS: Record<string, string> = {
  // ... existing ...
  trustpilot_review: "⭐",
  mouthshut_review:  "🗣",
  justdial_review:   "📍",
  ambitionbox_review:"💼",
  amazon_review:     "📦",
  flipkart_review:   "🛒",
  glassdoor_review:  "🏢",
};
```

---

## 9. Dependencies to Add

```
# requirements.txt additions
beautifulsoup4>=4.12
lxml>=5.0          # faster BS4 parser
```

Trustpilot uses the existing `httpx` (already in requirements). No additional deps for the API path.

For JustDial and Glassdoor if Playwright is needed:
```
playwright>=1.44
```
Note: Playwright adds ~60 MB to the Docker image. Only add it when JustDial Phase A scraping fails with httpx alone.

---

## 10. Implementation Phases

### Phase A — 2 weeks target

**Goal:** 3 collectors live, review sites unified under `review_site` category

| Task | Owner | Est |
|---|---|---|
| Migration 021 (Trustpilot + MouthShut + JustDial columns) | backend | 0.5d |
| `trustpilot_collector.py` (API-based) + tests | backend | 1d |
| `mouthshut_collector.py` (scraping) + tests with fixtures | backend | 2d |
| `justdial_collector.py` (WAP scraping attempt) + tests | backend | 2d |
| Orchestrator: 3 new collection blocks + sub-caps | backend | 0.5d |
| `_SOURCE_TYPE_CATEGORY` rename + `bySourceType.review_site` | backend | 0.5d |
| `ReviewSiteAnalysisPanel` multi-site upgrade | frontend | 1.5d |
| Channel Settings: Review Sites section | frontend | 1d |
| MentionsList: new source_type icons | frontend | 0.5d |

### Phase B — 3 weeks after Phase A

**Goal:** Amazon and Flipkart coverage for FMCG/product brands; AmbitionBox for employer brand

| Task | Est |
|---|---|
| Migration 022 (Amazon + Flipkart + AmbitionBox) | 0.5d |
| `ambitionbox_collector.py` + tests | 1.5d |
| `amazon_collector.py` (ASIN-based, Playwright) + tests | 3d |
| `flipkart_collector.py` + tests | 2d |
| Orchestrator: 3 new blocks | 0.5d |
| UI: Amazon/Flipkart in ReviewSiteAnalysisPanel; star distribution chart upgrade | 1.5d |

### Phase C — Deferred / manual path

**Goal:** Glassdoor (manual export) + IndiaMart (B2B)

- Glassdoor: Build a CSV upload endpoint so brands can manually export and upload Glassdoor data — avoids scraping entirely
- IndiaMart: Evaluate demand; if 3+ clients request it, implement scraping
- Migration 023 reserved columns added even if collectors not yet built

---

## 11. Testing Strategy

Each collector gets a test file at `backend/tests/test_{platform}_collector.py`:

- Save sample HTML/JSON responses to `backend/tests/fixtures/{platform}/`
- Mock `httpx.get()` / `httpx.post()` via `unittest.mock.patch` to return fixture content
- Assert: correct `source_type`, `reach_metadata.rating`, `content_hash` stability, empty list on error
- Test `collect_X_for_brand()` with `X_enabled: False` → returns `[]` without HTTP call

Follow the pattern established in `backend/tests/test_google_reviews.py`.

---

## 12. Legal & Ethical Notes

| Platform | ToS on scraping | Recommendation |
|---|---|---|
| Trustpilot | API use preferred; ToS allows crawling for research | Use API — no scraping |
| MouthShut | Prohibits commercial automated access | Scrape conservatively; review with legal before prod |
| JustDial | Prohibits automated scraping | Same as MouthShut; prefer data partnership |
| Glassdoor | Prohibits scraping (enforced) | Manual export path only |
| AmbitionBox | ToS silent on scraping; robots.txt permissive | Scrape conservatively |
| Amazon | Prohibits scraping per ToS | Rate-limit heavily; acceptable for internal analytics |
| Flipkart | ToS prohibits scraping | Same as Amazon |

**Practical stance:** All scraping is done for a brand about its own reviews, at very low volume (≤10 reviews/brand/run). This is a common and generally tolerated pattern for reputation monitoring SaaS tools. However, for enterprise clients, surface Trustpilot API as the "clean" alternative and document that MouthShut/JustDial/Amazon scrapers carry ToS caveats.

---

## 13. Open Questions Before Implementation

1. **`google_review` → `review_site` rename:** The existing `bySourceType.google_review` key in the dashboard API is used by `ReviewSiteAnalysisPanel`. Renaming it to `review_site` is a breaking change — need a single atomic commit that updates both backend and frontend together, or add a transitional alias.

2. **Multi-ASIN Amazon:** If a brand has 20 ASINs, do we scrape all of them every run? Recommend a max of 3 ASINs per run with rotation — need brand-level config to specify priority ASINs.

3. **Language detection for regional reviews:** MouthShut and JustDial have Hindi, Tamil, and other language reviews. FastText already handles this — no change needed but worth confirming with real data.

4. **JustDial Playwright dependency:** Does Railway's Docker image include Playwright browsers? Check current `Dockerfile` — if not, adding it adds deploy complexity. Start with httpx-only and fall back to "not supported" for Playwright-only pages.

5. **Review deduplication:** `content_hash = sha256(brand_id + author + publish_date)` — confirm this is stable across runs when the same review is scraped twice. For Trustpilot API, use the `id` field from the API response instead.

6. **MouthShut numeric ID discovery:** The URL slug includes a numeric suffix (`-925925714`) that varies per product. Need a two-step flow: admin provides partial brand name → system searches MouthShut and lists candidates → admin picks one → slug saved. Or: admin provides the full URL.
