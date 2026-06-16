from typing import Optional, TypedDict


class Portal(TypedDict):
    id: str
    name: str
    language: str
    credibility: float
    rss_url: str


PORTALS: list[Portal] = [
    # English portals (verified working 2026-06)
    {"id": "the_hindu",      "name": "The Hindu",       "language": "en", "credibility": 0.92,
     "rss_url": "https://www.thehindu.com/feeder/default.rss"},
    {"id": "times_of_india", "name": "Times of India",  "language": "en", "credibility": 0.85,
     "rss_url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
    {"id": "ndtv",           "name": "NDTV",            "language": "en", "credibility": 0.88,
     "rss_url": "https://feeds.feedburner.com/ndtvnews-top-stories"},
    {"id": "india_today",    "name": "India Today",     "language": "en", "credibility": 0.84,
     "rss_url": "https://www.indiatoday.in/rss/home"},
    {"id": "economic_times", "name": "Economic Times",  "language": "en", "credibility": 0.86,
     "rss_url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms"},
    # Tamil portals (verified working 2026-06)
    # skip_keyword_filter=True: Tamil script cannot be matched by English regex;
    # relevance is handled by the 50 TA article cap + NLP sentiment analysis.
    {"id": "hindu_tamil",    "name": "The Hindu Tamil", "language": "ta", "credibility": 0.90,
     "rss_url": "https://www.hindutamil.in/feed",                          "skip_keyword_filter": True},
    {"id": "tamil_samayam",  "name": "Tamil Samayam",   "language": "ta", "credibility": 0.82,
     "rss_url": "https://tamil.samayam.com/rssfeedsdefault.cms",           "skip_keyword_filter": True},
    {"id": "polimer_news",   "name": "Polimer News",    "language": "ta", "credibility": 0.75,
     "rss_url": "https://www.polimernews.com/feed/",                       "skip_keyword_filter": True},
    {"id": "tamil_murasu",   "name": "Tamil Murasu",    "language": "ta", "credibility": 0.80,
     "rss_url": "https://www.tamilmurasu.com.sg/rss.xml",                  "skip_keyword_filter": True},
    {"id": "oneindia_tamil", "name": "Oneindia Tamil",  "language": "ta", "credibility": 0.72,
     "rss_url": "https://tamil.oneindia.com/rss/tamil-news-fb.xml",        "skip_keyword_filter": True},
    {"id": "news_tamil",     "name": "News Tamil",      "language": "ta", "credibility": 0.65,
     "rss_url": "https://www.newstamil.in/feed/",                          "skip_keyword_filter": True},
    {"id": "vikatan",        "name": "Vikatan",         "language": "ta", "credibility": 0.83,
     "rss_url": "https://www.vikatan.com/feed",                            "skip_keyword_filter": True},
    {"id": "maalaimalar",    "name": "Maalaimalar",     "language": "ta", "credibility": 0.78,
     "rss_url": "https://www.maalaimalar.com/feed",                        "skip_keyword_filter": True},
    {"id": "puthiyathalaimurai", "name": "Puthiyathalaimurai", "language": "ta", "credibility": 0.73,
     "rss_url": "https://www.puthiyathalaimurai.com/feed",                 "skip_keyword_filter": True},
    # Dinamalar: RSS server returns HTTP 500 on all paths (server-side bug, not fixable).
    # Dinamani: RSS feed discontinued — /rss redirects to their HTML homepage.
]

_portal_index: dict[str, Portal] = {p["id"]: p for p in PORTALS}


def get_portal(portal_id: str) -> Optional[Portal]:
    return _portal_index.get(portal_id)


def get_portals_for_languages(languages: list[str]) -> list[Portal]:
    return [p for p in PORTALS if p["language"] in languages]
