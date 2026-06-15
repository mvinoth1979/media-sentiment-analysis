from urllib.parse import quote_plus


def get_gnews_portals(keywords: list[str], language: str = "en") -> list[dict]:
    """Generate Google News RSS search portals for each top keyword.

    Returns portal-compatible dicts that plug straight into collect_portal.
    Only English is supported — Google News India has no Tamil RSS search.
    """
    if not keywords or language != "en":
        return []

    portals = []
    # Use up to the first 3 keywords to avoid too many RSS requests
    for kw in keywords[:3]:
        query = quote_plus(f"{kw} India")
        portals.append({
            "id": f"gnews_{kw.lower().replace(' ', '_')}",
            "name": f"Google News — {kw}",
            "language": "en",
            "credibility": 0.75,
            "rss_url": (
                f"https://news.google.com/rss/search"
                f"?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            ),
        })
    return portals
