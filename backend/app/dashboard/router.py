from collections import Counter
from fastapi import APIRouter, Depends, Query
from app.tenants.access import require_brand_access
from app.storage.postgres import get_articles, get_kpi_summary
from app.storage.influxdb import query_sentiment_trend
from app.pipeline.perception import calculate_perception_score
from app.dashboard.schemas import (
    OverviewResponse, KPISummary, ArticleItem, SourceStat, TrendPoint
)

router = APIRouter()


@router.get("/overview/{brand_id}", response_model=OverviewResponse)
def get_overview(
    brand_id: str,
    days: int = Query(7, ge=1, le=90),
    _user: dict = Depends(require_brand_access),
):
    kpi_raw = get_kpi_summary(brand_id)
    try:
        trend_raw = query_sentiment_trend(brand_id, days)
    except Exception:
        trend_raw = []
    recent = get_articles(brand_id, limit=10)

    recent_score = calculate_perception_score([
        {
            "sentiment_score": a.get("sentiment_score", 0),
            "source_credibility": a.get("source_credibility", 0.5),
            "reach_score": a.get("reach_score", 0),
        }
        for a in recent
    ])

    kw_counter: Counter = Counter()
    topic_counter: Counter = Counter()

    all_articles = get_articles(brand_id, limit=500)
    for a in all_articles:
        kw_counter.update(a.get("keywords", []))
        topic_counter.update(a.get("topics", []))

    return OverviewResponse(
        kpi=KPISummary(perception_score=recent_score, **kpi_raw),
        trend=[TrendPoint(**p) for p in trend_raw],
        recent_mentions=[
            ArticleItem(
                id=a.get("id", ""),
                title=a.get("title", ""),
                url=a.get("url", ""),
                portal_id=a.get("portal_id", ""),
                published_at=a.get("published_at"),
                sentiment_label=a.get("sentiment_label", "neutral"),
                sentiment_score=a.get("sentiment_score") or 0.0,
                language=a.get("language", "en"),
                source_credibility=a.get("source_credibility") or 0.5,
                entities=a.get("entities") or [],
                topics=a.get("topics") or [],
                keywords=a.get("keywords") or [],
                model_used=a.get("model_used"),
            )
            for a in recent
        ],
        top_sources=_compute_source_stats(all_articles)[:5],
        top_keywords=[kw for kw, _ in kw_counter.most_common(15)],
        top_topics=[t for t, _ in topic_counter.most_common(10)],
    )


def _compute_source_stats(articles: list[dict]) -> list[SourceStat]:
    source_map: dict[str, dict] = {}
    for a in articles:
        pid = a.get("portal_id", "unknown")
        if pid not in source_map:
            source_map[pid] = {"portal_id": pid, "count": 0,
                               "positive": 0, "negative": 0, "neutral": 0,
                               "_cred_sum": 0.0}
        source_map[pid]["count"] += 1
        source_map[pid]["_cred_sum"] += a.get("source_credibility", 0.5)
        label = a.get("sentiment_label", "neutral")
        source_map[pid][label] = source_map[pid].get(label, 0) + 1

    return [
        SourceStat(avg_credibility=round(v.pop("_cred_sum") / v["count"], 2), **v)
        for v in sorted(source_map.values(), key=lambda x: x["count"], reverse=True)
    ]


@router.get("/sources/{brand_id}", response_model=list[SourceStat])
def get_sources(
    brand_id: str,
    _user: dict = Depends(require_brand_access),
):
    articles = get_articles(brand_id, limit=500)
    return _compute_source_stats(articles)


@router.get("/mentions/{brand_id}", response_model=list[ArticleItem])
def get_mentions(
    brand_id: str,
    limit: int = Query(50, le=200),
    offset: int = 0,
    sentiment: str | None = None,
    language: str | None = None,
    portal_id: str | None = None,
    topic: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    _user: dict = Depends(require_brand_access),
):
    return get_articles(brand_id, limit=limit, offset=offset,
                        sentiment=sentiment, language=language,
                        portal_id=portal_id, topic=topic,
                        date_from=date_from, date_to=date_to, q=q)
