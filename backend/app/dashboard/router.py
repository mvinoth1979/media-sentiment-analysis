import csv
import io
import json as _json
import logging
import re
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

log = logging.getLogger(__name__)
from app.auth.dependencies import require_brand_role, require_role, READ_ROLES, WRITE_ROLES
from app.config import settings
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
from app.pipeline.virality_detector import compute_virality_flags
from app.dashboard.schemas import (
    OverviewResponse, KPISummary, ArticleItem, AuthorInfo, MentionMetrics,
    SourceStat, TopicStat, StateStat, TrendPoint, SourceTypeStat,
    InfluentialSource, TopSourcesResponse, BrandAdvocate, TopAdvocatesResponse,
    BrandSentimentEntry, CompetitorSentimentResponse,
    Annotation, AnnotationCreate, DeleteMentionsRequest, PipelineStats,
    SentimentTrendPoint, SentimentTrendResponse,
    SourceCategoryPoint, SourceCategoriesResponse,
    HeadlineItem, HeadlinesResponse,
    ReviewSummaryResponse, ReviewStarBucket, TopicTheme,
    ReviewPlatformStat, ReviewSitesBreakdownResponse,
    SoVEntry, CompetitorSoVResponse, CompetitorDiscoveryResponse,
    ClusterArticle, IssueCluster, IssueClustersResponse,
    ToneWeek, ToneBreakdownResponse,
    DivergentArticle, DivergenceSummaryResponse,
    JournalistArticle, JournalistProfile, JournalistCoverageResponse,
    YTSentimentBucket, YTDivergentVideo, YTSentimentSplitResponse,
    IssueCategoryItem, IssueCategoriesResponse,
    ReviewQueueItem, ReviewQueueResponse, ReviewQueuePatchRequest,
    VideoRiskItem, BrandRiskScoresResponse,
    AISummaryResponse,
    ViralityFlag, ViralityAlertsResponse,
    ExplainRequest, ExplainResponse,
    ChatMessage, ChatRequest,
    MorningBriefResponse,
    StateHighlight, RegionalSummaryResponse,
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
    days: int = Query(7, ge=1, le=365),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    now = datetime.now(timezone.utc)
    if date_from:
        current_start = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        current_end = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else now
        span = current_end - current_start
        previous_start = current_start - span
    else:
        current_start = now - timedelta(days=days)
        current_end = now
        previous_start = now - timedelta(days=days * 2)

    trend_days = max(1, int((current_end - current_start).days))

    kpi_raw = get_kpi_summary(brand_id)
    try:
        trend_raw = query_sentiment_trend(brand_id, trend_days)
    except Exception:
        trend_raw = []
    recent = get_articles(brand_id, limit=10, date_from=current_start.isoformat(), date_to=current_end.isoformat())

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

    all_articles = get_articles(brand_id, limit=500, date_from=current_start.isoformat(), date_to=current_end.isoformat())
    for a in all_articles:
        kw_counter.update(a.get("keywords", []))
        topic_counter.update(a.get("topics", []))

    current_window = _window_kpi(brand_id, current_start.isoformat(), current_end.isoformat())
    previous_window = _window_kpi(brand_id, previous_start.isoformat(), current_start.isoformat())
    wow_delta = _compute_wow_delta(current_window, previous_window)

    pipeline_info = get_pipeline_info(brand_id)
    raw_stats = pipeline_info.get("pipeline_last_stats") or {}

    previous_articles = get_articles(brand_id, limit=500, date_from=previous_start.isoformat(), date_to=current_start.isoformat())
    by_source_type = _compute_by_source_type(all_articles, previous_articles)

    total_reach = sum(int(a.get("reach_score") or 0) for a in all_articles) * 1000

    return OverviewResponse(
        kpi=KPISummary(perception_score=recent_score, total_reach=total_reach, **kpi_raw, **wow_delta),
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
        by_source_type=by_source_type,
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


_SOURCE_TYPE_CATEGORY: dict[str, str] = {
    "news": "news", "rss": "news",
    "youtube_video": "youtube", "youtube_comment": "youtube",
    "blog": "blog", "portal": "blog",
    "google_review":      "review_site",
    "trustpilot_review":  "review_site",
    "mouthshut_review":   "review_site",
    "justdial_review":    "review_site",
    "ambitionbox_review":  "review_site",
    "tripadvisor_review":  "review_site",
    "team_bhp_review":     "review_site",
    "amazon_review":       "review_site",
    "flipkart_review":     "review_site",
    "glassdoor_review":    "review_site",
    "indiamart_review":    "review_site",
    "play_store_review":   "review_site",
    "reddit_post": "reddit_post", "reddit_comment": "reddit_post", "forum": "reddit_post",
}
_SOURCE_CATEGORIES = ("news", "youtube", "blog", "review_site", "reddit_post")


def _compute_by_source_type(
    current: list[dict],
    previous: list[dict],
) -> dict[str, SourceTypeStat]:
    def _cat(a: dict) -> str:
        return _SOURCE_TYPE_CATEGORY.get(a.get("source_type") or "", "news")

    curr_map: dict[str, list[dict]] = {c: [] for c in _SOURCE_CATEGORIES}
    prev_map: dict[str, list[dict]] = {c: [] for c in _SOURCE_CATEGORIES}
    for a in current:
        curr_map[_cat(a)].append(a)
    for a in previous:
        prev_map[_cat(a)].append(a)

    result: dict[str, SourceTypeStat] = {}
    for cat in _SOURCE_CATEGORIES:
        curr_arts = curr_map[cat]
        prev_arts = prev_map[cat]
        count = len(curr_arts)
        prev_count = len(prev_arts)
        neg = sum(1 for a in curr_arts if a.get("sentiment_label") == "negative")
        neg_pct = round(neg / count * 100, 1) if count else 0.0
        delta_pct = round((count - prev_count) / prev_count * 100, 1) if prev_count else None
        avg_rating: float | None = None
        if cat == "review_site" and count:
            score_sum = sum(float(a.get("sentiment_score") or 0) for a in curr_arts)
            avg_score = score_sum / count
            avg_rating = round((avg_score + 1) / 2 * 4 + 1, 1)
        result[cat] = SourceTypeStat(
            count=count,
            delta_pct=delta_pct,
            negative_pct=neg_pct,
            avg_rating=avg_rating,
        )
    return result


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
    issue_category: str | None = None,
    source_category: str | None = None,
    entity: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    articles = get_articles(brand_id, limit=limit, offset=offset,
                            sentiment=sentiment, language=language,
                            portal_id=portal_id, topic=topic, state=state,
                            source_type=source_type,
                            date_from=date_from, date_to=date_to, q=q,
                            editorial_tone=editorial_tone,
                            issue_category=issue_category,
                            source_category=source_category,
                            entity=entity)
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
    articles = get_articles(brand_id, limit=2000, date_from=date_from, date_to=date_to,
                            source_category="review_site")
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


_REVIEW_PLATFORM_NAMES: dict[str, str] = {
    "google_review":     "Google Reviews",
    "trustpilot_review": "Trustpilot",
    "mouthshut_review":  "MouthShut",
    "justdial_review":   "JustDial",
    "ambitionbox_review": "AmbitionBox",
    "tripadvisor_review": "TripAdvisor",
    "team_bhp_review":   "Team-BHP",
    "amazon_review":     "Amazon",
    "flipkart_review":   "Flipkart",
    "glassdoor_review":  "Glassdoor",
    "indiamart_review":   "IndiaMART",
    "play_store_review":  "Google Play Store",
}


@router.get("/review-sites-breakdown/{brand_id}", response_model=ReviewSitesBreakdownResponse)
def get_review_sites_breakdown(
    brand_id: str,
    days: int = Query(30, ge=1, le=365),
    date_from: str | None = None,
    date_to: str | None = None,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    now = datetime.now(timezone.utc)
    if date_from:
        df = date_from
        dt = date_to or now.isoformat()
    else:
        df = (now - timedelta(days=days)).isoformat()
        dt = now.isoformat()

    articles = get_articles(
        brand_id, limit=2000,
        date_from=df, date_to=dt,
        source_category="review_site",
    )

    platform_map: dict[str, list[dict]] = {}
    for a in articles:
        st = a.get("source_type") or "unknown"
        platform_map.setdefault(st, []).append(a)

    platforms: list[ReviewPlatformStat] = []
    for source_type, arts in sorted(platform_map.items(), key=lambda x: -len(x[1])):
        count = len(arts)
        pos = sum(1 for a in arts if a.get("sentiment_label") == "positive")
        neg = sum(1 for a in arts if a.get("sentiment_label") == "negative")
        neu = count - pos - neg

        score_sum = sum(float(a.get("sentiment_score") or 0) for a in arts)
        avg_score = score_sum / count if count else 0.0
        avg_rating = round((avg_score + 1) / 2 * 4 + 1, 1)

        # Up to 3 recent review snippets (body first 120 chars)
        recent = sorted(arts, key=lambda a: a.get("published_at") or "", reverse=True)[:3]
        snippets = [
            (a.get("body") or a.get("title") or "")[:120].strip()
            for a in recent if (a.get("body") or a.get("title"))
        ]

        platforms.append(ReviewPlatformStat(
            source_type=source_type,
            platform_name=_REVIEW_PLATFORM_NAMES.get(source_type, source_type.replace("_", " ").title()),
            count=count,
            avg_rating=avg_rating,
            positive_count=pos,
            negative_count=neg,
            neutral_count=neu,
            positive_pct=round(pos / count * 100, 1) if count else 0.0,
            negative_pct=round(neg / count * 100, 1) if count else 0.0,
            recent_snippets=snippets,
        ))

    total = sum(p.count for p in platforms)
    overall_avg: float | None = None
    if total:
        score_sum = sum(float(a.get("sentiment_score") or 0) for a in articles)
        avg_s = score_sum / total
        overall_avg = round((avg_s + 1) / 2 * 4 + 1, 1)

    return ReviewSitesBreakdownResponse(
        platforms=platforms,
        total_reviews=total,
        overall_avg_rating=overall_avg,
        brand_id=brand_id,
        period_days=days,
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


def _build_clusters(articles: list[dict], cutoff_7d: str) -> list[dict]:
    """Group articles into issue clusters by issue_category.

    Uses issue_category (always an English taxonomy label, always populated)
    as the primary grouping key. This is more reliable than the previous
    topics co-occurrence approach, which broke for non-English articles where
    LLMs returned topics in the article language instead of the English taxonomy.
    """
    cat_map: dict[str, list[dict]] = {}
    for a in articles:
        cat = (a.get("issue_category") or "other").strip() or "other"
        cat_map.setdefault(cat, []).append(a)

    if not cat_map:
        return []

    clusters: list[dict] = []
    for cat, arts in cat_map.items():
        pos = neg = neu = recent = 0
        top_cands: list[tuple[float, dict]] = []
        for a in arts:
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

        total = len(arts)
        net_pct = round((pos - neg) / total * 100) if total else 0
        trend = "rising" if total > 0 and recent / total > 0.5 else "stable"
        top_arts = [
            {"title": a.get("title", ""), "url": a.get("url", ""),
             "sentiment_label": a.get("sentiment_label", "neutral")}
            for _, a in sorted(top_cands, key=lambda x: x[0], reverse=True)[:3]
        ]
        clusters.append({
            "cluster_name": cat,
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


# ── Human Review Queue (Item 5) ───────────────────────────────────────────────

@router.get("/review-queue/{brand_id}", response_model=ReviewQueueResponse)
def get_review_queue(
    brand_id: str,
    status: str | None = Query(None, pattern="^(pending|approved|rejected)$"),
    user: dict = Depends(require_brand_role(*WRITE_ROLES)),
):
    """List review queue items for a brand. Both GET and PATCH require WRITE_ROLES."""
    db = get_db()
    query = (
        db.table("human_review_queue")
        .select("*")
        .eq("brand_id", brand_id)
    )
    if status:
        query = query.eq("status", status)
    rows = (
        query
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
    ) or []

    # Enrich with article title/url via a secondary lookup
    article_ids = [r["article_id"] for r in rows if r.get("article_id")]
    article_map: dict[str, dict] = {}
    if article_ids:
        art_rows = (
            db.table("articles")
            .select("id, title, url")
            .in_("id", article_ids)
            .execute()
            .data
        ) or []
        article_map = {a["id"]: a for a in art_rows}

    items = []
    for r in rows:
        art = article_map.get(r.get("article_id") or "")
        items.append(ReviewQueueItem(
            id=str(r["id"]),
            brand_id=str(r["brand_id"]),
            article_id=str(r["article_id"]),
            reason=r.get("reason") or "",
            status=r.get("status") or "pending",
            reviewer_id=r.get("reviewer_id"),
            reviewed_at=r.get("reviewed_at"),
            created_at=r.get("created_at"),
            article_title=art.get("title") if art else None,
            article_url=art.get("url") if art else None,
        ))

    return ReviewQueueResponse(items=items, total=len(items))


@router.patch("/review-queue/{item_id}")
def patch_review_queue_item(
    item_id: str,
    payload: ReviewQueuePatchRequest,
    user: dict = Depends(require_role(*WRITE_ROLES)),
):
    """Approve or reject a review queue item."""
    db = get_db()
    update_data: dict = {
        "status": payload.status,
        "reviewer_id": user.get("user_id"),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    result = (
        db.table("human_review_queue")
        .update(update_data)
        .eq("id", item_id)
        .execute()
    )
    rows = result.data or []
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Review queue item not found")
    return {"id": item_id, "status": payload.status}


# ── Per-video Brand Risk Score (Item 8) ───────────────────────────────────────

import math as _math


def _brand_risk_reach_tier(view_count: int) -> str:
    """Map view count to reach tier label per Item 8 spec."""
    if view_count > 1_000_000:
        return "Viral"
    if view_count >= 100_000:
        return "High"
    if view_count >= 10_000:
        return "Mid"
    return "Low"


def _compute_risk_score(
    sentiment_score: float,
    view_count: int,
    like_count: int,
    comment_count: int,
    days_old: int,
) -> float:
    """
    Per-video brand risk score formula (Item 8):

      risk = sentiment_score
             × log10(views+1) / log10(10_000_001)
             × (likes+comments) / max(views, 1) / 0.1
             × recency_decay

    recency_decay = exp(-days_old / 30)   (half-life ~30 days)
    Returns 0.0 when views == 0.
    """
    if view_count <= 0:
        return 0.0

    reach_factor = _math.log10(view_count + 1) / _math.log10(10_000_001)
    engagement_factor = (like_count + comment_count) / max(view_count, 1) / 0.1
    recency_decay = _math.exp(-days_old / 30.0)

    return sentiment_score * reach_factor * engagement_factor * recency_decay


@router.get("/brand-risk-scores/{brand_id}", response_model=BrandRiskScoresResponse)
def get_brand_risk_scores(
    brand_id: str,
    days: int = Query(30, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    """Top 10 YouTube videos by absolute risk score in the last {days} days."""
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    rows = (
        db.table("articles")
        .select(
            "id, title, url, portal_id, sentiment_score, published_at, collected_at, reach_metadata"
        )
        .eq("brand_id", brand_id)
        .in_("source_type", ["youtube_video"])
        .gte("collected_at", cutoff)
        .execute()
        .data
    ) or []

    now = datetime.now(timezone.utc)
    videos: list[VideoRiskItem] = []

    for r in rows:
        reach = r.get("reach_metadata") or {}
        view_count = int(reach.get("view_count") or 0)
        like_count = int(reach.get("like_count") or 0)
        comment_count = int(reach.get("comment_count") or 0)
        sentiment_score = float(r.get("sentiment_score") or 0.0)

        # Compute days_old from collected_at
        collected_str = r.get("collected_at") or r.get("published_at") or ""
        try:
            collected_dt = datetime.fromisoformat(collected_str.replace("Z", "+00:00"))
            days_old = max(0, (now - collected_dt).days)
        except Exception:
            days_old = 0

        risk_score = _compute_risk_score(
            sentiment_score=sentiment_score,
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            days_old=days_old,
        )

        videos.append(VideoRiskItem(
            article_id=str(r["id"]),
            title=r.get("title") or "",
            url=r.get("url") or "",
            portal_id=r.get("portal_id") or "",
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            sentiment_score=round(sentiment_score, 4),
            risk_score=round(risk_score, 4),
            reach_tier=_brand_risk_reach_tier(view_count),
            published_at=r.get("published_at"),
        ))

    # Sort by absolute risk score descending and keep top 10
    videos.sort(key=lambda v: abs(v.risk_score), reverse=True)
    return BrandRiskScoresResponse(videos=videos[:10], brand_id=brand_id, period_days=days)


# ── AI Executive Summary ──────────────────────────────────────────────────────

_AI_SUMMARY_CACHE: dict = {}
_AI_SUMMARY_TTL = 3600  # 1 hour


@router.get("/ai-summary/{brand_id}", response_model=AISummaryResponse)
def get_ai_summary(
    brand_id: str,
    days: int = Query(7, ge=1, le=90),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    cache_key = f"{brand_id}:{days}:{date_from}:{date_to}"
    now = time.time()
    if cache_key in _AI_SUMMARY_CACHE and _AI_SUMMARY_CACHE[cache_key]["expires_at"] > now:
        return AISummaryResponse(**_AI_SUMMARY_CACHE[cache_key]["data"])

    current_end = datetime.now(timezone.utc)
    if date_from:
        current_start = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        current_end = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else current_end
    else:
        current_start = current_end - timedelta(days=days)

    all_articles = get_articles(
        brand_id, limit=300,
        date_from=current_start.isoformat(),
        date_to=current_end.isoformat(),
    )

    db = get_db()
    brand_row = db.table("brands").select("name").eq("id", brand_id).execute().data
    brand_name = brand_row[0]["name"] if brand_row else "the brand"

    if not all_articles:
        result = {
            "what_changed": f"No media coverage collected for {brand_name} in this period.",
            "why": "The pipeline has not yet processed articles for the selected date range. Trigger a run to start collecting coverage.",
            "actions": ["Trigger a pipeline run from the admin panel", "Verify brand keywords are correctly configured", "Check that portal RSS feeds are accessible"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        _AI_SUMMARY_CACHE[cache_key] = {"data": result, "expires_at": now + _AI_SUMMARY_TTL}
        return AISummaryResponse(**result)

    total = len(all_articles)
    neg = sum(1 for a in all_articles if a.get("sentiment_label") == "negative")
    pos = sum(1 for a in all_articles if a.get("sentiment_label") == "positive")
    neu = total - neg - pos
    neg_pct = round(neg / total * 100, 1) if total else 0
    pos_pct = round(pos / total * 100, 1) if total else 0

    issue_counter: Counter = Counter(
        a.get("issue_category", "other")
        for a in all_articles
        if a.get("issue_category") and a.get("issue_category") != "other"
    )
    top_issues = [cat.replace("_", " ") for cat, _ in issue_counter.most_common(3)]

    # Top negative + positive articles by reach
    neg_articles = sorted(
        [a for a in all_articles if a.get("sentiment_label") == "negative"],
        key=lambda a: a.get("reach_score") or 0,
        reverse=True,
    )[:3]
    pos_articles = sorted(
        [a for a in all_articles if a.get("sentiment_label") == "positive"],
        key=lambda a: a.get("reach_score") or 0,
        reverse=True,
    )[:2]
    neg_headlines = [a.get("title", "")[:90] for a in neg_articles if a.get("title")]
    pos_headlines = [a.get("title", "")[:90] for a in pos_articles if a.get("title")]

    # Source type breakdown
    source_counter: Counter = Counter(
        a.get("source_type", "news") for a in all_articles
    )
    source_summary = ", ".join(
        f"{k.replace('_', ' ')} ({v})"
        for k, v in source_counter.most_common(4)
    )

    # Regulatory + critical tone flags
    reg_count = sum(1 for a in all_articles if a.get("is_regulatory_source"))
    critical_count = sum(1 for a in all_articles if a.get("editorial_tone") in ("critical", "negative_frame"))

    neg_block = "\n".join(f"  • {h}" for h in neg_headlines) if neg_headlines else "  • none"
    pos_block = "\n".join(f"  • {h}" for h in pos_headlines) if pos_headlines else "  • none"

    prompt = (
        f"You are a senior brand reputation analyst writing a concise executive briefing for the CMO.\n"
        f"Brand: {brand_name} | Period: last {days} days\n\n"
        f"Coverage snapshot:\n"
        f"  Total articles: {total} | Positive: {pos} ({pos_pct}%) | Negative: {neg} ({neg_pct}%) | Neutral: {neu}\n"
        f"  Top issue categories: {', '.join(top_issues) if top_issues else 'general coverage'}\n"
        f"  Sources: {source_summary}\n"
        + (f"  Regulatory/government sources flagged: {reg_count}\n" if reg_count else "")
        + (f"  Critical/negative-framed editorial tone: {critical_count} articles\n" if critical_count else "")
        + f"\nHighest-reach negative coverage:\n{neg_block}\n"
        + f"\nTop positive signals:\n{pos_block}\n\n"
        "Write a tight 3-part executive briefing. Be specific — name actual issues, sources, or patterns from the data above. "
        "Respond in JSON only — no markdown, no preamble:\n"
        '{"what_changed": "1-2 sentences on the dominant trend or risk — be specific, cite the issue category or a headline.", '
        '"why": "1 sentence on the root cause or context driving this trend.", '
        '"actions": ["Specific action referencing a named issue or source (max 10 words)", '
        '"Second specific action", "Third specific action"]}'
    )

    # Try LLM — paid key first, then free key with lighter model
    _AI_SUMMARY_ATTEMPTS = [
        (settings.gemini_api_key,      settings.gemini_model or "gemini-2.5-flash"),
        (settings.gemini_free_api_key, "gemini-2.0-flash"),
        (settings.gemini_free_api_key, "gemini-1.5-flash"),
    ]
    from app.nlp.gemini_handler import _strip_fences
    from google import genai as _genai
    for _api_key, _model in _AI_SUMMARY_ATTEMPTS:
        if not _api_key:
            continue
        try:
            _client = _genai.Client(api_key=_api_key, http_options={"timeout": 10})
            response = _client.models.generate_content(model=_model, contents=prompt)
            raw = _strip_fences(response.text.strip())
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                continue
            parsed = _json.loads(match.group())
            result = {
                "what_changed": str(parsed.get("what_changed", "")).strip() or f"Negative sentiment at {neg_pct}% of {total} articles.",
                "why": str(parsed.get("why", "")).strip() or f"Coverage driven by {top_issues[0] if top_issues else 'general news'}.",
                "actions": [str(a).strip() for a in parsed.get("actions", []) if a][:3] or ["Review coverage", "Monitor trends", "Engage stakeholders"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            _AI_SUMMARY_CACHE[cache_key] = {"data": result, "expires_at": now + _AI_SUMMARY_TTL}
            return AISummaryResponse(**result)
        except Exception as e:
            err = str(e)
            if "RESOURCE_EXHAUSTED" in err or "429" in err:
                log.warning("AI summary: %s quota exhausted, trying next", _model)
                continue
            if "404" in err:
                continue
            if "timeout" in err.lower() or "deadline" in err.lower() or "timed out" in err.lower():
                log.warning("AI summary: %s timed out, trying next", _model)
                continue
            log.warning("AI summary LLM error (%s): %s", _model, err[:150])
            break

    # Fallback: data-driven summary without LLM
    if neg_pct > 35:
        situation = f"{brand_name} faces elevated negative coverage — {neg_pct}% of {total} articles carry negative sentiment over the last {days} days."
    elif neg_pct > 20:
        situation = f"{brand_name}'s sentiment is mixed at {neg_pct}% negative across {total} articles — {top_issues[0].title() if top_issues else 'key issues'} is the primary concern."
    else:
        situation = f"{brand_name} coverage is largely positive ({pos_pct}%) across {total} articles. {top_issues[0].title() if top_issues else 'Brand visibility'} is the most active topic."
    root_cause = (
        f"Coverage concentrated in {', '.join(top_issues[:2]) if top_issues else 'general news'}."
        + (f" {reg_count} regulatory source mention{'s' if reg_count != 1 else ''} detected." if reg_count else "")
    )
    result = {
        "what_changed": situation,
        "why": root_cause,
        "actions": [
            f"Review top negative {top_issues[0] if top_issues else 'coverage'} articles by reach",
            f"Engage proactively on {top_issues[1].title() if len(top_issues) > 1 else (top_issues[0].title() if top_issues else 'key concerns')}",
            "Monitor daily for escalation — set alert threshold at 35% negative",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _AI_SUMMARY_CACHE[cache_key] = {"data": result, "expires_at": now + _AI_SUMMARY_TTL}
    return AISummaryResponse(**result)


# ── AI Explainer ─────────────────────────────────────────────────────────────

_EXPLAIN_CACHE: dict = {}
_EXPLAIN_TTL   = 30 * 60   # 30 minutes

_METRIC_PROMPTS = {
    "reputation_score": (
        "Explain in 2-3 sentences why this brand's reputation score is {value}/100. "
        "Identify the 3 specific root causes from the coverage data. "
        "Name actual issue categories, source types, or article patterns — not generic statements."
    ),
    "mention_growth": (
        "Explain why mention volume changed recently for this brand. "
        "Identify what event, source, or content type is driving the change. "
        "Be specific about timing, source, and topic."
    ),
    "risk_score": (
        "Explain why this brand's reputation risk score is elevated. "
        "Identify the 3 specific risk signals from the articles: source type, issue category, velocity. "
        "Name the dominant negative driver."
    ),
    "state_sentiment": (
        "Explain why {state} has this sentiment pattern for this brand. "
        "Identify what specific sources, channels, or topics are driving regional coverage. "
        "Name TV, YouTube, or news portals if visible in the data."
    ),
    "executive_summary": (
        "Generate a 2-sentence executive briefing headline for this brand's current media situation. "
        "Then identify the 3 key drivers. Be specific — cite issue categories and source types."
    ),
    "investigation_context": (
        "Explain why this topic/query is generating coverage for this brand. "
        "Identify the causal chain: what triggered it, who amplified it, and what type of content is driving it. "
        "Context: {extra_context}"
    ),
    "board_recommendation": (
        "Based on this brand's current media coverage, generate a single high-priority recommended action for leadership. "
        "Make it specific, time-bound, and actionable. Include a confidence assessment."
    ),
}

_EXPLAIN_SYSTEM = (
    "You are a media intelligence analyst. Brand: {brand_name}. Period: last {days} days.\n"
    "Coverage: {total} articles — {pos_pct}% positive, {neg_pct}% negative, {neu_pct}% neutral.\n"
    "Top issues: {top_issues}. Top sources: {top_sources}.\n"
    "Highest-reach negatives: {neg_headlines}.\n\n"
    "{metric_prompt}\n\n"
    "Respond ONLY in valid JSON — no markdown:\n"
    '{{"headline": "<1 sentence, specific>", '
    '"drivers": ["<specific driver 1>", "<specific driver 2>", "<specific driver 3>"], '
    '"evidence": ["<article title or source>", "<article title or source>"], '
    '"suggested_action": "<1 concrete action, max 15 words>", '
    '"drill_tab": "<A|B|C>"}}'
)


@router.post("/explain", response_model=ExplainResponse)
def explain_metric(
    req: ExplainRequest,
    days: int = Query(7, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    import html as _html

    # sanitise user-supplied strings before embedding in prompts
    safe_metric  = _html.escape(str(req.metric))[:80]
    safe_context = {k: _html.escape(str(v))[:200] for k, v in (req.context or {}).items()}

    cache_key = f"explain:{req.brand_id}:{safe_metric}:{req.date_from}:{req.date_to}:{str(sorted(safe_context.items()))}"
    now = time.time()
    if cache_key in _EXPLAIN_CACHE and _EXPLAIN_CACHE[cache_key]["expires_at"] > now:
        return ExplainResponse(**_EXPLAIN_CACHE[cache_key]["data"])

    # date window
    current_end = datetime.now(timezone.utc)
    if req.date_from:
        current_start = datetime.fromisoformat(req.date_from.replace("Z", "+00:00"))
        current_end   = datetime.fromisoformat(req.date_to.replace("Z", "+00:00")) if req.date_to else current_end
    else:
        current_start = current_end - timedelta(days=days)

    # fetch articles for context
    articles = get_articles(
        req.brand_id, limit=200,
        date_from=current_start.isoformat(),
        date_to=current_end.isoformat(),
    )

    # brand name
    db = get_db()
    brand_row = db.table("brands").select("name").eq("id", req.brand_id).execute().data
    brand_name = brand_row[0]["name"] if brand_row else "the brand"

    total = len(articles)

    # ── Confidence computation ─────────────────────────────────────────────────
    recent_cutoff = (current_end - timedelta(days=3)).isoformat()
    recent_count  = sum(1 for a in articles if (a.get("published_at") or "") >= recent_cutoff)
    unique_sources = len({a.get("portal_id") for a in articles if a.get("portal_id")})

    base_conf      = min(total / 20.0, 1.0)
    recency_factor = recent_count / max(total, 1)
    source_div     = min(unique_sources / 10.0, 1.0)
    confidence_pct = round((base_conf * 0.5 + recency_factor * 0.3 + source_div * 0.2) * 100)
    confidence_lbl = "high" if confidence_pct >= 70 else "medium" if confidence_pct >= 40 else "low"

    # ── fallback when no articles ─────────────────────────────────────────────
    if not articles:
        result = {
            "headline": f"No coverage data available for {brand_name} in this period.",
            "drivers": ["No articles collected", "Pipeline may not have run", "Check brand keyword configuration"],
            "evidence": [],
            "confidence": "low",
            "confidence_pct": 0,
            "suggested_action": "Trigger a pipeline run and verify brand keywords.",
            "drill_tab": "A",
        }
        _EXPLAIN_CACHE[cache_key] = {"data": result, "expires_at": now + _EXPLAIN_TTL}
        return ExplainResponse(**result)

    # ── Build context stats ───────────────────────────────────────────────────
    neg  = sum(1 for a in articles if a.get("sentiment_label") == "negative")
    pos  = sum(1 for a in articles if a.get("sentiment_label") == "positive")
    neu  = total - neg - pos
    neg_pct = round(neg / total * 100, 1) if total else 0
    pos_pct = round(pos / total * 100, 1) if total else 0
    neu_pct = round(100 - neg_pct - pos_pct, 1)

    issue_ctr: Counter = Counter(
        a.get("issue_category", "other") for a in articles
        if a.get("issue_category") and a.get("issue_category") != "other"
    )
    top_issues_str = ", ".join(c.replace("_", " ") for c, _ in issue_ctr.most_common(3)) or "general coverage"

    source_ctr: Counter = Counter(a.get("source_type", "news") for a in articles)
    top_sources_str = ", ".join(f"{k}({v})" for k, v in source_ctr.most_common(3))

    neg_arts = sorted(
        [a for a in articles if a.get("sentiment_label") == "negative"],
        key=lambda a: a.get("reach_score") or 0, reverse=True,
    )[:3]
    neg_headlines_str = "; ".join(a.get("title", "")[:80] for a in neg_arts if a.get("title")) or "none"

    # ── Build metric-specific prompt ──────────────────────────────────────────
    metric_tmpl = _METRIC_PROMPTS.get(safe_metric, _METRIC_PROMPTS["executive_summary"])
    metric_prompt = metric_tmpl.format(
        value=req.value or "",
        state=safe_context.get("state", "this region"),
        extra_context=str(safe_context),
    )

    prompt = _EXPLAIN_SYSTEM.format(
        brand_name=brand_name,
        days=days,
        total=total,
        pos_pct=pos_pct,
        neg_pct=neg_pct,
        neu_pct=neu_pct,
        top_issues=top_issues_str,
        top_sources=top_sources_str,
        neg_headlines=neg_headlines_str,
        metric_prompt=metric_prompt,
    )

    # ── LLM call (same pattern as ai-summary) ─────────────────────────────────
    _ATTEMPTS = [
        (settings.gemini_api_key,      settings.gemini_model or "gemini-2.5-flash"),
        (settings.gemini_free_api_key, "gemini-2.0-flash"),
        (settings.gemini_free_api_key, "gemini-1.5-flash"),
    ]
    from app.nlp.gemini_handler import _strip_fences
    from google import genai as _genai

    parsed: dict | None = None
    for _api_key, _model in _ATTEMPTS:
        if not _api_key:
            continue
        try:
            _client = _genai.Client(api_key=_api_key, http_options={"timeout": 12})
            resp    = _client.models.generate_content(model=_model, contents=prompt)
            raw     = _strip_fences(resp.text.strip())
            match   = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                continue
            parsed = _json.loads(match.group())
            break
        except Exception as e:
            err = str(e)
            if "RESOURCE_EXHAUSTED" in err or "429" in err:
                continue
            if "404" in err or "timeout" in err.lower() or "deadline" in err.lower():
                continue
            log.warning("Explain LLM error (%s): %s", _model, err[:150])
            break

    # ── Assemble response (with LLM output or data-driven fallback) ───────────
    if parsed:
        drivers  = [str(d).strip() for d in parsed.get("drivers", []) if d][:5]
        evidence = [str(e).strip() for e in parsed.get("evidence", []) if e][:5]
        headline = str(parsed.get("headline", "")).strip()
        action   = str(parsed.get("suggested_action", "")).strip()
        tab      = str(parsed.get("drill_tab", "A")).strip()
        tab      = tab if tab in {"A", "B", "C"} else "A"
    else:
        # Data-driven fallback — no LLM
        headline = f"{neg_pct}% negative across {total} articles. Top issue: {issue_ctr.most_common(1)[0][0].replace('_', ' ') if issue_ctr else 'general coverage'}."
        drivers  = [
            f"Negative: {neg_pct}% of {total} articles",
            f"Top issues: {top_issues_str}",
            f"Sources: {top_sources_str}",
        ]
        evidence = [a.get("title", "")[:80] for a in neg_arts[:2] if a.get("title")]
        action   = "Review the top negative articles and assess escalation risk."
        tab      = "B"

    result = {
        "headline":         headline or f"Coverage analysis for {brand_name}.",
        "drivers":          drivers or ["Insufficient data for detailed analysis"],
        "evidence":         evidence,
        "confidence":       confidence_lbl,
        "confidence_pct":   confidence_pct,
        "suggested_action": action or "Monitor brand coverage daily.",
        "drill_tab":        tab,
    }
    _EXPLAIN_CACHE[cache_key] = {"data": result, "expires_at": now + _EXPLAIN_TTL}
    return ExplainResponse(**result)


# ── Screen 2: Top Influential Sources ──────────────────────────────────────────

@router.get("/top-sources/{brand_id}", response_model=TopSourcesResponse)
def get_top_sources_endpoint(
    brand_id: str,
    days: int = Query(30),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    from collections import defaultdict
    current_end = datetime.utcnow()
    current_start = current_end - timedelta(days=days)
    articles = get_articles(brand_id, limit=500, date_from=current_start.isoformat(), date_to=current_end.isoformat())

    stats: dict = defaultdict(lambda: {"name": "", "total_reach": 0.0, "scores": [], "credibilities": [], "counts": {}})
    for a in articles:
        pid = a.get("portal_id", "unknown")
        reach_meta = a.get("reach_metadata") or {}
        reach = float(reach_meta.get("estimated_reach", 1)) if isinstance(reach_meta, dict) else 1.0
        score = abs(float(a.get("sentiment_score") or 0))
        cred = float(a.get("source_credibility") or 0.5)
        sent = a.get("sentiment_label") or "neutral"

        s = stats[pid]
        s["name"] = a.get("portal_name") or pid
        s["total_reach"] += reach
        s["scores"].append(score)
        s["credibilities"].append(cred)
        s["counts"][sent] = s["counts"].get(sent, 0) + 1

    rows = []
    for pid, s in stats.items():
        avg_score = sum(s["scores"]) / len(s["scores"]) if s["scores"] else 0
        avg_cred = sum(s["credibilities"]) / len(s["credibilities"]) if s["credibilities"] else 0.5
        impact_raw = s["total_reach"] * avg_score * avg_cred
        total = sum(s["counts"].values())
        dominant = max(s["counts"], key=s["counts"].get) if s["counts"] else "neutral"
        rows.append({"name": s["name"], "impact_raw": impact_raw, "sentiment": dominant, "count": total})

    rows.sort(key=lambda x: x["impact_raw"], reverse=True)
    max_raw = rows[0]["impact_raw"] if rows else 1.0
    sources = [
        InfluentialSource(
            portal_name=r["name"],
            impact_score=round(r["impact_raw"] / max_raw * 100) if max_raw > 0 else 0,
            sentiment=r["sentiment"],
            article_count=r["count"],
        )
        for r in rows[:5]
    ]
    return TopSourcesResponse(sources=sources)


# ── Screen 2: Top Brand Advocates ──────────────────────────────────────────────

_ADVOCATE_SOURCE_TYPES = {"youtube_video", "youtube_comment", "blog", "reddit_post"}
_ADVOCATE_TYPE_LABEL = {"youtube_video": "YouTube", "youtube_comment": "YouTube", "blog": "Blog", "reddit_post": "Reddit"}


@router.get("/top-advocates/{brand_id}", response_model=TopAdvocatesResponse)
def get_top_advocates_endpoint(
    brand_id: str,
    days: int = Query(30),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    from collections import defaultdict
    current_end = datetime.utcnow()
    current_start = current_end - timedelta(days=days)
    articles = get_articles(brand_id, limit=500, sentiment="positive", date_from=current_start.isoformat(), date_to=current_end.isoformat())
    articles = [a for a in articles if a.get("source_type") in _ADVOCATE_SOURCE_TYPES]

    stats: dict = defaultdict(lambda: {"name": "", "source_type": "", "total_reach": 0.0, "count": 0})
    for a in articles:
        author_info = a.get("author_info")
        author = a.get("author") or (author_info.get("display_name") if isinstance(author_info, dict) else None)
        key = author or a.get("portal_id", "unknown")
        name = author or a.get("portal_name") or a.get("portal_id", "Unknown")
        src_type = a.get("source_type", "blog")
        reach_meta = a.get("reach_metadata") or {}
        reach = float(reach_meta.get("estimated_reach", 1)) if isinstance(reach_meta, dict) else 1.0

        s = stats[key]
        s["name"] = name
        s["source_type"] = _ADVOCATE_TYPE_LABEL.get(src_type, "Media")
        s["total_reach"] += reach
        s["count"] += 1

    results = sorted(stats.values(), key=lambda x: x["total_reach"], reverse=True)
    advocates = [
        BrandAdvocate(name=r["name"], source_type=r["source_type"], article_count=r["count"], total_reach=r["total_reach"])
        for r in results[:5]
    ]
    return TopAdvocatesResponse(advocates=advocates)


# ── Screen 3: Competitor Sentiment Comparison ──────────────────────────────────

def _sentiment_pcts(arts: list[dict]) -> dict:
    if not arts:
        return {"positive_pct": 0.0, "neutral_pct": 0.0, "negative_pct": 0.0, "count": 0}
    total = len(arts)
    pos = sum(1 for a in arts if a.get("sentiment_label") == "positive")
    neg = sum(1 for a in arts if a.get("sentiment_label") == "negative")
    return {
        "positive_pct": round(pos / total * 100, 1),
        "neutral_pct": round((total - pos - neg) / total * 100, 1),
        "negative_pct": round(neg / total * 100, 1),
        "count": total,
    }


@router.get("/competitor-sentiment/{brand_id}", response_model=CompetitorSentimentResponse)
def get_competitor_sentiment(
    brand_id: str,
    days: int = Query(30),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    db = get_db()
    brand_row = db.table("brands").select("name").eq("id", brand_id).execute().data
    brand_name = brand_row[0]["name"] if brand_row else "Brand"

    config_row = db.table("brand_configs").select("competitors").eq("brand_id", brand_id).execute().data
    competitors: list[str] = (config_row[0].get("competitors") or []) if config_row else []

    current_end = datetime.utcnow()
    current_start = current_end - timedelta(days=days)
    articles = get_articles(brand_id, limit=2000, date_from=current_start.isoformat(), date_to=current_end.isoformat())

    brands = [BrandSentimentEntry(name=brand_name, is_brand=True, **_sentiment_pcts(articles))]

    for comp in competitors[:4]:
        comp_lower = comp.lower()
        comp_articles = [
            a for a in articles
            if comp_lower in (a.get("title") or "").lower()
            or any(comp_lower in (e or "").lower() for e in (a.get("entities") or []))
        ]
        brands.append(BrandSentimentEntry(name=comp, is_brand=False, **_sentiment_pcts(comp_articles)))

    return CompetitorSentimentResponse(brands=brands)


# ── Virality Alerts ───────────────────────────────────────────────────────────

# ── Regional Summary ─────────────────────────────────────────────────────────

_REGIONAL_SUMMARY_CACHE: dict = {}
_REGIONAL_SUMMARY_TTL = 60 * 60  # 1 hour

_STATE_ZONE_MAP = {
    "Delhi": "North", "Haryana": "North", "Punjab": "North", "Rajasthan": "North",
    "Uttar Pradesh": "North", "Himachal Pradesh": "North", "Uttarakhand": "North",
    "Jammu & Kashmir": "North", "J&K": "North", "Chandigarh": "North", "Ladakh": "North",
    "Tamil Nadu": "South", "Kerala": "South", "Karnataka": "South",
    "Andhra Pradesh": "South", "Telangana": "South", "Puducherry": "South", "Goa": "South",
    "West Bengal": "East", "Bihar": "East", "Odisha": "East", "Jharkhand": "East",
    "Assam": "East", "Meghalaya": "East", "Nagaland": "East", "Manipur": "East",
    "Mizoram": "East", "Tripura": "East", "Arunachal Pradesh": "East", "Sikkim": "East",
    "Maharashtra": "West", "Gujarat": "West", "Madhya Pradesh": "West", "Chhattisgarh": "West",
}


@router.get("/regional-summary/{brand_id}", response_model=RegionalSummaryResponse)
def get_regional_summary(
    brand_id: str,
    days: int = Query(30, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    cache_key = f"{brand_id}:{days}"
    now = time.time()
    if cache_key in _REGIONAL_SUMMARY_CACHE and _REGIONAL_SUMMARY_CACHE[cache_key]["expires_at"] > now:
        return RegionalSummaryResponse(**_REGIONAL_SUMMARY_CACHE[cache_key]["data"])

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    articles = get_articles(brand_id, limit=500, date_from=start.isoformat(), date_to=end.isoformat())

    # Aggregate per-state sentiment
    state_map: dict[str, dict] = {}
    for a in articles:
        label = a.get("sentiment_label", "neutral")
        for state in a.get("states_mentioned") or []:
            if state not in state_map:
                state_map[state] = {"state": state, "count": 0, "positive": 0, "negative": 0, "neutral": 0}
            state_map[state]["count"] += 1
            state_map[state][label] = state_map[state].get(label, 0) + 1

    if not state_map:
        result = {
            "summary": "No regional data available for this period.",
            "state_highlights": [],
            "confidence_pct": 0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        _REGIONAL_SUMMARY_CACHE[cache_key] = {"data": result, "expires_at": now + _REGIONAL_SUMMARY_TTL}
        return RegionalSummaryResponse(**result)

    # Classify each state as improving/declining/stable by pos/neg ratio
    highlights_raw = []
    for state, s in state_map.items():
        total = s["count"]
        if total < 3:
            continue
        pos_pct = round(s["positive"] / total * 100, 1)
        neg_pct = round(s["negative"] / total * 100, 1)
        if pos_pct >= 55:
            direction = "improving"
            dominant = "positive"
            pct = pos_pct
        elif neg_pct >= 55:
            direction = "declining"
            dominant = "negative"
            pct = neg_pct
        else:
            direction = "stable"
            dominant = "neutral"
            pct = round(max(pos_pct, neg_pct), 1)
        highlights_raw.append({
            "state": state, "direction": direction,
            "sentiment_pct": pct, "dominant_sentiment": dominant,
            "article_count": total, "zone": _STATE_ZONE_MAP.get(state, "Other"),
        })

    highlights_raw.sort(key=lambda x: x["article_count"], reverse=True)
    top_highlights = highlights_raw[:6]

    # Zone-level summary for the Gemini prompt
    zone_totals: dict[str, dict] = {}
    for h in highlights_raw:
        z = h["zone"]
        if z not in zone_totals:
            zone_totals[z] = {"count": 0, "improving": 0, "declining": 0, "stable": 0}
        zone_totals[z]["count"] += 1
        zone_totals[z][h["direction"]] += 1

    zone_lines = []
    for zone, z in zone_totals.items():
        if z["improving"] > z["declining"]:
            trend = "improving"
        elif z["declining"] > z["improving"]:
            trend = "declining"
        else:
            trend = "stable"
        zone_lines.append(f"{zone}: {trend} ({z['count']} states)")

    zone_summary = "; ".join(zone_lines) or "mixed"
    notable_states = ", ".join(
        f"{h['state']} ({h['direction']})" for h in top_highlights[:4]
    )

    # Gemini for summary sentence
    from google import genai as _genai
    summary_prompt = (
        f"Write a 2-sentence regional media sentiment summary for a brand analyst. "
        f"Zone trends: {zone_summary}. Notable states: {notable_states}. "
        f"Mention the strongest trend and one specific state or region by name. "
        f"Respond with ONLY the 2 sentences — no quotes, no preamble."
    )
    summary = f"Regional coverage spans {len(state_map)} states. " + (zone_lines[0] if zone_lines else "Sentiment mixed across regions.")
    confidence_pct = 70

    _attempts = [
        (settings.gemini_api_key, settings.gemini_model or "gemini-2.5-flash"),
        (settings.gemini_free_api_key, "gemini-2.0-flash"),
        (settings.gemini_free_api_key, "gemini-1.5-flash"),
    ]
    for _api_key, _model in _attempts:
        if not _api_key:
            continue
        try:
            _client = _genai.Client(api_key=_api_key, http_options={"timeout": 8})
            _resp = _client.models.generate_content(model=_model, contents=summary_prompt)
            raw = _resp.text.strip().strip('"').strip("'")
            if raw and len(raw) > 15:
                summary = raw
                confidence_pct = 78
                break
        except Exception as e:
            err = str(e)
            if any(k in err for k in ("RESOURCE_EXHAUSTED", "429", "404")):
                continue
            break

    result = {
        "summary": summary,
        "state_highlights": [
            StateHighlight(
                state=h["state"], direction=h["direction"],
                sentiment_pct=h["sentiment_pct"], dominant_sentiment=h["dominant_sentiment"],
                article_count=h["article_count"],
            )
            for h in top_highlights[:5]
        ],
        "confidence_pct": confidence_pct,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    # Pydantic objects → dicts for cache
    cache_data = {
        "summary": result["summary"],
        "state_highlights": [h.model_dump() for h in result["state_highlights"]],
        "confidence_pct": result["confidence_pct"],
        "generated_at": result["generated_at"],
    }
    _REGIONAL_SUMMARY_CACHE[cache_key] = {"data": cache_data, "expires_at": now + _REGIONAL_SUMMARY_TTL}
    return RegionalSummaryResponse(**cache_data)


# ── Morning Brief ────────────────────────────────────────────────────────────

_MORNING_BRIEF_CACHE: dict = {}
_MORNING_BRIEF_TTL = 60 * 60  # 1 hour


@router.get("/morning-brief/{brand_id}", response_model=MorningBriefResponse)
def get_morning_brief(
    brand_id: str,
    days: int = Query(7, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    cache_key = f"{brand_id}:{days}"
    now = time.time()
    if cache_key in _MORNING_BRIEF_CACHE and _MORNING_BRIEF_CACHE[cache_key]["expires_at"] > now:
        return MorningBriefResponse(**_MORNING_BRIEF_CACHE[cache_key]["data"])

    end = datetime.now(timezone.utc)
    current_start = end - timedelta(days=days)
    prior_start = current_start - timedelta(days=days)

    current = _window_kpi(brand_id, current_start.isoformat(), end.isoformat())
    prior = _window_kpi(brand_id, prior_start.isoformat(), current_start.isoformat())

    score_change = round(current["perception_score"] - prior["perception_score"], 1) if prior["count"] > 0 else 0.0
    if abs(score_change) < 1.5:
        direction = "stable"
    elif score_change > 0:
        direction = "up"
    else:
        direction = "down"

    # Build highlights from actual data
    articles = get_articles(brand_id, limit=300, date_from=current_start.isoformat(), date_to=end.isoformat())
    db = get_db()
    brand_row = db.table("brands").select("name").eq("id", brand_id).execute().data
    brand_name = brand_row[0]["name"] if brand_row else "the brand"

    total = len(articles)
    neg = sum(1 for a in articles if a.get("sentiment_label") == "negative")
    pos = sum(1 for a in articles if a.get("sentiment_label") == "positive")
    neg_pct = round(neg / total * 100, 1) if total else 0
    pos_pct = round(pos / total * 100, 1) if total else 0

    issue_counter: Counter = Counter(
        a.get("issue_category", "other") for a in articles
        if a.get("issue_category") and a.get("issue_category") != "other"
    )
    top_issues = [c.replace("_", " ") for c, _ in issue_counter.most_common(2)]
    reg_count = sum(1 for a in articles if a.get("is_regulatory_source"))

    highlights: list[str] = []
    if abs(score_change) >= 1.5:
        direction_word = "increased" if score_change > 0 else "decreased"
        highlights.append(f"Reputation score {direction_word} by {abs(score_change):.1f} pts vs prior {days} days")
    else:
        highlights.append(f"Reputation score stable at {current['perception_score']:.0f}/100")
    if neg_pct > 30:
        highlights.append(f"Negative coverage elevated at {neg_pct}% of {total} articles")
    elif pos_pct > 50:
        highlights.append(f"Positive coverage strong at {pos_pct}% of {total} articles")
    else:
        highlights.append(f"{total} articles collected — {pos_pct}% positive, {neg_pct}% negative")
    if top_issues:
        highlights.append(f"Top issue: {top_issues[0].title()}" + (f" and {top_issues[1].title()}" if len(top_issues) > 1 else ""))
    if reg_count:
        highlights.append(f"{reg_count} regulatory source mention{'s' if reg_count != 1 else ''} detected — review recommended")
    else:
        highlights.append("No regulatory or crisis signals detected")

    # Gemini greeting sentence
    from google import genai as _genai
    from app.nlp.gemini_handler import _strip_fences
    score_line = f"Score {'up' if direction == 'up' else 'down' if direction == 'down' else 'stable'} {abs(score_change):.1f} pts." if abs(score_change) >= 1.5 else "Score stable."
    greeting_prompt = (
        f"Write a single-sentence executive morning greeting for {brand_name}. "
        f"Tone: calm, professional, brief — like a senior analyst speaking to a CMO. "
        f"Include: {score_line} Top concern: {top_issues[0] if top_issues else 'general coverage'}. "
        f"Coverage: {total} articles, {neg_pct}% negative. "
        f"Respond with ONLY the greeting sentence — no quotes, no punctuation beyond the sentence itself."
    )
    greeting = f"Good morning. {brand_name} coverage: {score_line} {total} articles monitored."
    confidence_pct = 72

    _attempts = [
        (settings.gemini_api_key, settings.gemini_model or "gemini-2.5-flash"),
        (settings.gemini_free_api_key, "gemini-2.0-flash"),
        (settings.gemini_free_api_key, "gemini-1.5-flash"),
    ]
    for _api_key, _model in _attempts:
        if not _api_key:
            continue
        try:
            _client = _genai.Client(api_key=_api_key, http_options={"timeout": 8})
            _resp = _client.models.generate_content(model=_model, contents=greeting_prompt)
            raw = _resp.text.strip().strip('"').strip("'")
            if raw and len(raw) > 10:
                greeting = raw
                confidence_pct = min(95, 68 + round(pos_pct * 0.3))
                break
        except Exception as e:
            err = str(e)
            if any(k in err for k in ("RESOURCE_EXHAUSTED", "429", "404")):
                continue
            break

    result = {
        "greeting": greeting,
        "score_change": score_change,
        "score_direction": direction,
        "highlights": highlights[:4],
        "confidence_pct": confidence_pct,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _MORNING_BRIEF_CACHE[cache_key] = {"data": result, "expires_at": now + _MORNING_BRIEF_TTL}
    return MorningBriefResponse(**result)


# ── AI Chat (streaming SSE) ───────────────────────────────────────────────────

_CHAT_SYSTEM = (
    "You are BrandPulse AI, a senior media intelligence analyst. "
    "Brand: {brand_name}. Coverage period: last {days} days.\n"
    "Context: {total} articles — {pos_pct}% positive, {neg_pct}% negative, {neu_pct}% neutral. "
    "Top issues: {top_issues}. Top sources: {top_sources}.\n"
    "Recent negative headlines: {neg_headlines}\n\n"
    "Answer the user's question concisely and specifically, always referencing the actual data above. "
    "Never give generic answers — cite issue categories, source types, or specific article patterns. "
    "If asked to predict, extrapolate from visible trends. "
    "If asked to generate content (tweet, statement, FAQ), produce it directly. "
    "Keep responses under 200 words unless generating content."
)


def _build_chat_context(brand_id: str, days: int) -> dict:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    articles = get_articles(brand_id, limit=200, date_from=start.isoformat(), date_to=end.isoformat())
    db = get_db()
    brand_row = db.table("brands").select("name").eq("id", brand_id).execute().data
    brand_name = brand_row[0]["name"] if brand_row else "the brand"

    total = len(articles)
    if total == 0:
        return {"brand_name": brand_name, "total": 0, "pos_pct": 0, "neg_pct": 0, "neu_pct": 0,
                "top_issues": "none", "top_sources": "none", "neg_headlines": "none"}

    neg = sum(1 for a in articles if a.get("sentiment_label") == "negative")
    pos = sum(1 for a in articles if a.get("sentiment_label") == "positive")
    neu = total - neg - pos
    neg_pct = round(neg / total * 100, 1)
    pos_pct = round(pos / total * 100, 1)
    neu_pct = round(neu / total * 100, 1)

    issue_counter: Counter = Counter(
        a.get("issue_category", "other") for a in articles
        if a.get("issue_category") and a.get("issue_category") != "other"
    )
    top_issues = ", ".join(c.replace("_", " ") for c, _ in issue_counter.most_common(4)) or "general coverage"

    portal_counter: Counter = Counter(a.get("portal_id", "") for a in articles)
    db2 = get_db()
    portal_ids = [pid for pid, _ in portal_counter.most_common(5) if pid]
    portal_names_map: dict[str, str] = {}
    if portal_ids:
        rows = db2.table("portals").select("id,name").in_("id", portal_ids).execute().data or []
        portal_names_map = {r["id"]: r["name"] for r in rows}
    top_sources = ", ".join(
        portal_names_map.get(pid, pid) for pid, _ in portal_counter.most_common(3) if pid
    ) or "various sources"

    neg_articles = sorted(
        [a for a in articles if a.get("sentiment_label") == "negative"],
        key=lambda a: a.get("reach_score") or 0, reverse=True
    )[:3]
    neg_headlines = "; ".join(a.get("title", "")[:80] for a in neg_articles if a.get("title")) or "none"

    return {
        "brand_name": brand_name, "days": days, "total": total,
        "pos_pct": pos_pct, "neg_pct": neg_pct, "neu_pct": neu_pct,
        "top_issues": top_issues, "top_sources": top_sources, "neg_headlines": neg_headlines,
    }


def _stream_chat(prompt: str, context_messages: list[ChatMessage]) -> object:
    from google import genai as _genai
    from app.nlp.gemini_handler import _strip_fences

    attempts = [
        (settings.gemini_api_key, settings.gemini_model or "gemini-2.5-flash"),
        (settings.gemini_free_api_key, "gemini-2.0-flash"),
        (settings.gemini_free_api_key, "gemini-1.5-flash"),
    ]

    full_text = None
    for api_key, model in attempts:
        if not api_key:
            continue
        try:
            client = _genai.Client(api_key=api_key, http_options={"timeout": 30})
            # Build conversation contents (system + history + new message)
            contents = [prompt]
            response = client.models.generate_content(model=model, contents=contents)
            full_text = response.text.strip()
            break
        except Exception as e:
            err = str(e)
            if any(k in err for k in ("RESOURCE_EXHAUSTED", "429", "404")):
                continue
            log.warning("Chat LLM error (%s): %s", model, err[:120])
            break

    if not full_text:
        full_text = "I couldn't generate a response right now. Please try again in a moment."

    # Word-by-word SSE simulation
    import json as _js
    words = full_text.split()
    for word in words:
        yield f'data: {_js.dumps({"token": word + " ", "done": False})}\n\n'
    yield f'data: {_js.dumps({"token": "", "done": True})}\n\n'


@router.post("/chat")
def chat_with_brand(
    req: ChatRequest,
    days: int = Query(7, ge=1, le=90),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    ctx = _build_chat_context(req.brand_id, days)
    system = _CHAT_SYSTEM.format(**ctx)
    prompt = f"{system}\n\nUser question: {req.message}"

    return StreamingResponse(
        _stream_chat(prompt, req.context_messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/virality-alerts/{brand_id}", response_model=ViralityAlertsResponse)
async def get_virality_alerts(
    brand_id: str,
    days: int = Query(7, ge=1, le=30),
    user=Depends(require_brand_role),
):
    """Return YouTube videos with virality spikes for the given brand.

    Works with whatever snapshot history is available:
    - 0 prior days: absolute threshold (50K views / 500 comments)
    - 1–7 prior days: rolling avg × 3 multiplier
    """
    raw_flags = compute_virality_flags(brand_id, article_days=days)
    flags = [ViralityFlag(**f) for f in raw_flags]
    flags.sort(key=lambda f: f.flag_level, reverse=True)
    return ViralityAlertsResponse(flags=flags, brand_id=brand_id, period_days=days)
