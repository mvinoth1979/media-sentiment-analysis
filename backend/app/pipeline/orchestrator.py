import logging
from app.ingestion.portals import get_portals_for_languages
from app.ingestion.gnews import get_gnews_portals
from app.ingestion.rss_collector import collect_portal
from app.ingestion.deduplication import filter_new_articles, mark_article_seen
from app.nlp.router import analyse_article
from app.pipeline.perception import calculate_perception_score
from app.storage.postgres import save_article
from app.storage.rejection_store import is_rejected
from app.storage.influxdb import write_sentiment_point
from app.storage.r2 import archive_article
from app.pipeline.dead_letter import push_to_dlq

log = logging.getLogger(__name__)


def run_brand_pipeline(brand: dict, config: dict) -> dict:
    brand_id = brand["id"]
    keywords = config.get("keywords", [])
    languages = config.get("languages", ["en"])
    stats = {"brand_id": brand_id, "collected": 0, "processed": 0, "errors": 0}

    # Google News portals come FIRST — they are pre-filtered by keyword so their
    # articles fill the per-language cap with relevant content. Static portals
    # (especially Tamil ones with skip_keyword_filter) are supplementary and only
    # consume cap slots when Google News doesn't fill them.
    portals = get_gnews_portals(keywords, languages) + get_portals_for_languages(languages)
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
    _new = filter_new_articles(all_articles, brand_id)
    # Skip articles that match user-rejected content (exact URL or similar title).
    # This is the learning loop: user deletions feed article_rejections table and
    # new pipeline runs respect that knowledge before spending NLP quota.
    _new = [a for a in _new if not is_rejected(brand_id, a.get("url", ""), a.get("title", ""))]
    # Capped low (not 50) so total daily NLP call volume across all brands stays
    # under Gemini/Groq free-tier daily quotas — see app/pipeline/scheduler.py
    # for the staleness-based ordering that ensures fairness under this cap.
    en_new = [a for a in _new if a.get("language") == "en"][:20]
    ta_new = [a for a in _new if a.get("language") == "ta"][:20]
    new_articles = en_new + ta_new

    if not new_articles:
        return stats

    log.info("Brand %s: %d EN + %d TA articles to process",
             brand_id[:8], len(en_new), len(ta_new))
    processed_articles = []
    for article in new_articles:
        try:
            lang = article.get("language", "?")
            nlp = analyse_article(article)
            if nlp is None:
                log.warning("NLP None [%s] %s", lang, article.get("title", "")[:60])
                stats["errors"] += 1
                push_to_dlq(article, brand_id)
                continue
            nlp_dict = nlp.to_dict()
            archive_article(article)
            save_article(article, nlp_dict)
            mark_article_seen(article["content_hash"], brand_id)
            processed_articles.append({**article, **nlp_dict})
            stats["processed"] += 1
        except Exception as e:
            log.error("Article %s failed: %s", article.get("content_hash"), e)
            stats["errors"] += 1
            push_to_dlq(article, brand_id)

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
