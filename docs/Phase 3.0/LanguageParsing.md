# Regional Language Relevance Filtering — Problem Analysis & Remediation Plan

## Problem Statement

Regional language portals (Tamil, Hindi, Kannada, Bengali, Gujarati) are ingesting general-purpose news — sports results, political coverage, cinema gossip, cricket scores — that has zero relevance to the monitored brands. This is being discovered manually by reviewing and deleting Tamil mentions in the dashboard. The volume is described as "considerable and alarming."

---

## Root Cause Analysis

### Why this happens: `skip_keyword_filter: True`

English portals pass through `keyword_matches()` — a regex word-boundary check that only accepts articles containing at least one brand keyword. All 38 Indian language portals bypass this entirely:

```
English portal:  collect → keyword_matches("Ashok Leyland", title+body) → pass/reject
Tamil portal:    collect → skip_keyword_filter=True → ALWAYS PASS → NLP
Hindi portal:    collect → skip_keyword_filter=True → ALWAYS PASS → NLP
(same for kn, bn, gu)
```

The original reason in the code comment: *"Tamil script cannot be matched by English regex; relevance is handled by the 50 TA article cap."*

The 20-article-per-language cap is the only filter. With 11 Tamil portals, up to 220 Tamil articles can enter per pipeline run — all from general-purpose portals that publish sports, politics, cinema, crime, weather alongside business news.

### Why the rejection memory isn't working

The rejection/learning store (`article_rejections` table) has only **4 entries** despite the user deleting many articles. The UI deletion flow removes the article from the `articles` table but either doesn't write to `article_rejections` consistently, or the pipeline's `is_rejected()` check isn't catching subsequent re-ingestion of the same content from different portal URLs. Net result: deleted articles return on the next pipeline run.

### Portal-level aggravation

Several portals in the active list are high-volume general news portals with no business/brand focus:

| Portal | Type | Problem |
|---|---|---|
| Polimer News | Tamil TV channel news site | Heavy sports/politics/cinema |
| Puthiyathalaimurai | Tamil TV news | Heavy crime/politics/cinema |
| Sathiyam TV | Tamil TV news | High-volume general feed |
| Sangbad Pratidin | Bengali tabloid-style | Entertainment-heavy |
| Prabhat Khabar | Hindi regional | Heavy local politics |
| TV9 Kannada / Public TV | Kannada TV news | Entertainment + politics |

---

## The Five-Layer Remediation Plan

### Layer 1 — Google News RSS for Regional Languages (Highest Impact)

**What:** Replace or supplement general portal RSS feeds with Google News RSS queries in regional languages. Google News pre-filters for keyword relevance before surfacing articles.

**How it works today (English):**
```
gnews_en_ashok_leyland_trucks → Google News RSS for "Ashok Leyland trucks"
```
Already implemented for English (`get_gnews_portals()`). Extend to Tamil, Hindi, Kannada.

**Google News RSS URL pattern in regional language:**
```
https://news.google.com/rss/search?q=<brand_keywords_in_script>&hl=ta&gl=IN&ceid=IN:ta
```

**Action items:**
- Extend `get_gnews_portals()` to accept a `languages` list and generate per-language gnews feeds
- Add brand keyword transliterations (see Layer 2) to these gnews queries
- These feeds are already keyword-filtered by Google — no `skip_keyword_filter` needed

**Expected outcome:** Replaces 60–70% of irrelevant regional articles with brand-relevant ones.

---

### Layer 2 — Transliterated Keyword Matching

**What:** Build a transliterated variant list for each brand's keywords in each supported script, and apply `keyword_matches()` before ingestion.

**Why this works:** Indian brand names in regional-language news appear in two forms:
1. English-script within Tamil/Hindi text (code-switching): `"Ashok Leyland"` written as-is
2. Transliterated into script: `"அஷோக் லேலேண்ட்"` (Tamil) or `"अशोक लेलैंड"` (Hindi)

Both forms can be matched if we maintain a keyword variant table.

**Implementation:**

Add a `keyword_variants` field to `brand_config` in the database:

```json
{
  "keyword_variants": {
    "ta": ["அஷோக் லேலேண்ட்", "Ashok Leyland", "லேலேண்ட்"],
    "hi": ["अशोक लेलैंड", "Ashok Leyland"],
    "kn": ["ಅಶೋಕ್ ಲೆಲ್ಯಾಂಡ್", "Ashok Leyland"],
    "bn": ["অশোক লেল্যান্ড", "Ashok Leyland"],
    "gu": ["અશોક લેલેન્ડ", "Ashok Leyland"]
  }
}
```

Change `skip_keyword_filter` logic in `rss_collector.py`:

```python
# Instead of blanket skip_keyword_filter=True:
lang = portal.get("language", "en")
lang_keywords = config.get("keyword_variants", {}).get(lang, []) + keywords
if not keyword_matches(combined, lang_keywords):
    continue
```

**Generating transliterations:** Use the Google Transliteration API or AI4Bharat IndicTrans2 (offline). For the initial rollout, Gemini can generate the variants once per brand via a one-time setup call.

**Action items:**
- Add `keyword_variants` column to `brand_config` Supabase table (JSONB)
- Add UI field in Channel Settings page for managing variants per language
- Modify `rss_collector.py` to use language-aware keyword matching
- Generate initial variants for all 14 brands via a one-time Gemini call

**Expected outcome:** Eliminates most remaining irrelevant articles even from general portals.

---

### Layer 3 — RSS Category Blocking

**What:** Many RSS feeds include category/tag metadata. Block known irrelevant categories before any further processing.

**Implementation in `rss_collector.py`:**

```python
_BLOCKED_CATEGORIES = frozenset({
    # Sports
    "cricket", "football", "sports", "ipl", "kabaddi", "chess", "badminton",
    "விளையாட்டு",  # Tamil: sports
    "खेल",          # Hindi: sports
    "ಕ್ರೀಡೆ",       # Kannada: sports
    "খেলাধুলা",     # Bengali: sports
    # Entertainment/Cinema
    "cinema", "kollywood", "bollywood", "film", "movie", "entertainment",
    "சினிமா",       # Tamil: cinema
    "मनोरंजन",      # Hindi: entertainment
    "ಚಲನಚಿತ್ರ",    # Kannada: cinema
    "বিনোদন",       # Bengali: entertainment
    # Astrology/Lifestyle
    "astrology", "horoscope", "lifestyle", "fashion",
    "ஜோதிடம்",     # Tamil: astrology
    "ರಾಶಿಫಲ",      # Kannada: horoscope
})

def _is_blocked_category(entry) -> bool:
    tags = entry.get("tags", []) or []
    for tag in tags:
        term = (tag.get("term") or "").lower()
        if term in _BLOCKED_CATEGORIES:
            return True
    return False
```

Apply in the main collector loop:
```python
if _is_blocked_category(entry):
    continue
```

**Limitation:** Not all RSS feeds include category tags. This catches portals that do (Vikatan, Samayam are well-tagged).

**Expected outcome:** Eliminates 15–25% of irrelevant articles that have proper category tags.

---

### Layer 4 — Post-NLP Brand Entity Gate (Most Precise)

**What:** After NLP runs and extracts entities, check whether any brand keyword appears in the extracted entity list. If not, treat the article as irrelevant — do not save, mark as seen to prevent re-ingestion.

**Why this works:** NLP extracts `entities` = named entities (brands, people, products). If an article about cricket mentions no brand keywords in its entities, it cannot be brand-relevant. This is the most precise filter because it uses the LLM's own understanding of who is mentioned.

**Implementation in `orchestrator.py`:**

```python
def _entity_relevance_check(nlp_dict: dict, keywords: list[str]) -> bool:
    """Return True if at least one brand keyword appears in extracted entities."""
    entities = [e.lower() for e in (nlp_dict.get("entities") or [])]
    for kw in keywords:
        kw_lower = kw.lower()
        if any(kw_lower in e or e in kw_lower for e in entities):
            return True
    return False

# In the article processing loop:
nlp = analyse_article(article)
lang = article.get("language", "en")
if lang != "en" and not _entity_relevance_check(nlp.to_dict(), keywords):
    # Mark seen to prevent re-ingestion; do not save to articles table
    mark_article_seen(article["content_hash"], brand_id)
    stats["filtered_irrelevant"] = stats.get("filtered_irrelevant", 0) + 1
    continue
```

**Trade-off:** This consumes one NLP call before deciding to reject. Cost ~₹0.0001/article. Acceptable given the alternative (manual deletion). Can be short-circuited to Layer 1/2 filtering for portals known to be noisy.

**Expected outcome:** Zero false-negatives — only articles where the brand is actually mentioned by the LLM pass through.

---

### Layer 5 — Rejection Memory Fix (Prevent Re-ingestion)

**What:** Fix the pipeline so user deletions from the UI permanently prevent re-ingestion. Currently only 4 rejections are stored despite many user deletions.

**Root cause:** The UI deletion call removes from `articles` table and writes to `article_rejections`. But `is_rejected()` in the pipeline checks URL similarity and title overlap — if the same article is re-fetched with a slightly different URL or title variant, it passes.

**Fixes needed:**

1. **Also write `content_hash` to `dedupe_hashes`** when a user deletes: ensures the exact same article never re-enters even if URL changes.

2. **Write `story_hash` to a rejections story table**: ensures syndicated versions of the same story are also blocked.

3. **Write rejected portal+title pattern**: if a user deletes 5 articles from `polimer_news` about the same topic, auto-suppress that topic from that portal.

**Implementation:**

```python
# In the article deletion API endpoint:
def delete_article(article_id: str, brand_id: str):
    article = get_article(article_id)
    
    # 1. Remove from articles
    db.table("articles").delete().eq("id", article_id).execute()
    
    # 2. Write to rejection store (existing)
    db.table("article_rejections").upsert({...}).execute()
    
    # 3. Write content_hash to dedupe_hashes (NEW — prevents exact re-ingestion)
    db.table("dedupe_hashes").upsert({
        "content_hash": article["content_hash"],
        "brand_id": brand_id
    }, on_conflict="content_hash,brand_id").execute()
    
    # 4. Write story_hash to block syndicated versions (NEW)
    if article.get("story_hash"):
        db.table("dedupe_hashes").upsert({
            "content_hash": article["story_hash"],  # reuse table for story-level blocks
            "brand_id": brand_id
        }, on_conflict="content_hash,brand_id").execute()
```

**Expected outcome:** User deletions permanently block re-ingestion of the same content and its syndicated copies.

---

## Phased Implementation Order

### Phase A — Immediate (1–2 days)
**Goal:** Stop the bleed. Reduce irrelevant articles by 60%+ without code changes.

1. Remove highest-noise portals from `portals.py` temporarily:
   - `polimer_news`, `puthiyathalaimurai`, `sathiyam_tv` (Tamil TV channels — general news)
   - `sangbad_pratidin` (Bengali tabloid)
   - `tv9_kannada`, `public_tv` (Kannada TV news)
2. Fix rejection memory (Layer 5) — 2-hour fix. Ensures user deletions stick.
3. Reduce per-language cap from 20 to 10 articles while proper filtering is built.

### Phase B — Short-term (3–5 days)
**Goal:** Systematic keyword filtering for all Indian languages.

4. Extend `get_gnews_portals()` for Tamil, Hindi, Kannada, Bengali, Gujarati (Layer 1)
5. Add `keyword_variants` JSONB column to `brand_config`
6. Generate initial keyword variants for all 14 brands via Gemini
7. Implement language-aware keyword matching in `rss_collector.py` (Layer 2)
8. Add RSS category blocking (Layer 3)

### Phase C — Medium-term (1–2 weeks)
**Goal:** Precision gate — only brand-mentioned articles survive.

9. Implement post-NLP entity relevance gate (Layer 4)
10. Add `filtered_irrelevant` counter to pipeline stats for monitoring
11. Add UI field in Channel Settings for managing `keyword_variants` per language
12. Re-evaluate removed portals — re-add with proper filtering in place

---

## Expected Outcome After All Layers

| Layer | Irrelevant articles eliminated | Cost |
|---|---|---|
| Layer 1 — Google News RSS for regional langs | ~60–70% | Zero (already have gnews infra) |
| Layer 2 — Transliterated keyword matching | ~20–25% of remainder | One-time Gemini call per brand |
| Layer 3 — RSS category blocking | ~15–20% of remainder | Zero |
| Layer 4 — Post-NLP entity gate | ~95%+ precision on what survives | ~₹0.0001/article |
| Layer 5 — Rejection memory fix | Prevents deleted articles returning | 2-hour fix |

**Combined:** From current ~50% irrelevance rate to <5% irrelevance rate.

---

## Monitoring After Implementation

Add to the pipeline stats response and Railway logs:

```
Brand [X]: 45 collected → 12 passed keyword filter → 8 passed category filter
         → 8 NLP processed → 7 passed entity gate → 7 saved
         → 1 filtered (no brand entity found)
```

This makes relevance filtering observable without manual dashboard review.

---

## Portal Quality Classification (Revised)

After implementing filtering, re-classify portals by content quality:

| Portal | Language | Recommendation | Reason |
|---|---|---|---|
| The Hindu Tamil | ta | Keep | Highest credibility (0.90), business-focused sections |
| Vikatan | ta | Keep with category filter | Well-tagged RSS, business content exists |
| Tamil Murasu | ta | Keep | Singapore Tamil — financial/business focus |
| Daily Thanthi | ta | Keep with keyword filter | Large circulation, covers business |
| Polimer News | ta | Re-evaluate | TV news — high noise, low business relevance |
| Puthiyathalaimurai | ta | Remove | Almost exclusively politics/crime/cinema |
| Sathiyam TV | ta | Remove | General TV news, no business focus |
| Maalaimalar | ta | Keep with keyword filter | Established newspaper |
| Amar Ujala | hi | Keep with keyword filter | Large Hindi daily, covers business |
| Dainik Bhaskar | hi | Keep with keyword filter | National reach, business sections |
| Dainik Jagran | hi | Keep with keyword filter | Largest Hindi daily |
| Prabhat Khabar | hi | Remove temporarily | Heavy local politics/crime |
| Prajavani | kn | Keep | Highest credibility Kannada portal |
| Vijaya Karnataka | kn | Keep with keyword filter | ET group — business coverage |
| Kannada Prabha | kn | Keep with keyword filter | Established newspaper |
| TV9 Kannada | kn | Remove | TV news — sports/politics heavy |
| Public TV | kn | Remove | Low credibility (0.70), general TV |
| Ananda Bazar | bn | Keep | Highest Bengali credibility (0.90) |
| Ei Samay | bn | Keep with category filter | Times group, business sections |
| Sangbad Pratidin | bn | Remove | Tabloid-style, entertainment-heavy |

---

## Why This Problem Matters for Client Deliverables

The Phase 3.0 spec (web-sentiment-framework) requires:

> *"Any monthly report should disclose which languages were monitored and the confidence level of sentiment classification per language."*

If 50%+ of regional language articles are irrelevant gossip and sports scored as brand sentiment, the confidence of the regional sentiment score is meaningless. A Tamil sentiment score of "34% positive, 40% negative" currently includes sports match results and film reviews — it does not reflect how Tamil-language media covers the brand.

Fixing relevance filtering is a prerequisite for regional language sentiment to be reportable.
