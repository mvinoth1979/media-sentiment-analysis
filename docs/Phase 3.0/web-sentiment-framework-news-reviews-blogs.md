# Brand Sentiment Monitoring Framework — News, RSS, Reviews & Beyond

A companion framework to the YouTube Sentiment Monitoring Framework. Where YouTube requires watch-time and comment-thread logic, text-based web monitoring — news portals, RSS feeds, review sites, blogs, and aggregator portals — has its own distinct data structures, source authority dynamics, and signal-to-noise challenges. This document addresses each channel with the same operational discipline: every metric is defined, every alert has a threshold, and every limitation is disclosed.

---

## Part 1: News Portals & RSS Feeds

### Why These Require a Separate Treatment

News mentions are structurally different from social commentary. A single article in a high-authority portal (e.g., The Hindu BusinessLine, Mint, Economic Times) has outsized reach, long shelf life via Google indexing, and journalist credibility that amplifies the sentiment far beyond its raw traffic. A neutral headline can carry a negative connotation. A factually accurate article can still be reputationally damaging by emphasis or placement.

---

### 1.1 Source Discovery & Ingestion

**RSS Feeds — Primary Method**

Most news portals publish RSS feeds. These are structured XML files updated in near-real time and are the most reliable, low-latency method for monitoring.

**How to build your feed list:**

| Source Type | Method |
|---|---|
| National English news portals | Subscribe to their RSS (e.g., Hindu, ET, Mint, NDTV) |
| Regional language portals | Identify RSS feeds for Tamil, Kannada, Telugu, Malayalam, Hindi portals separately |
| Government/PSU beat publications | Subscribe to sector-specific feeds (energy, insurance, banking, etc.) |
| Wire services | PTI, ANI, IANS syndicate broadly — one article becomes dozens |
| Industry newsletters | Many publish RSS; subscribe to sector newsletters in BFSI, energy, public sector |

**Tools that aggregate RSS at scale:**

- Google News RSS (search-based, generates a feed for any keyword combination) — good for coverage, not for archiving
- Feedly / Inoreader — managed aggregators with keyword filtering
- Custom RSS parser (Python `feedparser` library) — for agency-owned pipelines that need structured output into a database

**Important:** RSS gives you headlines and summaries, often not full article text. For full-text sentiment analysis, you need to fetch and parse the article URL — which may be blocked by paywalls. Define upfront which sources require paid API access (e.g., Factiva, Meltwater) versus those that are open.

---

### 1.2 Detection Beyond RSS

RSS alone will miss mentions. Complement with:

**Google News Alerts** — set up keyword alerts for:
- Brand name (all spellings and abbreviations)
- Product/service names
- Executive names
- Common misspellings
- Brand name + sector keywords (e.g., "CIPET + plastics", "IOCL + fuel")
- Campaign names and hashtags where the news could reference them

**Web Crawling / Scraping** — for portals that don't publish RSS, a scheduled crawler (weekly or daily) can pull new articles. This requires:
- robots.txt compliance check per domain
- Rate limiting to avoid IP blocks
- HTML parser (BeautifulSoup, Scrapy) to extract article body, headline, author, date, and publication

**API-Based News Aggregators:**
- NewsAPI, GDELT Project, MediaStack — provide structured access to global news with keyword filtering. GDELT is particularly useful for government/PSU clients as it indexes a large volume of South Asian and regional publications.

---

### 1.3 Sentiment Analysis Specific to News

News text is qualitatively different from social comments — it is more formal, uses passive voice, may not express sentiment explicitly, and often quotes multiple stakeholders with opposing views within one article. Standard social-media sentiment classifiers underperform on news text.

**Required adaptations:**

**Headline vs. Body Sentiment — Analyzed Separately**

A headline like "IOCL profits fall for third consecutive quarter" and a body that contextualizes it with structural reasons carry different sentiment signals. Always analyze both, and where they diverge, flag the divergence as the lead insight.

**Quote Extraction and Attribution**

Articles quote industry analysts, regulators, consumers, competitors, and the brand's own spokespeople. Each quote may carry a different sentiment. A named-entity recognition (NER) model should identify who said what before sentiment scoring is applied — otherwise a competitor's negative quote gets attributed to the brand.

**Tone vs. Factual Negativity**

A factually negative event (product recall, regulatory action) may be reported in a neutral, factual tone. A mildly negative event may be written with editorial slant. Track both:
- Factual negativity (what happened)
- Editorial tone (how it was framed)

**Suggested Sentiment Scale for News:**

| Score | Label | Description |
|---|---|---|
| +2 | Strongly Positive | Brand praised, award, milestone, endorsement |
| +1 | Mildly Positive | Positive reference, favorable context |
| 0 | Neutral | Factual mention, no editorial tone |
| −1 | Mildly Negative | Critical framing, concern raised |
| −2 | Strongly Negative | Allegation, crisis reporting, regulatory action |

Confidence threshold applies here too: any −2 score must pass human review before it enters a leadership report.

---

### 1.4 Authority Weighting for News Sources

Not all news is equal. A mention in a wire service that gets syndicated to 40 portals is not 40 independent mentions — it is one story with 40 surfaces. And a mention in a Tier 1 national outlet carries a different reputational weight than one in a hyperlocal portal.

**Build a Source Authority Matrix:**

| Tier | Description | Examples | Weight |
|---|---|---|---|
| Tier 1 | National print/digital, major broadcast | Economic Times, Mint, The Hindu, NDTV, Hindustan Times | 3× |
| Tier 2 | Regional English, major vernacular portals | Deccan Herald, The New Indian Express, Dinamalar | 2× |
| Tier 3 | Trade and industry publications | Petroleum Outlook, Banking Frontiers, Insurance Times | 2× (sector-specific) |
| Tier 4 | Hyperlocal, aggregator, blog-style news sites | Local city portals, republished content | 1× |
| Wire | PTI, ANI, IANS syndicated stories | Track as one story, not by surface count | 1× (counted once) |

**Syndication Deduplication:** Wire service articles that are republished verbatim across portals should be counted once in sentiment scoring. Track syndication reach separately as a distribution metric, not as independent sentiment data points.

---

### 1.5 Metrics to Capture Per News Mention

| Parameter | Notes |
|---|---|
| Publication name | With tier classification |
| Article URL | Permanent link, not aggregator redirect |
| Headline | Exact |
| Headline sentiment | −2 to +2 |
| Body sentiment | −2 to +2 |
| Editorial tone | Neutral / Positive Frame / Negative Frame |
| Quotes extracted | With attribution |
| Named entities | Brand, executives, competitors mentioned |
| Issue category | See below |
| Authority weight | Tier 1–4 |
| Estimated reach | Page views if available; otherwise domain authority as proxy |
| Syndication count | How many portals republished the same article |
| Publication date | |
| Author/journalist name | Track beat journalists who cover your client repeatedly |

---

### 1.6 Issue Classification for News

Adapted from the YouTube framework, with news-specific categories added:

| Category | Example |
|---|---|
| Financial Performance | Profit/loss, market share, revenue |
| Regulatory & Compliance | SEBI action, ministry directive, audit finding |
| Product / Service Quality | Launch, recall, performance review |
| Leadership & Governance | Executive appointments, board decisions |
| Crisis & Controversy | Allegation, scam, safety incident |
| Awards & Recognition | Rankings, certifications, milestones |
| CSR & Sustainability | Environmental, community, ESG coverage |
| Policy & Government Relations | Budget mentions, scheme references |
| Competitive Landscape | Comparisons with competitors |
| Market Opportunity | Sector growth, favorable macro coverage |

---

### 1.7 Virality & Escalation Detection in News

**Syndication spike:** If a single article is republished in more than 10 portals within 24 hours, treat as a reputational event regardless of sentiment — positive or negative.

**Journalist-beat tracking:** If a journalist who covers your client's sector publishes two or more critical pieces in 30 days, flag as an Emerging Narrative Risk — not just individual article sentiment.

**Government/regulatory-source articles:** Any article citing a government report, parliamentary mention, or regulatory body as a source should automatically be escalated for human review regardless of its sentiment score, given the formal weight of these sources.

---

## Part 2: Review Sites, Blogs & Web Portals

### 2.1 Why This Channel is Different

Reviews and blog content sit between social media (real-time, high volume) and news (authoritative, low volume). A single detailed negative review on a high-traffic review site can influence purchase decisions for months or years — Google indexes these pages with high domain authority, meaning they surface when someone searches the brand name. Unlike a negative tweet, a 600-word blog post about a bad experience doesn't decay quickly.

---

### 2.2 Source Typology and Discovery Method

**Category 1: Structured Review Platforms**

These have defined review schemas (star rating + text), which makes extraction more structured.

| Platform | Relevance for PSU/BFSI/Government Clients |
|---|---|
| Google Business Profile Reviews | High — most consumer-visible, indexed immediately |
| Trustpilot | Relevant for BFSI clients (banks, insurance) |
| MouthShut | Significant for Indian brands — legacy platform with active users |
| JustDial | Relevant for service-based brands with local presence |
| AmbitionBox / Glassdoor | Employer brand sentiment — relevant for PSU recruitment narratives |
| App Store / Play Store | For brands with a mobile app (banking apps, portal apps) |
| YouTube (covered separately) | — |

**How to monitor:**
- Most platforms have public-facing review pages that can be scraped or monitored via API (Google My Business API, Trustpilot API)
- Set up monitoring at the individual branch/location level for PSU clients with multiple offices (banks, LIC branches, petrol stations)

**Category 2: Editorial Review / Comparison Sites**

These are written by editors or community contributors, not customers. Carry higher Google authority.

| Platform | Relevance |
|---|---|
| BankBazaar, PolicyBazaar | Insurance, banking products — comparison with competitors built in |
| Digit Insurance, Value Research | BFSI-sector product reviews |
| 91mobiles, GSMArena | For technology-adjacent products |
| Sector-specific comparison portals | Varies by client — identify the 3–5 dominant comparison sites per sector |

**How to monitor:** These don't update in real time. Schedule a monthly crawl of your brand's dedicated page on each relevant comparison site. Track rating changes, editorial revisions, and user-comment sentiment.

**Category 3: Independent Blogs & Longform Content**

These are the hardest to monitor systematically because there is no centralized registry.

**Detection methods:**

| Method | How |
|---|---|
| Google Alerts | Set alerts for brand name + "review", "experience", "feedback", "complaint" |
| Google Search Operators | `"brand name" site:blogspot.com OR site:wordpress.com OR site:medium.com` |
| Ahrefs / Semrush Backlink Monitor | Tracks new domains linking to your brand's website — a new backlink from a blog usually means a mention |
| Social sharing signals | Blog posts shared on Twitter/X, LinkedIn, or Reddit often surface through social monitoring before Google indexes them |
| Reddit and Quora | Not blogs but function similarly — high-authority, long-shelf-life text content that ranks in search |

**Approach for PSU/government clients:** Prioritize monitoring by search rank. Run a weekly search for "brand name + review / complaint / experience" and track which pages appear in the top 20 results. These are what a member of the public, journalist, or regulator will actually see — they matter more than a blog post buried on page 8.

---

### 2.3 Sentiment Analysis Specific to Reviews

**Star Rating vs. Text Sentiment — These Often Diverge**

A 3-star review with text "would have been good but the branch manager was unhelpful and the process took weeks" is functionally a negative review with neutral numeric packaging. Always run text sentiment independently of the star rating and flag divergences.

**Review Freshness and Weight**

Reviews decay in reputational impact over time — but not in search visibility. A 2019 negative review on MouthShut may still appear on page 1 of a Google search. Track:
- Review date
- Whether the brand has responded (response = mitigation signal)
- Whether newer reviews have shifted the overall rating

**Verified vs. Unverified Reviews**

Flag whether a review platform verifies purchasers/customers. Unverified platforms are more susceptible to competitor-planted reviews and coordinated reputation attacks — a cluster of similar negative reviews in a short window is a signal for investigation, not just reporting.

---

### 2.4 Metrics to Capture Per Review/Blog Mention

| Parameter | Notes |
|---|---|
| Source platform | With category (structured review / editorial / blog) |
| URL | Permanent link |
| Publication date | |
| Author type | Verified customer / Editor / Anonymous / Blogger |
| Star rating (if applicable) | |
| Text sentiment | −2 to +2 |
| Star vs. text divergence | Flag if rating and text conflict |
| Issue category | Same taxonomy as news section |
| Google search rank | Where does this page appear for brand name queries? |
| Brand response status | Has the brand replied? Date of response? |
| Estimated reach | Monthly traffic of the platform (SimilarWeb/Semrush estimate) |
| Flagged for investigation | Suspicious clustering, possible coordinated attack |

---

### 2.5 Issue Classification for Reviews & Blogs

Reviews tend to surface operational issues that news misses. Expand the taxonomy:

| Category | Example |
|---|---|
| Product / Policy Quality | Insurance claim denied, loan terms unclear |
| Branch / Location Experience | Rude staff, long queues, unhygienic premises |
| Digital Experience | App crashes, portal login issues, poor UX |
| Turnaround Time | Slow claim processing, delayed service |
| Customer Service | No response, call center issues |
| Documentation / Process | Excessive paperwork, unclear requirements |
| Pricing & Value | Fees, charges, premium amounts |
| Trust & Transparency | Hidden charges, misleading communication |
| Positive Advocacy | Unprompted praise, recommendation |
| Comparison / Switching | "Switched from X to Y because..." |

---

### 2.6 Emerging Issue Detection for Reviews

**Clustering trigger:** If 3 or more reviews on the same platform cite the same issue within a 14-day window, flag as an Emerging Operational Issue — regardless of overall rating impact. This is where the framework moves from reputation reporting to operational intelligence.

**Rating trend trigger:** If the average rating on any platform drops by 0.3 points or more over 30 days, flag as a Reputation Risk.

**Unanswered review trigger:** For PSU/government clients, unanswered negative reviews on Google Business Profile older than 7 days should be flagged in the monthly report with a recommendation to respond — Google's algorithm and public perception both factor in response rate.

---

## Part 3: Unified Web Listening Architecture

Bringing news, RSS, reviews, and blogs into a single monitoring system requires a layered architecture. The pillars below complement the four YouTube pillars from the earlier framework.

---

**Pillar 5: News & RSS Monitoring**

Captures: National and regional news portals, wire services, trade publications, Google News alerts.

Reports: Tier-weighted mention count, headline vs. body sentiment, issue classification, syndication reach, journalist tracking, regulatory source flags.

---

**Pillar 6: Review Platform Monitoring**

Captures: Google Business, Trustpilot, MouthShut, JustDial, App Store/Play Store, sector-specific comparison sites.

Reports: Platform-level rating trends, text vs. star divergence, issue clustering, response rate, verified vs. unverified flag, Google search rank of each review page.

---

**Pillar 7: Blog & Long-Form Web Monitoring**

Captures: Independent blogs, Medium, Reddit, Quora, WordPress/Blogspot mentions detected via Google Alerts, backlink monitoring, and search rank tracking.

Reports: New brand mentions by domain authority, sentiment score, issue category, Google search visibility rank, social share signals.

---

**Pillar 8: Cross-Channel Risk & Opportunity Dashboard**

*Risks:*
- News articles with −2 sentiment from Tier 1/2 sources
- Regulatory-source news articles (any sentiment — human review required)
- Syndication spikes (10+ portals in 24 hours)
- Review clustering (same issue, 3+ reviews, 14 days)
- Rating drops (0.3+ points in 30 days)
- High-ranking negative search results for brand name

*Opportunities:*
- Positive news from Tier 1/2 sources — candidates for earned media amplification
- Positive reviews on high-traffic platforms — candidates for testimonial use (with permission)
- Blog posts from credible authors with high domain authority — candidate for brand partnership or PR engagement

---

## Part 4: Regional Language Coverage — Mandatory for This Scope

Both news portals and review sites see substantial regional-language content in the Indian context, particularly for government/PSU clients whose audiences span Tamil Nadu, Karnataka, Kerala, Andhra Pradesh, Bengal, and Hindi-belt states.

**What this requires:**
- A separate source list for major regional-language portals (Dinamalar, Udayavani, Mathrubhumi, Eenadu, Dainik Bhaskar, etc.) with their RSS feeds tracked independently
- Sentiment classifiers validated for each language — do not assume English-model accuracy transfers to Tamil or Kannada text, especially for code-mixed content (Tanglish, Kanglish)
- Regional-language Google Alerts set in the native script, not just transliteration
- Any monthly report should disclose which languages were monitored and the confidence level of sentiment classification per language

---

## Part 5: Audit Trail & Data Provenance

Same requirement as the YouTube framework — applicable here with additional nuance:

- For news articles: retain the article URL, headline, extraction date, full text (or excerpt if paywalled), sentiment score, confidence level, and who reviewed it
- For reviews: retain URL, date of review, date of monitoring extraction, rating, text, sentiment classification
- For blogs: retain URL, date published, domain authority at time of monitoring, and Google search rank position

For a PSU/government client, any mention that triggers a "Risk Alert" must have a complete evidence trail that can be produced on request — both for internal escalation and potential regulatory or audit purposes.

---

## Monthly Report Structure — Web Listening Edition

1. Executive Summary
2. Mention Volume Overview (by channel — news / reviews / blogs)
3. Sentiment Overview (% Positive, Neutral, Negative — by channel and in aggregate)
4. Top Positive Mentions (with source authority and reach)
5. Top Negative Mentions (with source authority and reach)
6. Emerging Issue Clusters (operational intelligence, not just reputation)
7. Journalist & Author Tracking (beat journalists, influential bloggers)
8. Review Platform Ratings Dashboard (trend over 30/90 days per platform)
9. High-Visibility Search Results Audit (top 20 Google results for brand name — sentiment map)
10. Competitor Benchmark (sentiment comparison across channels where data is available)
11. Regional Language Coverage Report
12. Reputation Risk Alerts (human-confirmed, with evidence trail)
13. Recommended Actions & Response Priorities
14. Data Sources & Limitations (channels monitored, languages covered, paywall gaps, confidence levels)

---

## Key Principle — This Framework as a System, Not a Report

Across YouTube, news, RSS, reviews, and blogs, the output should not be a collection of sentiment percentages — it should be a ranked, evidence-backed picture of where the brand stands, what is changing, what needs a response, and what represents an opportunity. Every number in the report should be traceable to a defined source, a defined method, and — where it carries operational consequence — a human reviewer's sign-off.
