from typing import Optional, TypedDict


class Portal(TypedDict):
    id: str
    name: str
    language: str
    credibility: float
    rss_url: str


PORTALS: list[Portal] = [
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
    # Tamil portals — individual RSS feeds were dead (404/500) as of 2026-06.
    # Tamil coverage is now handled by Google News Tamil RSS in get_gnews_portals().
]

_portal_index: dict[str, Portal] = {p["id"]: p for p in PORTALS}


def get_portal(portal_id: str) -> Optional[Portal]:
    return _portal_index.get(portal_id)


def get_portals_for_languages(languages: list[str]) -> list[Portal]:
    return [p for p in PORTALS if p["language"] in languages]
