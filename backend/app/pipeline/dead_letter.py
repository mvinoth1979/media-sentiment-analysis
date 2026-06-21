import json
import logging
import redis
from app.config import settings
from app.nlp.router import analyse_article
from app.ingestion.deduplication import mark_article_seen
from app.storage.postgres import save_article
from app.storage.r2 import archive_article

log = logging.getLogger(__name__)
DLQ_KEY = "mediasense:pipeline:dlq"
MAX_RETRIES = 5


def get_redis():
    return redis.Redis(
        host=settings.upstash_redis_host,
        port=settings.upstash_redis_port,
        password=settings.upstash_redis_password,
        ssl=True,
        decode_responses=True,
    )


_DLQ_MAX_ITEMS = 500


def push_to_dlq(article: dict, brand_id: str, retry_count: int = 0):
    r = get_redis()
    # Slim the article body to keep each DLQ entry small (Upstash: 100MB/key limit)
    slim = {k: v for k, v in article.items() if k != "body"}
    slim["body"] = (article.get("body") or "")[:300]
    r.rpush(DLQ_KEY, json.dumps({
        "article": slim,
        "brand_id": brand_id,
        "retry_count": retry_count,
    }))
    # Cap at 500 entries — oldest are evicted first
    r.ltrim(DLQ_KEY, -_DLQ_MAX_ITEMS, -1)


def retry_dead_letters(max_items: int = 50) -> dict:
    r = get_redis()
    stats = {"retried": 0, "recovered": 0, "dropped": 0}

    items = []
    while len(items) < max_items:
        raw = r.lpop(DLQ_KEY)
        if raw is None:
            break
        items.append(json.loads(raw))

    for item in items:
        stats["retried"] += 1
        article = item["article"]
        brand_id = item["brand_id"]
        retry_count = item["retry_count"]
        try:
            nlp = analyse_article(article)
            if nlp is None:
                raise RuntimeError("NLP still unavailable")
            archive_article(article)
            save_article(article, nlp.to_dict())
            mark_article_seen(article["content_hash"], brand_id)
            stats["recovered"] += 1
        except Exception as e:
            if retry_count + 1 >= MAX_RETRIES:
                stats["dropped"] += 1
                log.warning("DLQ permanently dropped after %d retries [%s]: %s",
                            retry_count + 1, e, article.get("title", "")[:60])
            else:
                push_to_dlq(article, brand_id, retry_count + 1)

    return stats
