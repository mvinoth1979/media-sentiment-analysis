import math
from datetime import datetime, timezone


def _recency_weight(article: dict) -> float:
    ts = article.get("collected_at") or article.get("published_at")
    if not ts:
        return 0.7
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - dt).days
    except (ValueError, TypeError):
        return 0.7
    if age_days <= 7:
        return 1.0
    if age_days <= 30:
        return 0.7
    if age_days <= 90:
        return 0.4
    return 0.15


def _engagement_multiplier(article: dict) -> float:
    meta = article.get("reach_metadata") or {}
    if not meta:
        return 0.5  # no engagement data — neutral multiplier
    views = int(meta.get("view_count") or 0) or 1
    likes = int(meta.get("like_count") or 0)
    comments = int(meta.get("comment_count") or 0)
    eng_rate = (likes + comments) / views
    # cap at 10% engagement rate → maps to 1.0 multiplier
    return min(eng_rate / 0.10, 1.0)


def _weight(article: dict) -> float:
    credibility = article.get("source_credibility", 0.5)
    reach = article.get("reach_score", 0)
    reach_normalised = math.log10(reach + 1) / math.log10(10001)
    recency = _recency_weight(article)
    engagement = _engagement_multiplier(article)
    base = credibility * (0.6 + 0.4 * reach_normalised)
    return base * recency * (0.7 + 0.3 * engagement)


def calculate_perception_score(articles: list[dict]) -> float:
    if not articles:
        return 50.0

    total_weight = 0.0
    weighted_sum = 0.0

    for a in articles:
        score = a.get("sentiment_score", 0.0)
        w = _weight(a)
        weighted_sum += score * w
        total_weight += w

    if total_weight == 0:
        return 50.0

    normalised = weighted_sum / total_weight   # -1.0 to +1.0
    return round((normalised + 1.0) / 2.0 * 100.0, 2)
