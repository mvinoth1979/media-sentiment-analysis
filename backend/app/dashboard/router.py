from collections import Counter
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from app.tenants.access import require_brand_access
from app.storage.postgres import get_articles, get_kpi_summary, get_db
from app.storage.influxdb import query_sentiment_trend
from app.pipeline.perception import calculate_perception_score
from app.dashboard.schemas import (
    OverviewResponse, KPISummary, ArticleItem, SourceStat, TopicStat, TrendPoint,
    Annotation, AnnotationCreate,
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

    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=days)
    previous_start = now - timedelta(days=days * 2)
    current_window = _window_kpi(brand_id, current_start.isoformat(), now.isoformat())
    previous_window = _window_kpi(brand_id, previous_start.isoformat(), current_start.isoformat())
    wow_delta = _compute_wow_delta(current_window, previous_window)

    return OverviewResponse(
        kpi=KPISummary(perception_score=recent_score, **kpi_raw, **wow_delta),
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
        last_processed_at=recent[0].get("collected_at") if recent else None,
    )


def _window_kpi(brand_id: str, date_from: str, date_to: str) -> dict:
    articles = get_articles(brand_id, limit=500, date_from=date_from, date_to=date_to)
    score = calculate_perception_score([
        {
            "sentiment_score": a.get("sentiment_score", 0),
            "source_credibility": a.get("source_credibility", 0.5),
            "reach_score": a.get("reach_score", 0),
        }
        for a in articles
    ])
    return {"count": len(articles), "perception_score": score}


def _compute_wow_delta(current: dict, previous: dict) -> dict:
    if previous["count"] == 0:
        return {"perception_score_delta": None, "mentions_delta_pct": None}
    return {
        "perception_score_delta": round(current["perception_score"] - previous["perception_score"], 2),
        "mentions_delta_pct": round((current["count"] - previous["count"]) / previous["count"] * 100, 1),
    }


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


def _compute_topic_stats(articles: list[dict]) -> list[TopicStat]:
    topic_map: dict[str, dict] = {}
    for a in articles:
        label = a.get("sentiment_label", "neutral")
        for topic in a.get("topics") or []:
            if topic not in topic_map:
                topic_map[topic] = {"topic": topic, "count": 0,
                                    "positive": 0, "negative": 0, "neutral": 0}
            topic_map[topic]["count"] += 1
            topic_map[topic][label] = topic_map[topic].get(label, 0) + 1

    return [
        TopicStat(**v)
        for v in sorted(topic_map.values(), key=lambda x: x["count"], reverse=True)
    ]


@router.get("/topics/{brand_id}", response_model=list[TopicStat])
def get_topics(
    brand_id: str,
    _user: dict = Depends(require_brand_access),
):
    articles = get_articles(brand_id, limit=500)
    return _compute_topic_stats(articles)


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


@router.get("/trends/{brand_id}/annotations", response_model=list[Annotation])
def get_trend_annotations(
    brand_id: str,
    _user: dict = Depends(require_brand_access),
):
    db = get_db()
    rows = db.table("trend_annotations").select("*") \
              .eq("brand_id", brand_id).order("date").execute().data
    return rows


@router.post("/trends/{brand_id}/annotations", response_model=Annotation)
def create_trend_annotation(
    brand_id: str,
    payload: AnnotationCreate,
    user: dict = Depends(require_brand_access),
):
    db = get_db()
    row = {
        "brand_id": brand_id,
        "date": payload.date,
        "label": payload.label,
        "created_by": user["user_id"],
    }
    inserted = db.table("trend_annotations").insert(row).execute().data
    return inserted[0]
