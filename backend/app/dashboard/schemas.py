from pydantic import BaseModel


class KPISummary(BaseModel):
    perception_score: float
    total: int
    positive: int
    negative: int
    neutral: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    youtube_mention_count: int = 0
    perception_score_delta: float | None = None
    mentions_delta_pct: float | None = None


class TrendPoint(BaseModel):
    time: str
    value: float


class AuthorInfo(BaseModel):
    display_name: str | None = None


class MentionMetrics(BaseModel):
    estimated_reach: int = 0
    influence_score: float = 0.5


class ArticleItem(BaseModel):
    id: str
    title: str
    url: str
    portal_id: str
    published_at: str | None
    sentiment_label: str
    sentiment_score: float
    language: str
    source_credibility: float = 0.5
    source_platform: str = "news"
    source_type: str = "news"
    entities: list[str]
    topics: list[str]
    keywords: list[str]
    states_mentioned: list[str] = []
    reach_metadata: dict = {}
    model_used: str | None = None
    author_info: AuthorInfo | None = None
    metrics: MentionMetrics | None = None
    # Phase 1 data quality fields
    author: str | None = None
    editorial_tone: str | None = None
    sentiment_divergence: bool = False
    is_regulatory_source: bool = False
    # Structured issue taxonomy (12 categories)
    issue_category: str = "other"
    # Item 9: YouTube creator type classification
    creator_type: str | None = None


class SourceStat(BaseModel):
    portal_id: str
    count: int
    positive: int
    negative: int
    neutral: int
    avg_credibility: float = 0.5


class TopicStat(BaseModel):
    topic: str
    count: int
    positive: int
    negative: int
    neutral: int


class StateStat(BaseModel):
    state: str
    count: int
    positive: int
    negative: int
    neutral: int


class DeleteMentionsRequest(BaseModel):
    ids: list[str]


class AnnotationCreate(BaseModel):
    date: str
    label: str


class Annotation(BaseModel):
    id: str
    date: str
    label: str
    created_by: str
    created_at: str


class PipelineStats(BaseModel):
    collected: int = 0
    processed: int = 0
    errors: int = 0


class OverviewResponse(BaseModel):
    kpi: KPISummary
    trend: list[TrendPoint]
    recent_mentions: list[ArticleItem]
    top_sources: list[SourceStat]
    top_keywords: list[str]
    top_topics: list[str]
    state_breakdown: list[StateStat] = []
    last_processed_at: str | None = None
    pipeline_status: str = "idle"
    pipeline_last_run_at: str | None = None
    pipeline_last_stats: PipelineStats = PipelineStats()


# --- Phase 3: Sentiment Trend (3-line + Tier 1+2 overlay) ---

class SentimentTrendPoint(BaseModel):
    time: str
    positive: int
    negative: int
    neutral: int


class SentimentTrendResponse(BaseModel):
    points: list[SentimentTrendPoint]
    points_tier1: list[SentimentTrendPoint]
    window: str  # "1d" or "1h"


# --- Phase 3: Source Categories Donut ---

class SourceCategoryPoint(BaseModel):
    category: str
    label: str
    color: str
    count: int
    positive: int
    negative: int
    neutral: int
    pct: float
    avg_credibility: float
    tier_distribution: dict


class SourceCategoriesResponse(BaseModel):
    categories: list[SourceCategoryPoint]
    total: int


# --- Phase 3: Top Headlines ---

class HeadlineItem(BaseModel):
    id: str
    title: str
    url: str
    portal_id: str
    portal_name: str
    portal_category: str
    source_tier: int
    source_tier_label: str
    published_at: str | None = None
    collected_at: str | None = None
    sentiment_label: str
    sentiment_score: float
    sentiment_intensity: str
    source_credibility: float
    language: str
    source_type: str
    repeat_author: bool = False
    reach_tier: str | None = None
    author_name: str | None = None
    # Phase 1 data quality fields
    sentiment_divergence: bool = False
    is_regulatory_source: bool = False
    editorial_tone: str | None = None


class HeadlinesResponse(BaseModel):
    tab: str
    items: list[HeadlineItem]


# --- Review Summary (derived from pipeline sentiment data) ---

class ReviewStarBucket(BaseModel):
    stars: int
    count: int
    pct: float


class TopicTheme(BaseModel):
    label: str
    pct: float


class ReviewSummaryResponse(BaseModel):
    total: int
    avg_rating: float
    distribution: list[ReviewStarBucket]
    top_positive_topics: list[TopicTheme]
    top_negative_topics: list[TopicTheme]


# --- Competitor Share of Voice ---

class SoVEntry(BaseModel):
    name: str
    count: int
    pct: float
    color: str
    is_brand: bool = False


class CompetitorSoVResponse(BaseModel):
    total_articles: int
    entries: list[SoVEntry]
    source: str  # "configured" | "entity_fallback"


class CompetitorDiscoveryResponse(BaseModel):
    competitors: list[str]
    saved: bool


# --- Issue Clusters (B4) ---

class ClusterArticle(BaseModel):
    title: str
    url: str
    sentiment_label: str


class IssueCluster(BaseModel):
    cluster_name: str
    article_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    net_sentiment_pct: int
    trend: str  # "rising" | "stable"
    top_articles: list[ClusterArticle]


class IssueClustersResponse(BaseModel):
    clusters: list[IssueCluster]
    period_days: int
    brand_id: str


# ── Journalist Coverage ────────────────────────────────────────────────────────

class JournalistArticle(BaseModel):
    title: str
    url: str
    published_at: str
    sentiment_label: str


class JournalistProfile(BaseModel):
    author: str
    total_articles: int
    negative_count: int
    positive_count: int
    neutral_count: int
    negative_pct: float
    last_article_at: str
    recent_articles: list[JournalistArticle]


class JournalistCoverageResponse(BaseModel):
    journalists: list[JournalistProfile]
    period_days: int
    brand_id: str


# ── Editorial Tone Breakdown (Phase 1) ────────────────────────────────────────

class ToneWeek(BaseModel):
    week: str           # "2026-W24"
    factual: int
    positive_frame: int
    negative_frame: int
    critical: int


class ToneBreakdownResponse(BaseModel):
    total: dict         # {"factual": 42, "positive_frame": 18, ...}
    weekly_trend: list[ToneWeek]
    period_days: int
    brand_id: str


# ── Sentiment Divergence Summary (Phase 1) ────────────────────────────────────

class DivergentArticle(BaseModel):
    title: str
    url: str
    published_at: str | None
    headline_sentiment_score: float
    body_sentiment_score: float
    sentiment_label: str


class DivergenceSummaryResponse(BaseModel):
    total_divergent_count: int
    divergent_pct: float
    articles: list[DivergentArticle]
    period_days: int


# ── YouTube Creator vs Audience Sentiment Split ───────────────────────────────

class YTSentimentBucket(BaseModel):
    positive: int
    neutral: int
    negative: int
    total: int
    avg_score: float


class YTDivergentVideo(BaseModel):
    title: str
    url: str
    portal_name: str
    creator_label: str
    audience_label: str
    comment_count: int


class YTSentimentSplitResponse(BaseModel):
    creator: YTSentimentBucket
    audience: YTSentimentBucket
    divergent_videos: list[YTDivergentVideo]
    period_days: int
    brand_id: str


# ── Issue Category Breakdown (Phase 3) ───────────────────────────────────────

class IssueCategoryItem(BaseModel):
    category: str
    count: int
    positive_count: int
    negative_count: int


class IssueCategoriesResponse(BaseModel):
    categories: list[IssueCategoryItem]
    period_days: int
    brand_id: str
