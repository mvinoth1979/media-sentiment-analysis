from typing import Optional, TypedDict


class Portal(TypedDict, total=False):
    id: str
    name: str
    language: str
    credibility: float
    rss_url: str
    category: str
    skip_keyword_filter: bool


PORTALS: list[Portal] = [
    # English portals (verified working 2026-06)
    {"id": "the_hindu",        "name": "The Hindu",         "language": "en", "credibility": 0.92, "category": "news",
     "rss_url": "https://www.thehindu.com/feeder/default.rss"},
    {"id": "times_of_india",   "name": "Times of India",    "language": "en", "credibility": 0.85, "category": "news",
     "rss_url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
    {"id": "ndtv",             "name": "NDTV",              "language": "en", "credibility": 0.88, "category": "news",
     "rss_url": "https://feeds.feedburner.com/ndtvnews-top-stories"},
    {"id": "india_today",      "name": "India Today",       "language": "en", "credibility": 0.84, "category": "news",
     "rss_url": "https://www.indiatoday.in/rss/home"},
    {"id": "economic_times",   "name": "Economic Times",    "language": "en", "credibility": 0.86, "category": "news",
     "rss_url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms"},
    {"id": "indian_express",   "name": "Indian Express",    "language": "en", "credibility": 0.87, "category": "news",
     "rss_url": "https://indianexpress.com/feed/"},
    {"id": "deccan_chronicle", "name": "Deccan Chronicle",  "language": "en", "credibility": 0.78, "category": "news",
     "rss_url": "https://www.deccanchronicle.com/feed"},
    {"id": "hindustan_times",  "name": "Hindustan Times",   "language": "en", "credibility": 0.84, "category": "news",
     "rss_url": "https://www.hindustantimes.com/feeds/rss/india/rssfeed.xml"},
    {"id": "livemint",         "name": "Mint",              "language": "en", "credibility": 0.86, "category": "news",
     "rss_url": "https://www.livemint.com/rss/news"},
    {"id": "deccan_herald",    "name": "Deccan Herald",     "language": "en", "credibility": 0.82, "category": "news",
     "rss_url": "https://www.deccanherald.com/feed"},
    {"id": "the_quint",        "name": "The Quint",         "language": "en", "credibility": 0.79, "category": "news",
     "rss_url": "https://www.thequint.com/feed"},
    {"id": "news18",           "name": "News18",            "language": "en", "credibility": 0.76, "category": "news",
     "rss_url": "https://www.news18.com/commonfeeds/v1/eng/rss/india.xml"},
    # Tamil portals — keyword filtering now applied via multilang matching in rss_collector.
    # Removed: polimer_news (TV channel, sports/politics heavy),
    #          puthiyathalaimurai (politics/crime/cinema dominated),
    #          sathiyam_tv (general TV news, no business focus).
    {"id": "hindu_tamil",    "name": "The Hindu Tamil", "language": "ta", "credibility": 0.90, "category": "news",
     "rss_url": "https://www.hindutamil.in/feed"},
    {"id": "tamil_samayam",  "name": "Tamil Samayam",   "language": "ta", "credibility": 0.82, "category": "news",
     "rss_url": "https://tamil.samayam.com/rssfeedsdefault.cms"},
    {"id": "tamil_murasu",   "name": "Tamil Murasu",    "language": "ta", "credibility": 0.80, "category": "news",
     "rss_url": "https://www.tamilmurasu.com.sg/rss.xml"},
    {"id": "oneindia_tamil", "name": "Oneindia Tamil",  "language": "ta", "credibility": 0.72, "category": "news",
     "rss_url": "https://tamil.oneindia.com/rss/tamil-news-fb.xml"},
    {"id": "vikatan",        "name": "Vikatan",         "language": "ta", "credibility": 0.83, "category": "news",
     "rss_url": "https://www.vikatan.com/feed"},
    {"id": "maalaimalar",    "name": "Maalaimalar",     "language": "ta", "credibility": 0.78, "category": "news",
     "rss_url": "https://www.maalaimalar.com/feed"},
    {"id": "daily_thanthi",    "name": "Daily Thanthi",    "language": "ta", "credibility": 0.80, "category": "news",
     "rss_url": "https://www.dailythanthi.com/feed"},
    {"id": "news_tamil",     "name": "News Tamil",      "language": "ta", "credibility": 0.65, "category": "news",
     "rss_url": "https://www.newstamil.in/feed/"},
    # Hindi portals — keyword filtering via multilang matching.
    # Removed: prabhat_khabar (heavy local Bihar/Jharkhand politics).
    {"id": "navbharat_times",  "name": "Navbharat Times",   "language": "hi", "credibility": 0.80, "category": "news",
     "rss_url": "https://navbharattimes.indiatimes.com/rssfeedstopstories.cms"},
    {"id": "amar_ujala",       "name": "Amar Ujala",        "language": "hi", "credibility": 0.82, "category": "news",
     "rss_url": "https://www.amarujala.com/rss/breaking-news.xml"},
    {"id": "jagran",           "name": "Dainik Jagran",     "language": "hi", "credibility": 0.80, "category": "news",
     "rss_url": "https://www.jagran.com/rss/news-national.xml"},
    {"id": "ndtv_india",       "name": "NDTV India",        "language": "hi", "credibility": 0.85, "category": "news",
     "rss_url": "https://ndtv.in/rss/top-stories"},
    {"id": "live_hindustan",   "name": "Hindustan",         "language": "hi", "credibility": 0.78, "category": "news",
     "rss_url": "https://www.livehindustan.com/rss/svn-livehindustan-topstories.xml"},
    {"id": "dainik_bhaskar",   "name": "Dainik Bhaskar",   "language": "hi", "credibility": 0.82, "category": "news",
     "rss_url": "https://www.bhaskar.com/rss-v1--category-1061.xml"},
    {"id": "hari_bhoomi",      "name": "Hari Bhoomi",      "language": "hi", "credibility": 0.68, "category": "news",
     "rss_url": "https://haribhoomi.com/feed/"},
    # Bengali portals — keyword filtering via multilang matching.
    # Removed: sangbad_pratidin (tabloid-style, entertainment-heavy).
    {"id": "ei_samay",         "name": "Ei Samay",          "language": "bn", "credibility": 0.78, "category": "news",
     "rss_url": "https://eisamay.indiatimes.com/rssfeedstopstories.cms"},
    {"id": "ananda_bazar",     "name": "Ananda Bazar",      "language": "bn", "credibility": 0.90, "category": "news",
     "rss_url": "https://www.anandabazar.com/feeds/top-stories.rss"},
    # Kannada portals — keyword filtering via multilang matching.
    # Removed: tv9_kannada (TV news, sports/politics heavy), public_tv (low cred, general).
    {"id": "prajavani",        "name": "Prajavani",         "language": "kn", "credibility": 0.85, "category": "news",
     "rss_url": "https://www.prajavani.net/feed"},
    {"id": "vijaya_karnataka", "name": "Vijaya Karnataka",  "language": "kn", "credibility": 0.78, "category": "news",
     "rss_url": "https://vijayakarnataka.indiatimes.com/rssfeedstopstories.cms"},
    {"id": "udayavani",        "name": "Udayavani",         "language": "kn", "credibility": 0.80, "category": "news",
     "rss_url": "https://www.udayavani.com/feed"},
    {"id": "kannada_prabha",   "name": "Kannada Prabha",   "language": "kn", "credibility": 0.78, "category": "news",
     "rss_url": "https://kannadaprabha.com/feed/"},
    # Gujarati portals — keyword filtering via multilang matching.
    {"id": "divya_bhaskar",    "name": "Divya Bhaskar",     "language": "gu", "credibility": 0.82, "category": "news",
     "rss_url": "https://www.divyabhaskar.co.in/rss-feed/1061/"},
    {"id": "gujarat_samachar", "name": "Gujarat Samachar",  "language": "gu", "credibility": 0.80, "category": "news",
     "rss_url": "https://www.gujaratsamachar.com/rss/national-feed.xml"},
    {"id": "chitralekha",      "name": "Chitralekha",      "language": "gu", "credibility": 0.72, "category": "news",
     "rss_url": "https://chitralekha.com/feed/"},
    # Excluded (RSS not available or blocked as of 2026-06):
    # Dinamalar        — HTTP 500 on all paths; /rss returns HTML homepage.
    # Dinamani         — RSS discontinued; all paths 404.
    # Dinakaran        — HTTP 403; actively blocks scrapers.
    # Business Standard — HTTP 403 on all RSS paths.
    # Financial Express — HTTP 410 (Gone); RSS retired.
    # The Wire          — Returns 200 but HTML, not XML; no valid RSS endpoint found.
    # The Print         — Returns 200 but HTML, not XML; no valid RSS endpoint found.
    # Scroll.in         — Feedburner redirect broken (404).
    # Zee News (EN/HI)  — HTTP 403 on all RSS paths.
    # Dainik Jagran (alt paths) — main RSS works; alternative category feeds 404.
    # ABP Live Hindi    — All RSS paths return errors or HTML.
    # Nai Dunia         — 404 on all known RSS paths.
    # Punjab Kesari     — 404 on all known RSS paths.
    # Bartaman Patrika  — Connection error; no reachable RSS.
    # Aajkaal           — 404 on RSS path.
    # Pratidin Time (BN)— Connection error.
    # Vishwa Karnataka  — Connection error.
    # Hosadiganta       — Connection error.
    # Sandesh (GU)      — Returns 200 but HTML, not XML.
    # Nakkheeran (TA)   — Connection error.
    # Suvarna News (KN) — Connection error.
]

_portal_index: dict[str, Portal] = {p["id"]: p for p in PORTALS}


def get_portal(portal_id: str) -> Optional[Portal]:
    return _portal_index.get(portal_id)


def get_portals_for_languages(languages: list[str]) -> list[Portal]:
    return [p for p in PORTALS if p["language"] in languages]


# --- Phase 3: Source category + authority tier helpers ---

PORTAL_CATEGORY_PREFIXES: dict[str, str] = {
    "youtube_": "youtube",
}

CATEGORY_LABELS: dict[str, str] = {
    "news":        "News & RSS",
    "youtube":     "YouTube",
    "blog":        "Blogs & Portals",
    "review_site": "Review Sites",
    "social":      "Social & Forums",
}

CATEGORY_COLORS: dict[str, str] = {
    "news":        "#6366f1",
    "youtube":     "#ef4444",
    "blog":        "#f59e0b",
    "review_site": "#22c55e",
    "social":      "#a855f7",
}

TIER_LABELS: dict[int, str] = {
    0: "YouTube",
    1: "Tier 1",
    2: "Tier 2",
    3: "Tier 3",
    4: "Tier 4",
    5: "Wire",
}


def get_portal_category(portal_id: str) -> str:
    for prefix, cat in PORTAL_CATEGORY_PREFIXES.items():
        if portal_id.startswith(prefix):
            return cat
    portal = get_portal(portal_id)
    if portal:
        return portal.get("category", "news")
    return "news"


def get_portal_tier(portal_id: str) -> int:
    """
    Maps a portal to Source Authority Tier 1–4 (0 for YouTube).
    Derived from existing credibility scores:
      Tier 1: national outlets        credibility >= 0.87
      Tier 2: regional / vernacular   credibility >= 0.78
      Tier 3: trade / specialist      credibility >= 0.68
      Tier 4: hyperlocal / community  credibility <  0.68
    """
    if portal_id.startswith("youtube_"):
        return 0
    if portal_id.startswith("gnews_"):
        return 5
    portal = get_portal(portal_id)
    if not portal:
        return 4
    cred = portal.get("credibility", 0.5)
    if cred >= 0.87:
        return 1
    if cred >= 0.78:
        return 2
    if cred >= 0.68:
        return 3
    return 4
