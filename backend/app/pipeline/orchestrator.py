import logging
import time
from app.ingestion.portals import get_portals_for_languages
from app.ingestion.gnews import get_gnews_portals
from app.ingestion.rss_collector import collect_portal
from app.ingestion.deduplication import filter_new_articles
from app.nlp.router import analyse_article
from app.pipeline.perception import calculate_perception_score
from app.storage.postgres import save_article
from app.storage.influxdb import write_sentiment_point
from app.storage.r2 import archive_article

log = logging.getLogger(__name__)


def run_brand_pipeline(brand: dict, config: dict) -> dict:
    brand_id = brand["id"]
    keywords = config.get("keywords", [])
    languages = config.get("languages", ["en"])
    stats = {"brand_id": brand_id, "collected": 0, "processed": 0, "errors": 0}

    portals = get_portals_for_languages(languages)
    portals = portals + get_gnews_portals(keywords, "en")
    all_articles: list[dict] = []

    for portal in portals:
        try:
            articles = collect_portal(portal, keywords, brand_id)
            log.info("Portal %s → %d articles", portal["id"], len(articles))
            all_articles.extend(articles)
        except Exception as e:
            log.error("Portal %s failed: %s", portal["id"], e)
            stats["errors"] += 1

    stats["collected"] = len(all_articles)
    new_articles = filter_new_articles(all_articles, brand_id)

    if not new_articles:
        return stats

    processed_articles = []
    for article in new_articles:
        time.sleep(4)  # ~15 req/min — Gemini free tier limit
        try:
            nlp = analyse_article(article)
            if nlp is None:
                stats["errors"] += 1
                continue
            nlp_dict = nlp.to_dict()
            archive_article(article)
            save_article(article, nlp_dict)
            processed_articles.append({**article, **nlp_dict})
            stats["processed"] += 1
        except Exception as e:
            log.error("Article %s failed: %s", article.get("content_hash"), e)
            stats["errors"] += 1

    if processed_articles:
        score = calculate_perception_score(processed_articles)
        counts = {
            "positive": sum(1 for a in processed_articles if a.get("sentiment_label") == "positive"),
            "negative": sum(1 for a in processed_articles if a.get("sentiment_label") == "negative"),
            "neutral":  sum(1 for a in processed_articles if a.get("sentiment_label") == "neutral"),
            "total": len(processed_articles),
        }
        write_sentiment_point(brand_id, score, counts)

    return stats
