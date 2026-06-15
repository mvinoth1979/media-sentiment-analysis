import math


def _weight(article: dict) -> float:
    credibility = article.get("source_credibility", 0.5)
    reach = article.get("reach_score", 0)
    reach_normalised = math.log10(reach + 1) / math.log10(10001)
    return credibility * (0.6 + 0.4 * reach_normalised)


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
