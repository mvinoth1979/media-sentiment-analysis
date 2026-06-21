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
    ReviewSummaryResponse, ReviewStarBucket, TopicTheme,
    SoVEntry, CompetitorSoVResponse, CompetitorDiscoveryResponse,
    ClusterArticle, IssueCluster, IssueClustersResponse,
    ToneWeek, ToneBreakdownResponse,
    DivergentArticle, DivergenceSummaryResponse,
    JournalistArticle, JournalistProfile, JournalistCoverageResponse,
    YTSentimentBucket, YTDivergentVideo, YTSentimentSplitResponse,
    IssueCategoryItem, IssueCategoriesResponse,
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
        # Phase 1 data quality fields
        author=a.get("author") or None,
        editorial_tone=a.get("editorial_tone") or None,
        sentiment_divergence=bool(a.get("sentiment_divergence")),
        is_regulatory_source=bool(a.get("is_regulatory_source")),
        issue_category=a.get("issue_category") or "other",
        # Item 9: YouTube creator type classification
        creator_type=a.get("creator_type") or None,
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
            "collected_at": a.get("collected_at"),
            "reach_metadata": a.get("reach_metadata") or {},
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
            "collected_at": a.get("collected_at"),
            "reach_metadata": a.get("reach_metadata") or {},
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
    editorial_tone: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    articles = get_articles(brand_id, limit=limit, offset=offset,
                            sentiment=sentiment, language=language,
                            portal_id=portal_id, topic=topic, state=state,
                            source_type=source_type,
                            date_from=date_from, date_to=date_to, q=q,
                            editorial_tone=editorial_tone)
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
            sentiment_divergence=bool(a.get("sentiment_divergence")),
            is_regulatory_source=bool(a.get("is_regulatory_source")),
            editorial_tone=a.get("editorial_tone") or None,
        ))

    return HeadlinesResponse(tab=tab, items=items)


def _score_to_stars(score: float) -> int:
    """Map sentiment_score (-1 to +1) to 1–5 star rating."""
    if score >= 0.5:
        return 5
    if score >= 0.1:
        return 4
    if score > -0.1:
        return 3
    if score > -0.5:
        return 2
    return 1


@router.get("/review-summary/{brand_id}", response_model=ReviewSummaryResponse)
def get_review_summary(
    brand_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    articles = get_articles(brand_id, limit=2000, date_from=date_from, date_to=date_to)
    if not articles:
        return ReviewSummaryResponse(
            total=0,
            avg_rating=0.0,
            distribution=[ReviewStarBucket(stars=s, count=0, pct=0.0) for s in (5, 4, 3, 2, 1)],
            top_positive_topics=[],
            top_negative_topics=[],
        )

    star_counts: dict[int, int] = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    pos_topics: Counter = Counter()
    neg_topics: Counter = Counter()
    score_sum = 0.0

    for a in articles:
        score = a.get("sentiment_score") or 0.0
        label = a.get("sentiment_label", "neutral")
        score_sum += score
        star_counts[_score_to_stars(score)] += 1
        topics = a.get("topics") or []
        if label == "positive":
            pos_topics.update(topics)
        elif label == "negative":
            neg_topics.update(topics)

    total = len(articles)
    avg_score = score_sum / total
    avg_rating = round((avg_score + 1) / 2 * 4 + 1, 1)

    distribution = [
        ReviewStarBucket(stars=s, count=c, pct=round(c / total * 100, 1))
        for s, c in sorted(star_counts.items(), reverse=True)
    ]

    pos_total = sum(pos_topics.values()) or 1
    neg_total = sum(neg_topics.values()) or 1

    return ReviewSummaryResponse(
        total=total,
        avg_rating=avg_rating,
        distribution=distribution,
        top_positive_topics=[
            TopicTheme(label=t, pct=round(c / pos_total * 100, 1))
            for t, c in pos_topics.most_common(5)
        ],
        top_negative_topics=[
            TopicTheme(label=t, pct=round(c / neg_total * 100, 1))
            for t, c in neg_topics.most_common(5)
        ],
    )


# SoV colour palette — brand always gets index 0 (blue)
_SOV_COLORS = ["#3b82f6", "#8b5cf6", "#06b6d4", "#f59e0b", "#10b981", "#d1d5db"]


@router.get("/competitor-sov/{brand_id}", response_model=CompetitorSoVResponse)
def get_competitor_sov(
    brand_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    db = get_db()

    brand_row = db.table("brands").select("name").eq("id", brand_id).execute().data
    brand_name = brand_row[0]["name"] if brand_row else "Brand"

    config_row = db.table("brand_configs").select("competitors").eq("brand_id", brand_id).execute().data
    configured_competitors: list[str] = (config_row[0].get("competitors") or []) if config_row else []

    articles = get_articles(brand_id, limit=2000, date_from=date_from, date_to=date_to)
    total = len(articles)

    if total == 0:
        return CompetitorSoVResponse(
            total_articles=0,
            entries=[SoVEntry(name=brand_name, count=0, pct=100.0, color=_SOV_COLORS[0], is_brand=True)],
            source="configured" if configured_competitors else "entity_fallback",
        )

    if configured_competitors:
        # Count articles where each competitor name appears in title or entities
        comp_counts: dict[str, int] = {}
        for comp in configured_competitors[:5]:
            comp_lower = comp.lower()
            count = sum(
                1 for a in articles
                if comp_lower in (a.get("title") or "").lower()
                or any(comp_lower in (e or "").lower() for e in (a.get("entities") or []))
            )
            if count > 0:
                comp_counts[comp] = count
        source = "configured"
    else:
        # Fallback: top co-mentioned named entities, excluding media portals,
        # Indian states/UTs, and the brand's own name
        from app.ingestion.portals import PORTALS
        _INDIAN_STATES_SET = {
            "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
            "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
            "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
            "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
            "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
            "west bengal", "delhi", "jammu & kashmir", "jammu and kashmir", "ladakh",
            "chandigarh", "puducherry", "india", "भारत",
        }
        _PORTAL_NAMES = {p["name"].lower() for p in PORTALS}
        brand_lower = brand_name.lower()

        def _is_blocked(entity: str) -> bool:
            el = entity.lower().strip()
            return (
                el in _INDIAN_STATES_SET
                or el in _PORTAL_NAMES
                or brand_lower in el
                or el in brand_lower
                or len(el) < 3
            )

        entity_counter: Counter = Counter()
        for a in articles:
            for e in (a.get("entities") or []):
                if e and not _is_blocked(e):
                    entity_counter[e] += 1

        comp_counts = dict(entity_counter.most_common(4))
        source = "entity_fallback"

    # Normalize to SoV: brand has weight = total; each competitor weight = its count
    grand_total = total + sum(comp_counts.values())
    entries: list[SoVEntry] = [
        SoVEntry(
            name=brand_name,
            count=total,
            pct=round(total / grand_total * 100, 1),
            color=_SOV_COLORS[0],
            is_brand=True,
        )
    ]
    for i, (name, count) in enumerate(
        sorted(comp_counts.items(), key=lambda x: x[1], reverse=True), start=1
    ):
        entries.append(SoVEntry(
            name=name,
            count=count,
            pct=round(count / grand_total * 100, 1),
            color=_SOV_COLORS[min(i, len(_SOV_COLORS) - 1)],
        ))

    return CompetitorSoVResponse(total_articles=total, entries=entries, source=source)


@router.post("/competitor-sov/{brand_id}/discover", response_model=CompetitorDiscoveryResponse)
def discover_and_save_competitors(
    brand_id: str,
    _user: dict = Depends(require_brand_role(*WRITE_ROLES)),
):
    from app.nlp.gemini_handler import discover_competitors
    db = get_db()

    brand_row = db.table("brands").select("name").eq("id", brand_id).execute().data
    brand_name = brand_row[0]["name"] if brand_row else "Brand"

    config_row = db.table("brand_configs").select("keywords").eq("brand_id", brand_id).execute().data
    keywords: list[str] = (config_row[0].get("keywords") or []) if config_row else []

    # Build candidate entity list — reuse same block-list as the SoV GET endpoint
    from app.ingestion.portals import PORTALS as _PORTALS
    _STATES = {
        "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
        "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
        "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
        "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
        "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
        "west bengal", "delhi", "jammu & kashmir", "jammu and kashmir", "ladakh",
        "chandigarh", "puducherry", "india",
    }
    _MEDIA = {p["name"].lower() for p in _PORTALS}
    brand_lower = brand_name.lower()

    articles = get_articles(brand_id, limit=1000)
    entity_counter: Counter = Counter()
    for a in articles:
        for e in (a.get("entities") or []):
            el = (e or "").lower().strip()
            if el and len(el) >= 3 and el not in _STATES and el not in _MEDIA \
                    and brand_lower not in el and el not in brand_lower:
                entity_counter[e] += 1
    candidate_entities = [e for e, _ in entity_counter.most_common(20)]

    competitors = discover_competitors(brand_name, keywords, candidate_entities)

    saved = False
    if competitors:
        db.table("brand_configs") \
          .update({"competitors": competitors}) \
          .eq("brand_id", brand_id) \
          .execute()
        saved = True

    return CompetitorDiscoveryResponse(competitors=competitors, saved=saved)


# ── Issue Clusters (B4) ────────────────────────────────────────────────────────

class _UF:
    """Minimal union-find for topic co-occurrence merging."""
    def __init__(self): self._p: dict[str, str] = {}
    def find(self, x: str) -> str:
        self._p.setdefault(x, x)
        if self._p[x] != x:
            self._p[x] = self.find(self._p[x])
        return self._p[x]
    def union(self, x: str, y: str) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self._p[ry] = rx


def _build_clusters(articles: list[dict], cutoff_7d: str) -> list[dict]:
    """Group NLP topics into issue clusters via co-occurrence union-find.

    Two topics belong to the same cluster when they co-appear in ≥2 articles.
    Cluster label = the topic with the highest individual article count.
    """
    # topic → article indices
    topic_arts: dict[str, list[int]] = {}
    for i, a in enumerate(articles):
        for t in (a.get("topics") or []):
            if t:
                topic_arts.setdefault(t, []).append(i)

    if not topic_arts:
        return []

    # co-occurrence counts (within each article, all topic pairs)
    co_occ: Counter = Counter()
    for a in articles:
        topics = list({t for t in (a.get("topics") or []) if t})
        for j in range(len(topics)):
            for k in range(j + 1, len(topics)):
                co_occ[tuple(sorted((topics[j], topics[k])))] += 1

    # merge topics that co-appear in ≥2 articles
    uf = _UF()
    for (ta, tb), cnt in co_occ.items():
        if cnt >= 2:
            uf.union(ta, tb)

    # group topics by cluster root
    root_members: dict[str, list[str]] = {}
    for t in topic_arts:
        root = uf.find(t)
        root_members.setdefault(root, []).append(t)

    clusters: list[dict] = []
    for members in root_members.values():
        # article_set: union of all articles mentioning any topic in this cluster
        art_idx: set[int] = set()
        for t in members:
            art_idx.update(topic_arts.get(t, []))

        cluster_name = max(members, key=lambda t: len(topic_arts.get(t, [])))
        pos = neg = neu = recent = 0
        top_cands: list[tuple[float, dict]] = []

        for idx in art_idx:
            a = articles[idx]
            label = a.get("sentiment_label", "neutral")
            if label == "positive":
                pos += 1
            elif label == "negative":
                neg += 1
            else:
                neu += 1
            if (a.get("collected_at") or "") >= cutoff_7d:
                recent += 1
            top_cands.append((abs(a.get("sentiment_score") or 0.5), a))

        total = len(art_idx)
        net_pct = round((pos - neg) / total * 100) if total else 0
        trend = "rising" if total > 0 and recent / total > 0.5 else "stable"
        top_arts = [
            {"title": a.get("title", ""), "url": a.get("url", ""),
             "sentiment_label": a.get("sentiment_label", "neutral")}
            for _, a in sorted(top_cands, reverse=True)[:3]
        ]
        clusters.append({
            "cluster_name": cluster_name,
            "article_count": total,
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "net_sentiment_pct": net_pct,
            "trend": trend,
            "top_articles": top_arts,
        })

    clusters.sort(key=lambda c: c["article_count"], reverse=True)
    return clusters[:10]


@router.get("/issue-clusters/{brand_id}", response_model=IssueClustersResponse)
def get_issue_clusters(
    brand_id: str,
    days: int = Query(30, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    articles = get_articles(brand_id, limit=2000, date_from=cutoff)
    raw = _build_clusters(articles, cutoff_7d)
    return IssueClustersResponse(
        clusters=[IssueCluster(
            cluster_name=c["cluster_name"],
            article_count=c["article_count"],
            positive_count=c["positive_count"],
            negative_count=c["negative_count"],
            neutral_count=c["neutral_count"],
            net_sentiment_pct=c["net_sentiment_pct"],
            trend=c["trend"],
            top_articles=[ClusterArticle(**a) for a in c["top_articles"]],
        ) for c in raw],
        period_days=days,
        brand_id=brand_id,
    )


# ── Editorial Tone Breakdown (Phase 1) ────────────────────────────────────────

@router.get("/tone-breakdown/{brand_id}", response_model=ToneBreakdownResponse)
def get_tone_breakdown(
    brand_id: str,
    days: int = Query(30, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    articles = get_articles(brand_id, limit=2000, date_from=cutoff)

    tone_keys = ("factual", "positive_frame", "negative_frame", "critical")
    total: dict[str, int] = {k: 0 for k in tone_keys}
    week_counts: dict[str, dict[str, int]] = {}

    for a in articles:
        tone = (a.get("editorial_tone") or "").strip()
        if tone not in tone_keys:
            continue
        total[tone] += 1
        collected = a.get("collected_at") or a.get("published_at") or ""
        try:
            dt = datetime.fromisoformat(collected.replace("Z", "+00:00"))
            week_label = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
        except Exception:
            continue
        bucket = week_counts.setdefault(week_label, {k: 0 for k in tone_keys})
        bucket[tone] += 1

    # Return last 8 weeks, sorted chronologically
    sorted_weeks = sorted(week_counts.keys())[-8:]
    weekly_trend = [
        ToneWeek(
            week=w,
            factual=week_counts[w]["factual"],
            positive_frame=week_counts[w]["positive_frame"],
            negative_frame=week_counts[w]["negative_frame"],
            critical=week_counts[w]["critical"],
        )
        for w in sorted_weeks
    ]

    return ToneBreakdownResponse(
        total=total,
        weekly_trend=weekly_trend,
        period_days=days,
        brand_id=brand_id,
    )


# ── Sentiment Divergence Summary (Phase 1) ────────────────────────────────────

@router.get("/divergence-summary/{brand_id}", response_model=DivergenceSummaryResponse)
def get_divergence_summary(
    brand_id: str,
    days: int = Query(14, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    all_articles = get_articles(brand_id, limit=2000, date_from=cutoff)
    total = len(all_articles)

    divergent = [
        a for a in all_articles
        if a.get("sentiment_divergence")
        and a.get("headline_sentiment_score") is not None
        and a.get("body_sentiment_score") is not None
    ]

    # Sort by abs diff descending
    divergent.sort(
        key=lambda a: abs((a.get("headline_sentiment_score") or 0) - (a.get("body_sentiment_score") or 0)),
        reverse=True,
    )

    divergent_pct = round(len(divergent) / total * 100, 1) if total else 0.0

    return DivergenceSummaryResponse(
        total_divergent_count=len(divergent),
        divergent_pct=divergent_pct,
        articles=[
            DivergentArticle(
                title=a.get("title") or "",
                url=a.get("url") or "",
                published_at=a.get("published_at"),
                headline_sentiment_score=float(a.get("headline_sentiment_score") or 0),
                body_sentiment_score=float(a.get("body_sentiment_score") or 0),
                sentiment_label=a.get("sentiment_label") or "neutral",
            )
            for a in divergent[:10]
        ],
        period_days=days,
    )


# ── Journalist Coverage ────────────────────────────────────────────────────────

@router.get("/journalist-coverage/{brand_id}", response_model=JournalistCoverageResponse)
def get_journalist_coverage(
    brand_id: str,
    days: int = Query(90, ge=1, le=180),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    articles = get_articles(brand_id, limit=5000, date_from=cutoff)

    # Group by author
    author_map: dict[str, list[dict]] = {}
    for a in articles:
        author = (a.get("author") or "").strip()
        if not author:
            continue
        author_map.setdefault(author, []).append(a)

    profiles: list[JournalistProfile] = []
    for author, arts in author_map.items():
        total = len(arts)
        neg = sum(1 for a in arts if a.get("sentiment_label") == "negative")
        pos = sum(1 for a in arts if a.get("sentiment_label") == "positive")
        neu = total - neg - pos
        neg_pct = round(neg / total * 100, 1)
        last_at = max((a.get("published_at") or a.get("collected_at") or "") for a in arts)

        recent = sorted(
            arts,
            key=lambda a: a.get("published_at") or a.get("collected_at") or "",
            reverse=True,
        )[:3]

        profiles.append(JournalistProfile(
            author=author,
            total_articles=total,
            negative_count=neg,
            positive_count=pos,
            neutral_count=neu,
            negative_pct=neg_pct,
            last_article_at=last_at,
            recent_articles=[
                JournalistArticle(
                    title=a.get("title") or "",
                    url=a.get("url") or "",
                    published_at=a.get("published_at") or a.get("collected_at") or "",
                    sentiment_label=a.get("sentiment_label") or "neutral",
                )
                for a in recent
            ],
        ))

    profiles.sort(key=lambda p: p.negative_count, reverse=True)
    return JournalistCoverageResponse(
        journalists=profiles[:20],
        period_days=days,
        brand_id=brand_id,
    )


# ── YouTube Creator vs Audience Sentiment Split ───────────────────────────────

@router.get("/youtube-sentiment-split/{brand_id}", response_model=YTSentimentSplitResponse)
def get_youtube_sentiment_split(
    brand_id: str,
    days: int = Query(30, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    rows = (
        db.table("articles")
        .select("title, url, portal_id, portal_name, sentiment_label, sentiment_score, source_type")
        .eq("brand_id", brand_id)
        .in_("source_type", ["youtube_video", "youtube_comment"])
        .gte("collected_at", cutoff)
        .execute()
        .data
    ) or []

    videos   = [r for r in rows if r.get("source_type") == "youtube_video"]
    comments = [r for r in rows if r.get("source_type") == "youtube_comment"]

    def _bucket(items: list[dict]) -> YTSentimentBucket:
        pos = sum(1 for r in items if r.get("sentiment_label") == "positive")
        neg = sum(1 for r in items if r.get("sentiment_label") == "negative")
        neu = sum(1 for r in items if r.get("sentiment_label") == "neutral")
        total = len(items) or 1
        avg = sum(float(r.get("sentiment_score") or 0) for r in items) / total
        return YTSentimentBucket(positive=pos, neutral=neu, negative=neg,
                                  total=len(items), avg_score=round(avg, 3))

    creator_bucket  = _bucket(videos)
    audience_bucket = _bucket(comments)

    # Group comments by portal_id to find divergent videos
    from collections import defaultdict
    comments_by_portal: dict[str, list[str]] = defaultdict(list)
    for c in comments:
        pid = c.get("portal_id") or ""
        if pid:
            comments_by_portal[pid].append(c.get("sentiment_label", "neutral"))

    divergent: list[YTDivergentVideo] = []
    for v in videos:
        pid = v.get("portal_id") or ""
        comment_labels = comments_by_portal.get(pid, [])
        if not comment_labels:
            continue
        audience_majority = Counter(comment_labels).most_common(1)[0][0]
        creator_label = v.get("sentiment_label", "neutral")
        if creator_label != audience_majority:
            divergent.append(YTDivergentVideo(
                title=v.get("title", "")[:120],
                url=v.get("url", ""),
                portal_name=v.get("portal_name", ""),
                creator_label=creator_label,
                audience_label=audience_majority,
                comment_count=len(comment_labels),
            ))

    divergent.sort(key=lambda d: d.comment_count, reverse=True)

    return YTSentimentSplitResponse(
        creator=creator_bucket,
        audience=audience_bucket,
        divergent_videos=divergent[:5],
        period_days=days,
        brand_id=brand_id,
    )


# ── Issue Category Breakdown ──────────────────────────────────────────────────

@router.get("/issue-categories/{brand_id}", response_model=IssueCategoriesResponse)
def get_issue_categories(
    brand_id: str,
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    db = get_db()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = (
        db.table("articles")
        .select("issue_category, sentiment_label")
        .eq("brand_id", brand_id)
        .gte("published_at", since)
        .not_.is_("issue_category", "null")
        .execute()
        .data
    ) or []

    counts: dict[str, dict] = {}
    for r in rows:
        cat = r.get("issue_category") or "other"
        if cat == "other":
            continue
        label = r.get("sentiment_label", "neutral")
        if cat not in counts:
            counts[cat] = {"count": 0, "positive_count": 0, "negative_count": 0}
        counts[cat]["count"] += 1
        if label == "positive":
            counts[cat]["positive_count"] += 1
        elif label == "negative":
            counts[cat]["negative_count"] += 1

    categories = [
        IssueCategoryItem(category=cat, **vals)
        for cat, vals in sorted(counts.items(), key=lambda x: -x[1]["count"])
    ]
    return IssueCategoriesResponse(categories=categories, period_days=days, brand_id=brand_id)
