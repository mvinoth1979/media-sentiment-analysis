# YouTube Sentiment Monitoring Framework — Unified Enterprise Version

A three-pronged sentiment framework (owned, earned, public conversation) is a solid starting point, but for media intelligence and reputation management — especially for PSU/government/BFSI clients — it needs more rigor to avoid biased or incomplete reporting. This document integrates the original framework with the fixes needed to make it operationally trustworthy, not just conceptually complete.

---

## Foundation: The Three Original Pillars

1. **Owned Media Sentiment** — Brand's own YouTube channel
2. **Earned Media Sentiment** — Third-party videos discussing the brand
3. **Public Conversation Sentiment** — Brand mentions across the YouTube ecosystem

This aligns broadly with how professional social listening platforms classify conversations. Everything below builds on top of this foundation.

---

## 1. Influence Score — Reach-Weighted Sentiment

**Problem it solves:** Treating every comment equally is a classic vanity-metrics trap. A video with 5 negative comments and 500 views is not equivalent to one with 20 negative comments and 1.5 million views — the second has far greater reputational impact.

**For each video, track:**
- Views
- Likes
- Shares
- Subscriber count of creator
- Engagement rate

**Brand Risk Score — defined, not hand-wavy:**

The original formula — *Sentiment × Reach × Engagement* — is directionally correct but unusable without defined scales. Views follow a power-law distribution, so raw multiplication lets one viral video swamp every other signal. The formula needs:

- **Sentiment** normalized to a fixed range (e.g., −1 to +1)
- **Reach** log-normalized (e.g., `log10(views + 1)` scaled to 0–1) so virality doesn't mathematically erase everything else
- **Engagement rate** as a 0–1 multiplier (likes + comments + shares ÷ views)
- A **decay function** so a 6-month-old spike doesn't carry the same weight as one from yesterday

> Brand Risk Score = Sentiment(−1 to +1) × log-normalized Reach(0–1) × Engagement(0–1) × Recency Decay

This score must be reproducible — any PSU/government reviewer should be able to ask "how was this number derived?" and get a clear answer.

---

## 2. Issue Classification — With a Confidence Gate

**Problem it solves:** Labeling comments Positive/Negative/Neutral tells management *how many* people are unhappy, not *what* they're unhappy about — which is the question that's actually actionable.

**Categories:**

| Category | Example |
|---|---|
| Product Quality | Product failed |
| Customer Service | No response |
| Pricing | Too expensive |
| Delivery | Delay |
| Trust/Reputation | Fake claims |
| Sustainability | Environmental concern |
| Brand Love | Positive advocacy |
| Recommendation | User referrals |

**Built-in safeguard:** Categories like "Trust/Reputation" and any "Allegation" tag are the most prone to misclassification — sarcasm, a comment quoting someone else's complaint, or a rhetorical question ("is this a fake review?") will fool a keyword or LLM classifier. Because a misclassified allegation escalating into a public "Crisis Alert" is a bigger operational risk than quietly missing a real one:

- Every classification carries a **confidence score**
- Anything below threshold routes to **human review** before it can populate a public-facing or leadership-facing report
- Only human-confirmed items can be labeled a "Risk Alert"

---

## 3. Creator Sentiment vs. Audience Sentiment — Reported Separately

**Problem it solves:** Earned media has two distinct audiences whose sentiment can diverge sharply. Example: a tech reviewer posts "This is the best phone of 2026," but the comments say "Paid review." Creator = Positive, Audience = Negative — collapsing these into one number hides the real signal.

**Recommended structure, per third-party video:**

| Parameter |
|---|
| Creator Sentiment |
| Audience Sentiment |
| Reach |
| Key Topics |
| Risk Level |

---

## 4. Virality Detection — With Defined Thresholds

**Problem it solves:** One viral negative video can outweigh hundreds of positive comments, so emerging spikes need to be caught early.

**Track:**
- Sudden increase in views
- Sudden spike in comments
- Sudden increase in negative sentiment

**Made operational:** "Sudden" must be a defined, not subjective, threshold — otherwise it's left to whoever happens to be looking at the dashboard that day. Use a rolling baseline, e.g.:

- **Trigger:** Any video exceeding **3× its 7-day rolling average** in views, comments, or negative-sentiment volume within a 24-hour window

**Flag levels:**
- Emerging Issue (1 metric triggered)
- Reputation Risk (2 metrics triggered)
- Crisis Alert (all 3 metrics triggered **and** human-confirmed per the confidence gate in Section 2)

---

## 5. Comment Quality Filtering

**Problem it solves:** Monotonous, low-information comments dilute signal quality.

**Ignore:** Nice / Good / Super / 👍 / ❤️

**Consider** comments containing: Complaint, Recommendation, Experience, Question, Comparison, Allegation (subject to the confidence gate above)

---

## 6. Competitor Benchmarking — With an Explicit Scope Caveat

**Problem it solves:** Sentiment without context is uninterpretable. "Positive 58%, Negative 18%" means nothing on its own.

| Brand | Positive | Negative |
|---|---|---|
| Brand A | 58% | 18% |
| Competitor 1 | 72% | 10% |
| Competitor 2 | 61% | 15% |

**Caveat that must travel with this table:** This benchmark reflects **YouTube conversation only**. For PSU/government/BFSI brands, a substantial share of relevant public conversation happens on Twitter/X, Reddit, and news-site comment sections — channels this framework does not capture. Any report using this table should state this limitation explicitly rather than implying it represents "overall brand sentiment."

---

## 7. Influencer/Creator Classification

**Problem it solves:** Not every creator carries equal weight — a negative comment from an industry expert matters more than one from a random user.

**Classify by type:** Journalist, Reviewer, Influencer, Customer, Industry Expert, Activist, Competitor Affiliate

This classification should feed directly into the Brand Risk Score as a weighting factor (Section 1) rather than sitting as a standalone label.

---

## 8. Brand Mention Detection — Beyond Hashtags

**Problem it solves:** Many brand conversations carry no hashtag at all. Example: a video titled "Why I switched from Apple to Samsung" generates a huge brand conversation with zero hashtags.

**Detection must search by:**
- Brand name
- Product names
- Common abbreviations
- Campaign hashtags
- Executive names
- Misspellings

---

## 9. Regional Language Coverage *(new — addresses a gap in the original framework)*

**Problem it solves:** For a government/PSU client with a multilingual audience base, sentiment classifiers trained primarily on English degrade significantly on code-mixed regional comments (e.g., Tanglish, Hinglish, and similar blends in Kannada, Telugu, Malayalam, Bengali).

**Requirements:**
- Sentiment and issue classification must be validated separately for each regional language/dialect in scope, not assumed to inherit English-model accuracy
- Any report should disclose which languages were covered and the relative confidence in each, rather than presenting a single blended accuracy figure

---

## 10. Audit Trail & Data Provenance *(new — addresses a gap in the original framework)*

**Problem it solves:** If a "Risk Alert" or classification is ever challenged internally — which is likely in a PSU/government context — there must be a clear record of how the conclusion was reached.

**Every flagged item should retain:**
- Source comment/video, with timestamp
- Classification assigned and confidence score
- Whether it passed through human review, and by whom
- Version of the model/ruleset used

---

## Unified Enterprise Framework — Four Pillars

**Pillar 1: Owned Channel Sentiment**
Brand's official YouTube handle. Capture: video title, URL, positive/negative comments, topic classification, sentiment score.

**Pillar 2: Earned Media Analysis**
Videos uploaded by others mentioning the brand. Capture: video title, URL, creator name, **creator sentiment**, **audience sentiment** (separately), reach score, key issues, creator classification (Section 7).

**Pillar 3: Community Conversation Analysis**
Brand mentions across YouTube, using the expanded detection methods in Section 8. Capture: brand mentions, product mentions, hashtag mentions, executive mentions, comment sentiment (with confidence scores), emerging topics, **language/dialect tag**.

**Pillar 4: Reputation Risk & Opportunity Dashboard**

*Risks (each requiring a Brand Risk Score and, where applicable, human-confirmed status):*
- Negative sentiment spikes (Section 4 thresholds)
- Viral criticism
- Product complaints
- Service complaints

*Opportunities:*
- Brand advocates
- Positive reviews
- Influencer endorsements
- Product recommendations

---

## Monthly Report Structure for CIPET/PSU/Government Clients

1. Executive Summary
2. Sentiment Overview (% Positive, Neutral, Negative — with regional-language breakdown where relevant)
3. Top Positive Conversations
4. Top Negative Conversations
5. Emerging Themes
6. Influential Videos (Brand Risk Score-ranked)
7. Creator Analysis
8. Audience Analysis
9. Competitor Benchmark *(with YouTube-only scope caveat)*
10. Reputation Risk Alerts *(human-confirmed only)*
11. Recommendations & Action Points
12. **Data Sources & Limitations** *(new — methodology, languages covered, confidence levels, channels excluded)*

This structure moves the framework from a sentiment-counting exercise to a decision-support system — one where every number on the dashboard can be traced back to a defined method, and every alert has been through a confidence check before it reaches leadership.
