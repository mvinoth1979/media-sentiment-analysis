import json
import logging
import redis
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    items = []
    while len(items) < max_items:
        item = r.lpop(QUEUE_KEY)
        if item is None:
            break
        items.append(json.loads(item))

    if not items:
        return 0

    with ThreadPoolExecutor(max_workers=min(4, len(items))) as pool:
        futures = {
            pool.submit(run_brand_pipeline, d["brand"], d["config"]): d["brand"]["name"]
            for d in items
        }
        for future in as_completed(futures):
            brand_name = futures[future]
            try:
                stats = future.result()
                log.info("Pipeline done [%s]: %s", brand_name, stats)
            except Exception as e:
                log.error("Pipeline failed [%s]: %s", brand_name, e)

    return len(items)
