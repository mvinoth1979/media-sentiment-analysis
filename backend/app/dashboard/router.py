import csv
import io
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from app.auth.dependencies import require_brand_role, READ_ROLES, WRITE_ROLES
from app.storage.postgres import (
    get_articles, get_kpi_summary, get_db, delete_articles,
    get_pipeline_info, get_state_breakdown,
)
from app.storage.rejection_store import save_rejections
from app.storage.influxdb import (
    query_sentiment_trend,
    query_sentiment_counts_trend,
    query_sentiment_counts_trend_range,
)
from app.pipeline.perception import calculate_perception_score
from app.dashboard.schemas import (
    OverviewResponse, KPISummary, ArticleItem, AuthorInfo, MentionMetrics,
    SourceStat, TopicStat, StateStat, TrendPoint,
    Annotation, AnnotationCreate, DeleteMentionsRequest, PipelineStats,
    SentimentTrendPoint, SentimentTrendResponse,
    SourceCategoryPoint, SourceCategoriesResponse,
    HeadlineItem, HeadlinesResponse,
)

router = APIRouter()


def _article_to_item(a: dict) -> ArticleItem:
    return ArticleItem(
        id=a.get("id", ""),
        title=a.get("title", ""),
        url=a.get("url", ""),
        portal_id=a.get("portal_id", ""),
        published_at=a.get("published_at"),
        sentiment_label=a.get("sentiment_label", "neutral"),
        sentiment_score=a.get("sentiment_score") or 0.0,
        language=a.get("language", "en"),
        source_credibility=a.get("source_credibility") or 0.5,
        source_platform=a.get("source_platform", "news"),
        source_type=a.get("source_type") or "news",
        entities=a.get("entities") or [],
        topics=a.get("topics") or [],
        keywords=a.get("keywords") or [],
        states_mentioned=a.get("states_mentioned") or [],
        reach_metadata=a.get("reach_metadata") or {},
        model_used=a.get("model_used"),
        author_info=AuthorInfo(display_name=a.get("author")) if a.get("author") else None,
        metrics=MentionMetrics(
            estimated_reach=a.get("reach_score") or 0,
            influence_score=a.get("source_credibility") or 0.5,
        ),
    )


@router.get("/overview/{brand_id}", response_model=OverviewResponse)
def get_overview(
    brand_id: str,
    days: int = Query(7, ge=1, le=90),
    user: dict = Depends(require_brand_role(*READ_ROLES)),
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

    pipeline_info = get_pipeline_info(brand_id)
    raw_stats = pipeline_info.get("pipeline_last_stats") or {}

    return OverviewResponse(
        kpi=KPISummary(perception_score=recent_score, **kpi_raw, **wow_delta),
        trend=[TrendPoint(**p) for p in trend_raw],
        recent_mentions=[_article_to_item(a) for a in recent],
        top_sources=_compute_source_stats(all_articles)[:5],
        top_keywords=[kw for kw, _ in kw_counter.most_common(15)],
        top_topics=[t for t, _ in topic_counter.most_common(10)],
        state_breakdown=[StateStat(**s) for s in get_state_breakdown(brand_id)],
        last_processed_at=recent[0].get("collected_at") if recent else None,
        pipeline_status=pipeline_info.get("pipeline_status", "idle"),
        pipeline_last_run_at=pipeline_info.get("pipeline_last_run_at"),
        pipeline_last_stats=PipelineStats(
            collected=raw_stats.get("collected", 0),
            processed=raw_stats.get("processed", 0),
            errors=raw_stats.get("errors", 0),
        ),
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
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
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
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
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
    state: str | None = None,
    source_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    articles = get_articles(brand_id, limit=limit, offset=offset,
                            sentiment=sentiment, language=language,
                            portal_id=portal_id, topic=topic, state=state,
                            source_type=source_type,
                            date_from=date_from, date_to=date_to, q=q)
    return [_article_to_item(a) for a in articles]


@router.get("/export/{brand_id}")
def export_mentions_csv(
    brand_id: str,
    sentiment: str | None = None,
    language: str | None = None,
    portal_id: str | None = None,
    topic: str | None = None,
    state: str | None = None,
    source_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    articles = get_articles(brand_id, limit=2000, offset=0,
                            sentiment=sentiment, language=language,
                            portal_id=portal_id, topic=topic, state=state,
                            source_type=source_type,
                            date_from=date_from, date_to=date_to, q=q)
    output = io.StringIO()
    fields = [
        "title", "url", "portal_id", "source_type", "published_at", "collected_at",
        "sentiment_label", "sentiment_score", "language",
        "topics", "entities", "keywords", "states_mentioned", "source_credibility",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    scalar = ["title", "url", "portal_id", "source_type", "published_at", "collected_at",
              "sentiment_label", "sentiment_score", "language", "source_credibility"]
    for a in articles:
        writer.writerow({
            **{f: a.get(f, "") for f in scalar},
            "topics":           "|".join(a.get("topics") or []),
            "entities":         "|".join(a.get("entities") or []),
            "keywords":         "|".join(a.get("keywords") or []),
            "states_mentioned": "|".join(a.get("states_mentioned") or []),
        })
    output.seek(0)
    fname = f"mediasense-{brand_id[:8]}-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.delete("/mentions/{brand_id}")
def delete_mentions(
    brand_id: str,
    body: DeleteMentionsRequest,
    user: dict = Depends(require_brand_role("master_admin")),
):
    deleted = delete_articles(body.ids, brand_id)
    if deleted:
        save_rejections(brand_id, deleted, rejected_by=user.get("user_id"))
    return {"deleted": len(deleted)}


@router.get("/alerts/{brand_id}")
def get_alerts(brand_id: str, _user: dict = Depends(require_brand_role(*READ_ROLES))):
    from app.storage.alerts import get_alert_configs
    return get_alert_configs(brand_id)


class AlertCreate(BaseModel):
    alert_type: str
    threshold: float
    notify_email: str

@router.post("/alerts/{brand_id}", status_code=201)
def create_alert(
    brand_id: str,
    payload: AlertCreate,
    _user: dict = Depends(require_brand_role(*WRITE_ROLES)),
):
    from app.storage.alerts import create_alert_config
    return create_alert_config(brand_id, payload.alert_type, payload.threshold, payload.notify_email)


@router.delete("/alerts/{brand_id}/{alert_id}")
def delete_alert(
    brand_id: str,
    alert_id: str,
    _user: dict = Depends(require_brand_role(*WRITE_ROLES)),
):
    from app.storage.alerts import delete_alert_config
    delete_alert_config(alert_id)
    return {"deleted": alert_id}


@router.get("/trends/{brand_id}/annotations", response_model=list[Annotation])
def get_trend_annotations(
    brand_id: str,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    db = get_db()
    rows = db.table("trend_annotations").select("*") \
              .eq("brand_id", brand_id).order("date").execute().data
    return rows


@router.post("/trends/{brand_id}/annotations", response_model=Annotation)
def create_trend_annotation(
    brand_id: str,
    payload: AnnotationCreate,
    user: dict = Depends(require_brand_role(*WRITE_ROLES)),
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


# ── Phase 3 helpers ────────────────────────────────────────────────────────────

def _days_between(iso_from: str, iso_to: str) -> int:
    a = datetime.fromisoformat(iso_from.replace("Z", "+00:00"))
    b = datetime.fromisoformat(iso_to.replace("Z", "+00:00"))
    return abs((b - a).days)


def _aggregate_by_window(articles: list[dict], window: str) -> list[dict]:
    """Groups articles into time buckets (day or hour) and counts by sentiment."""
    from collections import defaultdict
    buckets: dict[str, dict] = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for a in articles:
        ts = a.get("collected_at") or a.get("published_at") or ""
        if not ts:
            continue
        day = ts[:10]
        buckets[day][a.get("sentiment_label", "neutral")] += 1
    return [
        {"time": f"{day}T00:00:00+00:00", **counts}
        for day, counts in sorted(buckets.items())
    ]


def _sentiment_intensity(label: str, score: float) -> str:
    """Maps existing 3-label + 0–1 score to a 5-level intensity label (no NLP rescore)."""
    if label == "positive":
        return "Strongly Positive" if score >= 0.75 else "Mildly Positive"
    if label == "negative":
        return "Strongly Negative" if score <= 0.25 else "Mildly Negative"
    return "Neutral"


def _youtube_reach_tier(view_count: int) -> str:
    if view_count >= 500_000:
        return "High"
    if view_count >= 50_000:
        return "Medium"
    return "Low"


def _get_repeat_negative_authors(brand_id: str) -> set[str]:
    """Authors with >= 2 negative articles in the last 30 days — repeat-critic flag."""
    from collections import Counter
    date_from = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    articles = get_articles(brand_id, limit=500, sentiment="negative", date_from=date_from)
    counts = Counter(
        a.get("author") for a in articles
        if a.get("author") and not str(a.get("author", "")).startswith("youtube_")
    )
    return {auth for auth, n in counts.items() if n >= 2}


# ── Phase 3 endpoints ──────────────────────────────────────────────────────────

@router.get("/trends/{brand_id}/sentiment", response_model=SentimentTrendResponse)
def get_sentiment_trend(
    brand_id: str,
    days: int = Query(30, ge=1, le=365),
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    effective_to = date_to or datetime.now(timezone.utc).isoformat()
    span_days = _days_between(date_from, effective_to) if date_from else days
    window = "1h" if span_days <= 14 else "1d"

    if date_from:
        raw = query_sentiment_counts_trend_range(brand_id, date_from, effective_to, window)
    else:
        raw = query_sentiment_counts_trend(brand_id, days)

    # Tier 1+2 overlay: aggregate from Supabase articles with credibility >= 0.78
    all_articles = get_articles(brand_id, limit=2000, date_from=date_from, date_to=date_to)
    tier12 = [a for a in all_articles if (a.get("source_credibility") or 0) >= 0.78]
    points_tier1 = _aggregate_by_window(tier12, window)

    return SentimentTrendResponse(
        points=[SentimentTrendPoint(**p) for p in raw],
        points_tier1=[SentimentTrendPoint(**p) for p in points_tier1],
        window=window,
    )


@router.get("/source-categories/{brand_id}", response_model=SourceCategoriesResponse)
def get_source_categories(
    brand_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    from collections import defaultdict
    from app.ingestion.portals import get_portal_category, get_portal_tier, CATEGORY_LABELS, CATEGORY_COLORS

    articles = get_articles(brand_id, limit=2000, date_from=date_from, date_to=date_to)
    cat_map: dict[str, dict] = {}

    for a in articles:
        pid = a.get("portal_id", "")
        cat = get_portal_category(pid)
        tier = get_portal_tier(pid)
        if cat not in cat_map:
            cat_map[cat] = {
                "category": cat,
                "label": CATEGORY_LABELS.get(cat, cat),
                "color": CATEGORY_COLORS.get(cat, "#6b7280"),
                "count": 0, "positive": 0, "negative": 0, "neutral": 0,
                "_cred_sum": 0.0,
                "_tier_dist": {"tier1": 0, "tier2": 0, "tier3": 0, "tier4": 0, "youtube": 0},
            }
        cat_map[cat]["count"] += 1
        cat_map[cat]["_cred_sum"] += a.get("source_credibility") or 0.5
        cat_map[cat][a.get("sentiment_label", "neutral")] += 1
        tier_key = f"tier{tier}" if tier > 0 else "youtube"
        cat_map[cat]["_tier_dist"][tier_key] = cat_map[cat]["_tier_dist"].get(tier_key, 0) + 1

    total = sum(v["count"] for v in cat_map.values())
    result = []
    for entry in sorted(cat_map.values(), key=lambda x: x["count"], reverse=True):
        count = entry["count"]
        cred_sum = entry.pop("_cred_sum")
        tier_dist = entry.pop("_tier_dist")
        result.append(SourceCategoryPoint(
            **{k: v for k, v in entry.items()},
            pct=round(count / total * 100, 1) if total else 0.0,
            avg_credibility=round(cred_sum / count, 2) if count else 0.0,
            tier_distribution=tier_dist,
        ))

    return SourceCategoriesResponse(categories=result, total=total)


@router.get("/headlines/{brand_id}", response_model=HeadlinesResponse)
def get_headlines(
    brand_id: str,
    tab: str = Query("positive", pattern="^(positive|negative|trending)$"),
    limit: int = Query(5, ge=1, le=10),
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    from app.ingestion.portals import get_portal, get_portal_category, get_portal_tier, TIER_LABELS

    sentiment_filter = None if tab == "trending" else tab
    articles = get_articles(
        brand_id, limit=limit * 6,
        sentiment=sentiment_filter,
        date_from=date_from, date_to=date_to,
    )

    if tab == "positive":
        articles = sorted(articles, key=lambda a: (
            a.get("sentiment_score") or 0,
            a.get("source_credibility") or 0,
        ), reverse=True)
    elif tab == "negative":
        articles = sorted(articles, key=lambda a: a.get("sentiment_score") or 1.0)
    else:
        # trending: recency-sorted (already default), filter noise
        articles = [a for a in articles if (a.get("source_credibility") or 0) >= 0.70]

    repeat_authors = _get_repeat_negative_authors(brand_id) if tab == "negative" else set()

    items = []
    for a in articles[:limit]:
        pid = a.get("portal_id", "")
        portal = get_portal(pid)
        tier = get_portal_tier(pid)
        label = a.get("sentiment_label", "neutral")
        score = a.get("sentiment_score") or 0.5
        reach_meta = a.get("reach_metadata") or {}
        view_count = int(reach_meta.get("view_count") or 0)
        author = a.get("author")

        items.append(HeadlineItem(
            id=str(a.get("id", "")),
            title=a.get("title", ""),
            url=a.get("url", ""),
            portal_id=pid,
            portal_name=portal["name"] if portal else pid.replace("_", " ").title(),
            portal_category=get_portal_category(pid),
            source_tier=tier,
            source_tier_label=TIER_LABELS.get(tier, "Tier 4"),
            published_at=a.get("published_at"),
            collected_at=a.get("collected_at"),
            sentiment_label=label,
            sentiment_score=score,
            sentiment_intensity=_sentiment_intensity(label, score),
            source_credibility=a.get("source_credibility") or 0.5,
            language=a.get("language", "en"),
            source_type=a.get("source_type") or "news",
            repeat_author=bool(author and author in repeat_authors),
            reach_tier=_youtube_reach_tier(view_count) if pid.startswith("youtube_") and view_count > 0 else None,
            author_name=author,
        ))

    return HeadlinesResponse(tab=tab, items=items)
