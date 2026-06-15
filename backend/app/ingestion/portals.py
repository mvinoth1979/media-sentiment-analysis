from typing import Optional

PORTALS: list[dict] = [
    # English portals
    {"id": "the_hindu",       "name": "The Hindu",         "language": "en", "credibility": 0.92,
     "rss_url": "https://www.thehindu.com/feeder/default.rss"},
    {"id": "times_of_india",  "name": "Times of India",    "language": "en", "credibility": 0.85,
     "rss_url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
    {"id": "ndtv",            "name": "NDTV",              "language": "en", "credibility": 0.88,
     "rss_url": "https://feeds.feedburner.com/ndtvnews-top-stories"},
    {"id": "india_today",     "name": "India Today",       "language": "en", "credibility": 0.84,
     "rss_url": "https://www.indiatoday.in/rss/home"},
    {"id": "the_news_minute", "name": "The News Minute",   "language": "en", "credibility": 0.82,
     "rss_url": "https://www.thenewsminute.com/feeds/rss"},
    {"id": "deccan_herald",   "name": "Deccan Herald",     "language": "en", "credibility": 0.80,
     "rss_url": "https://www.deccanherald.com/rss-feeds/news.rss"},
    {"id": "the_wire",        "name": "The Wire",          "language": "en", "credibility": 0.81,
     "rss_url": "https://thewire.in/feed"},
    {"id": "economic_times",  "name": "Economic Times",    "language": "en", "credibility": 0.86,
     "rss_url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms"},
    # Tamil portals
    {"id": "dinamalar",       "name": "Dinamalar",         "language": "ta", "credibility": 0.88,
     "rss_url": "https://www.dinamalar.com/rss/top_news_rss.asp"},
    {"id": "dinamani",        "name": "Dinamani",          "language": "ta", "credibility": 0.85,
     "rss_url": "https://www.dinamani.com/rss/"},
    {"id": "dina_thanthi",    "name": "Dina Thanthi",      "language": "ta", "credibility": 0.86,
     "rss_url": "https://www.dinathanthi.com/feed/"},
    {"id": "vikatan",         "name": "Vikatan",           "language": "ta", "credibility": 0.83,
     "rss_url": "https://www.vikatan.com/rss/all-news.xml"},
    {"id": "puthiya_thalaimurai", "name": "Puthiya Thalaimurai", "language": "ta", "credibility": 0.80,
     "rss_url": "https://www.puthiyathalaimurai.com/feed/"},
    {"id": "kalakkal_news",   "name": "Kalakkal News",     "language": "ta", "credibility": 0.72,
     "rss_url": "https://www.kalakkal.com/feed/"},
    {"id": "tamil_samayam",   "name": "Tamil Samayam",     "language": "ta", "credibility": 0.82,
     "rss_url": "https://tamil.samayam.com/feeds/rss/index.cms"},
]

_portal_index: dict[str, dict] = {p["id"]: p for p in PORTALS}

def get_portal(portal_id: str) -> Optional[dict]:
    return _portal_index.get(portal_id)

def get_portals_for_languages(languages: list[str]) -> list[dict]:
    return [p for p in PORTALS if p["language"] in languages]
