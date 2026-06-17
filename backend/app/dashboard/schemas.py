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
    entities: list[str]
    topics: list[str]
    keywords: list[str]
    states_mentioned: list[str] = []
    model_used: str | None = None
    author_info: AuthorInfo | None = None
    metrics: MentionMetrics | None = None


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
