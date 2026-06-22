import logging
from app.ingestion.portals import get_portals_for_languages
from app.ingestion.gnews import get_gnews_portals
from app.ingestion.rss_collector import collect_portal
from app.ingestion.deduplication import filter_new_articles, mark_article_seen, filter_syndicated
from app.ingestion.youtube_collector import collect_youtube_for_brand
from app.ingestion.reddit_collector import collect_reddit_for_brand
from app.ingestion.google_reviews_collector import collect_google_reviews_for_brand
from app.ingestion.keyword_variants import get_variants_for_keywords
from app.nlp.router import analyse_article
from app.pipeline.perception import calculate_perception_score
from app.storage.postgres import save_article, update_pipeline_status, decrement_bootstrap_runs
from app.storage.alerts import check_and_fire_alerts
from app.storage.rejection_store import is_rejected
from app.storage.influxdb import write_sentiment_point
from app.storage.r2 import archive_article
from app.pipeline.dead_letter import push_to_dlq
from app.pipeline.virality_detector import save_snapshot, compute_virality_flags

log = logging.getLogger(__name__)


def _entity_relevant(nlp_dict: dict, keywords: list[str], script_variants: dict) -> bool:
    """Return True if any brand keyword appears in the NLP-extracted entity list.

    Checks both English keywords and any script variants. Used as the final
    relevance gate (Layer 4) for non-English articles before saving to DB.
    """
    entities = [e.lower() for e in (nlp_dict.get("entities") or [])]
    all_variants = [v for variants in script_variants.values() for v in variants]
    for kw in keywords:
        kw_l = kw.lower()
        if any(kw_l in e or e in kw_l for e in entities):
            return True
    for variant in all_variants:
        if variant and any(variant.lower() in e or e in variant.lower() for e in entities):
            return True
    return False


def run_brand_pipeline(brand: dict, config: dict) -> dict:
    brand_id = brand["id"]
    keywords = config.get("keywords", [])
    languages = config.get("languages", ["en"])
    # Fetch transliterated keyword variants for this brand's keyword set
    keyword_variants = get_variants_for_keywords(keywords)
    stats = {"brand_id": brand_id, "collected": 0, "processed": 0, "errors": 0,
             "filtered_irrelevant": 0}

    update_pipeline_status(brand_id, "running")

    try:
        # Google News portals come FIRST — they are pre-filtered by keyword so their
        # articles fill the per-language cap with relevant content. Static portals
        # now also apply keyword filtering (English + script variants) via collect_portal.
        portals = get_gnews_portals(keywords, languages) + get_portals_for_languages(languages)
        all_articles: list[dict] = []

        for portal in portals:
            try:
                articles = collect_portal(portal, keywords, brand_id,
                                          keyword_variants=keyword_variants)
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
        # A1: Story-level syndication dedup — wire-service articles republished
        # across N portals are collapsed to one before NLP runs. The others get
        # their syndication_count incremented in the DB instead.
        _new, syndicated_count = filter_syndicated(_new, brand_id)
        if syndicated_count:
            log.info("Brand %s: %d syndicated stories collapsed", brand_id[:8], syndicated_count)
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

        # YouTube collection — separate sub-cap (10 videos + 50 comments) so it cannot
        # crowd out news articles. Only runs when brand_config.youtube_enabled = True.
        if config.get("youtube_enabled", False):
            try:
                yt_raw = collect_youtube_for_brand(brand, config)
                yt_new = filter_new_articles(yt_raw, brand_id)
                yt_new = [a for a in yt_new
                          if not is_rejected(brand_id, a.get("url", ""), a.get("title", ""))]
                new_articles.extend(yt_new)
                stats["collected"] += len(yt_raw)
            except Exception as e:
                log.error("YouTube collection failed for brand %s: %s", brand_id[:8], e)
                stats["errors"] += 1

        # Reddit collection — sub-cap (10 posts + 50 comments) so it cannot crowd out news.
        # Only runs when brand_config.reddit_enabled = True and credentials are set.
        if config.get("reddit_enabled", False):
            log.info("Reddit collection starting for brand %s", brand_id[:8])
            try:
                reddit_raw = collect_reddit_for_brand(brand, config)
                log.info("Reddit collection done for brand %s: %d raw items", brand_id[:8], len(reddit_raw))
                reddit_new = filter_new_articles(reddit_raw, brand_id)
                reddit_new = [a for a in reddit_new
                              if not is_rejected(brand_id, a.get("url", ""), a.get("title", ""))]
                new_articles.extend(reddit_new)
                stats["collected"] += len(reddit_raw)
            except Exception as e:
                log.error("Reddit collection failed for brand %s: %s", brand_id[:8], e)
                stats["errors"] += 1
        else:
            log.info("Reddit skipped for brand %s (reddit_enabled=%s)", brand_id[:8], config.get("reddit_enabled"))

        # Google Business Reviews — separate sub-cap (5 reviews) so it cannot crowd out news.
        # Only runs when brand_config.google_reviews_enabled = True and API key is set.
        if config.get("google_reviews_enabled", False):
            log.info("Google Reviews collection starting for brand %s", brand_id[:8])
            try:
                gr_raw = collect_google_reviews_for_brand(brand, config)
                log.info("Google Reviews done for brand %s: %d raw items", brand_id[:8], len(gr_raw))
                gr_new = filter_new_articles(gr_raw, brand_id)
                gr_new = [a for a in gr_new
                          if not is_rejected(brand_id, a.get("url", ""), a.get("title", ""))]
                new_articles.extend(gr_new)
                stats["collected"] += len(gr_raw)
            except Exception as e:
                log.error("Google reviews collection failed for brand %s: %s", brand_id[:8], e)
                stats["errors"] += 1
        else:
            log.info("Google Reviews skipped for brand %s (google_reviews_enabled=%s)", brand_id[:8], config.get("google_reviews_enabled"))

        if config.get("trustpilot_enabled", False):
            try:
                from app.ingestion.trustpilot_collector import collect_trustpilot_for_brand
                tp_raw = collect_trustpilot_for_brand(brand, config)
                tp_new = filter_new_articles(tp_raw, brand_id)
                tp_new = [a for a in tp_new if not is_rejected(brand_id, a.get("url", ""), a.get("title", ""))]
                new_articles.extend(tp_new)
                stats["collected"] += len(tp_raw)
            except Exception as e:
                log.error("Trustpilot collection failed for brand %s: %s", brand_id[:8], e)
                stats["errors"] += 1
        else:
            log.info("Trustpilot skipped for brand %s (trustpilot_enabled=%s)", brand_id[:8], config.get("trustpilot_enabled"))

        if config.get("mouthshut_enabled", False):
            try:
                from app.ingestion.mouthshut_collector import collect_mouthshut_for_brand
                ms_raw = collect_mouthshut_for_brand(brand, config)
                ms_new = filter_new_articles(ms_raw, brand_id)
                ms_new = [a for a in ms_new if not is_rejected(brand_id, a.get("url", ""), a.get("title", ""))]
                new_articles.extend(ms_new)
                stats["collected"] += len(ms_raw)
            except Exception as e:
                log.error("MouthShut collection failed for brand %s: %s", brand_id[:8], e)
                stats["errors"] += 1
        else:
            log.info("MouthShut skipped for brand %s", brand_id[:8])

        if config.get("justdial_enabled", False):
            try:
                from app.ingestion.justdial_collector import collect_justdial_for_brand
                jd_raw = collect_justdial_for_brand(brand, config)
                jd_new = filter_new_articles(jd_raw, brand_id)
                jd_new = [a for a in jd_new if not is_rejected(brand_id, a.get("url", ""), a.get("title", ""))]
                new_articles.extend(jd_new)
                stats["collected"] += len(jd_raw)
            except Exception as e:
                log.error("JustDial collection failed for brand %s: %s", brand_id[:8], e)
                stats["errors"] += 1
        else:
            log.info("JustDial skipped for brand %s", brand_id[:8])

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

                # Layer 4: post-NLP entity gate for non-English articles.
                # If the LLM found no brand entity in the text, the article is
                # structurally irrelevant regardless of sentiment score. Mark it
                # seen (prevents re-ingestion) but do not save to articles table.
                if lang != "en" and article.get("source_type", "news") == "news":
                    if not _entity_relevant(nlp_dict, keywords, keyword_variants):
                        mark_article_seen(article["content_hash"], brand_id)
                        stats["filtered_irrelevant"] += 1
                        log.info(
                            "Entity gate filtered [%s] %s",
                            lang, article.get("title", "")[:70],
                        )
                        continue

                archive_article(article)
                article_id = save_article(article, nlp_dict)
                mark_article_seen(article["content_hash"], brand_id)
                if article.get("source_type") == "youtube_video" and article_id:
                    meta = article.get("reach_metadata") or {}
                    save_snapshot(
                        article_id=article_id,
                        brand_id=brand_id,
                        view_count=int(meta.get("view_count") or 0),
                        comment_count=int(meta.get("comment_count") or 0),
                        negative_count=0,
                    )
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

        # Virality detection — runs after all articles are saved so snapshots exist.
        # Needs ≥1 day of prior history to produce flags; harmless on first run.
        virality_flags = compute_virality_flags(brand_id)
        if virality_flags:
            log.warning(
                "Brand %s: %d virality flag(s) detected: %s",
                brand_id[:8],
                len(virality_flags),
                [(f["title"][:40], f["flag_level"]) for f in virality_flags],
            )

    finally:
        update_pipeline_status(brand_id, "idle", stats)
        if config.get("bootstrap_runs_remaining", 0) > 0:
            decrement_bootstrap_runs(brand_id)

    return stats
