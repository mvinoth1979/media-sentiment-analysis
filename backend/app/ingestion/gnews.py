from urllib.parse import quote_plus

_LANG_CONFIG = {
    "en": {"hl": "en-IN", "ceid": "IN:en"},
    "ta": {"hl": "ta-IN", "ceid": "IN:ta"},
}


def get_gnews_portals(keywords: list[str], languages: list[str] | None = None) -> list[dict]:
    """Generate Google News RSS search portals for top keywords × supported languages.

    Returns portal-compatible dicts with skip_keyword_filter=True because the
    URL query already filters by keyword — regex matching on vernacular text
    would miss transliterated brand names (e.g. அமுல் for Amul).
    """
    if not keywords:
        return []

    langs = [l for l in (languages or ["en"]) if l in _LANG_CONFIG]
    if not langs:
        return []

    portals = []
    for lang in langs:
        cfg = _LANG_CONFIG[lang]
        for kw in keywords[:3]:
            query = quote_plus(f"{kw} India")
            portals.append({
                "id": f"gnews_{lang}_{kw.lower().replace(' ', '_')}",
                "name": f"Google News {lang.upper()} — {kw}",
                "language": lang,
                "credibility": 0.75,
                "skip_keyword_filter": True,
                "rss_url": (
                    f"https://news.google.com/rss/search"
                    f"?q={query}&hl={cfg['hl']}&gl=IN&ceid={cfg['ceid']}"
                ),
            })
    return portals
