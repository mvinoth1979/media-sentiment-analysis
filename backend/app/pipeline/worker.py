import json
import logging
import redis
from app.config import settings
from app.pipeline.orchestrator import run_brand_pipeline

log = logging.getLogger(__name__)
QUEUE_KEY = "mediasense:pipeline:queue"


def get_redis():
    return redis.Redis(
        host=settings.upstash_redis_host,
        port=settings.upstash_redis_port,
        password=settings.upstash_redis_password,
        ssl=True,
        decode_responses=True,
    )


def enqueue_brand(brand: dict, config: dict):
    r = get_redis()
    r.rpush(QUEUE_KEY, json.dumps({"brand": brand, "config": config}))


def process_queue(max_items: int = 100):
    r = get_redis()
    processed = 0
    while processed < max_items:
        item = r.lpop(QUEUE_KEY)
        if item is None:
            break
        try:
            data = json.loads(item)
            stats = run_brand_pipeline(data["brand"], data["config"])
            log.info("Pipeline done: %s", stats)
        except Exception as e:
            log.error("Queue item failed: %s", e)
        processed += 1
    return processed
