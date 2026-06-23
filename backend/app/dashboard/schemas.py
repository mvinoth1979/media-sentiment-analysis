from pydantic import BaseModel, field_validator


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
    total_reach: int = 0
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


class SourceTypeStat(BaseModel):
    count: int = 0
    delta_pct: float | None = None
    negative_pct: float | None = None
    avg_rating: float | None = None
    sparkline: list[int] = []


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
    by_source_type: dict[str, SourceTypeStat] = {}


# --- Screen 3: Competitor Sentiment Comparison ---

class BrandSentimentEntry(BaseModel):
    name: str
    is_brand: bool
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    count: int


class CompetitorSentimentResponse(BaseModel):
    brands: list[BrandSentimentEntry]


# --- Screen 2: Top Influential Sources ---

class InfluentialSource(BaseModel):
    portal_name: str
    impact_score: int  # 0-100, normalised
    sentiment: str
    article_count: int


class TopSourcesResponse(BaseModel):
    sources: list[InfluentialSource]


# --- Screen 2: Top Brand Advocates ---

class BrandAdvocate(BaseModel):
    name: str
    source_type: str  # "YouTube" | "Blog" | "Reddit"
    article_count: int
    total_reach: float


class TopAdvocatesResponse(BaseModel):
    advocates: list[BrandAdvocate]


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


class ReviewPlatformStat(BaseModel):
    source_type: str
    platform_name: str
    count: int
    avg_rating: float | None = None
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    positive_pct: float = 0.0
    negative_pct: float = 0.0
    recent_snippets: list[str] = []


class ReviewSitesBreakdownResponse(BaseModel):
    platforms: list[ReviewPlatformStat]
    total_reviews: int
    overall_avg_rating: float | None = None
    brand_id: str
    period_days: int


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


# ── Human Review Queue (Item 5) ───────────────────────────────────────────────

class ReviewQueueItem(BaseModel):
    id: str
    brand_id: str
    article_id: str
    reason: str
    status: str          # "pending" | "approved" | "rejected"
    reviewer_id: str | None = None
    reviewed_at: str | None = None
    created_at: str | None = None
    # Denormalized from articles for display
    article_title: str | None = None
    article_url: str | None = None


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    total: int


class ReviewQueuePatchRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        if v not in ("approved", "rejected"):
            raise ValueError(f"status must be 'approved' or 'rejected', got '{v}'")
        return v


# ── Per-video Brand Risk Score (Item 8) ───────────────────────────────────────

class VideoRiskItem(BaseModel):
    article_id: str
    title: str
    url: str
    portal_id: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    sentiment_score: float = 0.0
    risk_score: float = 0.0
    reach_tier: str = "Low"   # "Viral" | "High" | "Mid" | "Low"
    published_at: str | None = None


class BrandRiskScoresResponse(BaseModel):
    videos: list[VideoRiskItem]
    brand_id: str
    period_days: int = 30


# ── AI Executive Summary ──────────────────────────────────────────────────────

class AISummaryResponse(BaseModel):
    what_changed: str
    why: str
    actions: list[str]
    generated_at: str



# ── AI Explainer ─────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    metric: str                        # "reputation_score" | "mention_growth" | "risk_score" | "state_sentiment" | "executive_summary" | "investigation_context" | ...
    brand_id: str
    value: float | None = None         # current metric value (e.g. 53.2)
    date_from: str | None = None
    date_to: str | None = None
    context: dict = {}                 # extra context: {"state": "Tamil Nadu", "source_type": "youtube", ...}


class ExplainResponse(BaseModel):
    headline: str                      # 1-sentence summary: "Score dropped 12 pts due to Tamil coverage spike"
    drivers: list[str]                 # 3-5 specific causal factors
    evidence: list[str]                # article titles or source references supporting the explanation
    confidence: str                    # "high" | "medium" | "low"
    confidence_pct: int                # 0–100 numeric confidence
    suggested_action: str              # 1 concrete recommended action
    drill_tab: str                     # "A" | "B" | "C" — which drill tab is most relevant


# ── Narrative DNA ────────────────────────────────────────────────────────────

class NarrativeDNAResponse(BaseModel):
    fear: float           # 0-100: regulatory/crisis signals
    criticism: float      # 0-100: critical editorial tone %
    consumer_trust: float # 0-100: review-source sentiment
    political: float      # 0-100: political issue %
    brand_safety: float   # 0-100: inverse of negative %
    period_days: int
    brand_id: str


# ── Entity Graph ─────────────────────────────────────────────────────────────

class EntityNode(BaseModel):
    entity: str
    count: int
    positive_count: int
    negative_count: int
    neutral_count: int


class EntityEdge(BaseModel):
    entity_a: str
    entity_b: str
    co_count: int


class EntityGraphResponse(BaseModel):
    nodes: list[EntityNode]
    edges: list[EntityEdge]
    period_days: int
    brand_id: str


# ── Advocate Scoring ─────────────────────────────────────────────────────────

class ScoredAdvocate(BaseModel):
    name: str
    source_type: str
    article_count: int
    total_reach: float
    affinity: int        # 0-100: positive%
    influence: int       # 0-100: volume proxy
    trust: int           # 0-100: inverse of negative%
    total_score: int     # weighted composite
    emerging: bool       # first seen < 30 days ago
    suggested_engagement: str


class ScoredAdvocatesResponse(BaseModel):
    advocates: list[ScoredAdvocate]


# ── Content Generation ────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    brand_id: str
    format: str   # "press_release" | "faq" | "tweet" | "linkedin" | "ceo_statement"
    topic: str


class GenerateResponse(BaseModel):
    content: str
    format: str
    word_count: int
    char_count: int
    confidence_pct: int
    generated_at: str


# ── Risk Forecast ────────────────────────────────────────────────────────────

class RiskDayPoint(BaseModel):
    date: str           # "2026-06-18"
    risk_score: float   # 0-100
    article_count: int
    negative_count: int


class RiskForecastPoint(BaseModel):
    days_ahead: int
    predicted_risk: float
    lower: float
    upper: float


class RiskForecastResponse(BaseModel):
    historical: list[RiskDayPoint]
    forecasts: list[RiskForecastPoint]   # 1d, 3d, 7d
    narrative: str
    slope: float         # points per day (positive = worsening)
    confidence: str      # "high" | "medium" | "low"
    confidence_pct: int
    brand_id: str


# ── Issue Radar ──────────────────────────────────────────────────────────────

class IssueRadarPoint(BaseModel):
    issue: str
    count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    velocity: float     # current 7d rate / 30d baseline rate (normalised to daily)
    reach: int          # summed reach_score proxy


class IssueRadarResponse(BaseModel):
    points: list[IssueRadarPoint]
    period_days: int
    brand_id: str


class EmergingTopic(BaseModel):
    topic: str
    novelty_score: float   # current_daily_rate / baseline_daily_rate
    current_count: int
    baseline_daily_rate: float


class EmergingTopicsResponse(BaseModel):
    emerging: list[EmergingTopic]   # novelty_score >= 3.0 AND count >= 5
    brand_id: str
    period_days: int
    baseline_days: int


# ── Story Feed ───────────────────────────────────────────────────────────────

class StoryCard(BaseModel):
    article_id: str
    title: str
    url: str
    portal_name: str
    published_at: str | None
    sentiment_label: str
    impact_score: int       # 0–100 composite
    source_type: str
    action: str | None = None  # "watch" | "investigate" | "ignore" | None


class StoryFeedResponse(BaseModel):
    stories: list[StoryCard]
    total: int


class StoryActionRequest(BaseModel):
    brand_id: str
    article_id: str
    action: str   # "watch" | "investigate" | "ignore"


# ── Regional Summary ─────────────────────────────────────────────────────────

class StateHighlight(BaseModel):
    state: str
    direction: str          # "improving" | "declining" | "stable"
    sentiment_pct: float    # dominant sentiment %
    dominant_sentiment: str # "negative" | "positive" | "neutral"
    article_count: int


class RegionalSummaryResponse(BaseModel):
    summary: str                           # "South India sentiment improving. West declining."
    state_highlights: list[StateHighlight] # top 5 notable states
    confidence_pct: int
    generated_at: str


# ── Morning Brief ────────────────────────────────────────────────────────────

class MorningBriefResponse(BaseModel):
    greeting: str           # "Good morning. Brand reputation stable."
    score_change: float     # +4.2 (delta vs prior period)
    score_direction: str    # "up" | "down" | "stable"
    highlights: list[str]   # 3-4 data-driven bullet points
    confidence_pct: int     # AI confidence 0-100
    generated_at: str


# ── AI Chat ──────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    brand_id: str
    context_messages: list[ChatMessage] = []


# ── Virality Alerts ───────────────────────────────────────────────────────────

class ViralityFlag(BaseModel):
    article_id: str
    title: str
    url: str = ""
    flag_level: int           # 1=emerging, 2=reputation_risk, 3=crisis_alert
    triggered_metrics: list[str]
    history_days: int = 0     # 0 = day-0 absolute threshold; 1-7 = rolling avg


class ViralityAlertsResponse(BaseModel):
    flags: list[ViralityFlag]
    brand_id: str
    period_days: int = 7
