import logging
from app.ingestion.portals import get_portals_for_languages
from app.ingestion.gnews import get_gnews_portals
from app.ingestion.rss_collector import collect_portal
from app.ingestion.deduplication import filter_new_articles, mark_article_seen
from app.nlp.router import analyse_article
from app.pipeline.perception import calculate_perception_score
from app.storage.postgres import save_article, update_pipeline_status, decrement_bootstrap_runs
from app.storage.alerts import check_and_fire_alerts
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

    update_pipeline_status(brand_id, "running")

    try:
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
        # Cap 20 articles per language to stay within Gemini/Groq free-tier daily
        # quotas. Only process languages the brand is configured for.
        per_lang: dict[str, list] = {}
        for a in _new:
            lang = a.get("language") or "en"
            if lang not in languages:
                continue
            if lang not in per_lang:
                per_lang[lang] = []
            if len(per_lang[lang]) < 20:
                per_lang[lang].append(a)
        new_articles = [a for articles in per_lang.values() for a in articles]

        if not new_articles:
            update_pipeline_status(brand_id, "idle", stats)
            return stats

        lang_summary = " + ".join(f"{len(v)} {k.upper()}" for k, v in per_lang.items())
        log.info("Brand %s: %s articles to process", brand_id[:8], lang_summary)
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
            negative_pct = round(counts["negative"] / counts["total"] * 100, 1) if counts["total"] else 0.0
            check_and_fire_alerts(
                brand_id=brand_id,
                brand_name=brand.get("name", brand_id),
                perception_score=score,
                negative_pct=negative_pct,
                mention_count=counts["total"],
            )

    finally:
        update_pipeline_status(brand_id, "idle", stats)
        if config.get("bootstrap_runs_remaining", 0) > 0:
            decrement_bootstrap_runs(brand_id)

    return stats
