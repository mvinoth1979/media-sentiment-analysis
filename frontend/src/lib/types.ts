export interface KPISummary {
  perception_score: number;
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  youtube_mention_count?: number;
  reddit_mention_count?: number;
  total_reach?: number;
  perception_score_delta: number | null;
  mentions_delta_pct: number | null;
}

export interface TrendPoint { time: string; value: number; }

export interface AuthorInfo {
  display_name: string | null;
}

export interface MentionMetrics {
  estimated_reach: number;
  influence_score: number;
}

export interface ArticleItem {
  id: string;
  title: string;
  url: string;
  portal_id: string;
  published_at: string;
  sentiment_label: "positive" | "negative" | "neutral";
  sentiment_score: number;
  language: string;
  source_credibility: number;
  source_platform: string;
  source_type?: string;
  entities: string[];
  topics: string[];
  keywords: string[];
  states_mentioned: string[];
  reach_metadata?: Record<string, number>;
  model_used: string;
  author_info?: AuthorInfo | null;
  metrics?: MentionMetrics | null;
  // Phase 1 data quality fields
  author?: string | null;
  editorial_tone?: "factual" | "positive_frame" | "negative_frame" | "critical" | null;
  sentiment_divergence?: boolean | null;
  is_regulatory_source?: boolean | null;
  issue_category?: string | null;
  // Item 9: YouTube creator type classification
  creator_type?: string | null;
}

export interface SourceStat {
  portal_id: string;
  count: number;
  positive: number;
  negative: number;
  neutral: number;
  avg_credibility: number;
}

export interface TopicStat {
  topic: string;
  count: number;
  positive: number;
  negative: number;
  neutral: number;
}

export interface StateStat {
  state: string;
  count: number;
  positive: number;
  negative: number;
  neutral: number;
}

export interface Annotation {
  id: string;
  date: string;
  label: string;
  created_by: string;
  created_at: string;
}

export interface PipelineStats {
  collected: number;
  processed: number;
  errors: number;
}

export interface AlertConfig {
  id: string;
  brand_id: string;
  alert_type: "perception_score_below" | "negative_pct_above" | "mention_spike" | "syndication_spike" | "journalist_beat";
  threshold: number;
  notify_email: string;
  enabled: boolean;
  last_triggered_at: string | null;
  created_at: string;
}

export interface BrandUser {
  id: string;
  user_id: string;
  email: string;
  role: string;
  brand_id: string | null;
  agency_id: string | null;
}

export interface SourceTypeStat {
  count: number;
  delta_pct: number | null;
  negative_pct: number | null;
  avg_rating: number | null;
  sparkline: number[];
}

export interface OverviewData {
  kpi: KPISummary;
  trend: TrendPoint[];
  recent_mentions: ArticleItem[];
  top_sources: SourceStat[];
  top_keywords: string[];
  top_topics: string[];
  state_breakdown: StateStat[];
  last_processed_at: string | null;
  pipeline_status: "idle" | "running";
  pipeline_last_run_at: string | null;
  pipeline_last_stats: PipelineStats;
  by_source_type: Record<string, SourceTypeStat>;
}

// ── Phase 3 types ──────────────────────────────────────────────────────────────

export interface SentimentTrendPoint {
  time: string;
  positive: number;
  negative: number;
  neutral: number;
}

export interface SentimentTrendData {
  points: SentimentTrendPoint[];
  points_tier1: SentimentTrendPoint[];
  window: "1d" | "1h";
}

export interface SourceCategoryPoint {
  category: string;
  label: string;
  color: string;
  count: number;
  positive: number;
  negative: number;
  neutral: number;
  pct: number;
  avg_credibility: number;
  tier_distribution: Record<string, number>;
}

export interface SourceCategoriesData {
  categories: SourceCategoryPoint[];
  total: number;
}

export interface HeadlineItem {
  id: string;
  title: string;
  url: string;
  portal_id: string;
  portal_name: string;
  portal_category: string;
  source_tier: number;
  source_tier_label: string;
  published_at: string | null;
  collected_at: string | null;
  sentiment_label: "positive" | "negative" | "neutral";
  sentiment_score: number;
  sentiment_intensity: string;
  source_credibility: number;
  language: string;
  source_type: string;
  repeat_author: boolean;
  reach_tier: string | null;
  author_name: string | null;
  // Phase 1 data quality fields
  sentiment_divergence?: boolean | null;
  is_regulatory_source?: boolean | null;
  editorial_tone?: string | null;
}

export interface HeadlinesData {
  tab: string;
  items: HeadlineItem[];
}

export interface ReviewStarBucket {
  stars: number;
  count: number;
  pct: number;
}

export interface TopicTheme {
  label: string;
  pct: number;
}

export interface ReviewSummaryData {
  total: number;
  avg_rating: number;
  distribution: ReviewStarBucket[];
  top_positive_topics: TopicTheme[];
  top_negative_topics: TopicTheme[];
}

export interface ReviewPlatformStat {
  source_type: string;
  platform_name: string;
  count: number;
  avg_rating: number | null;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_pct: number;
  negative_pct: number;
  recent_snippets: string[];
}

export interface ReviewSitesBreakdownData {
  platforms: ReviewPlatformStat[];
  total_reviews: number;
  overall_avg_rating: number | null;
  brand_id: string;
  period_days: number;
}

export interface SoVEntry {
  name: string;
  count: number;
  pct: number;
  color: string;
  is_brand: boolean;
}

export interface CompetitorSoVData {
  total_articles: number;
  entries: SoVEntry[];
  source: "configured" | "entity_fallback";
}

// ── Drill-down (Screen 5) ──────────────────────────────────────────────────────

export interface DrillFilters {
  sentiment?: string;
  topic?: string;
  sourceCategory?: string;
  sourceType?: string;
  issueCategory?: string;
  entity?: string;
  state?: string;
  q?: string;
}

export interface DrillEntry {
  widgetTitle: string;
  filters: DrillFilters;
}

// ── Issue Clusters (B4) ────────────────────────────────────────────────────────

export interface ClusterArticle {
  title: string;
  url: string;
  sentiment_label: "positive" | "negative" | "neutral";
}

export interface IssueCluster {
  cluster_name: string;
  article_count: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  net_sentiment_pct: number;
  trend: "rising" | "stable";
  top_articles: ClusterArticle[];
}

export interface IssueClustersData {
  clusters: IssueCluster[];
  period_days: number;
  brand_id: string;
}

// ── Journalist Coverage ────────────────────────────────────────────────────────

export interface JournalistArticleItem {
  title: string;
  url: string;
  published_at: string;
  sentiment_label: "positive" | "negative" | "neutral";
}

export interface JournalistProfile {
  author: string;
  total_articles: number;
  negative_count: number;
  positive_count: number;
  neutral_count: number;
  negative_pct: number;
  last_article_at: string;
  recent_articles: JournalistArticleItem[];
}

export interface JournalistCoverageData {
  journalists: JournalistProfile[];
  period_days: number;
  brand_id: string;
}

// ── Editorial Tone Breakdown (Phase 1) ────────────────────────────────────────

export interface ToneWeek {
  week: string;
  factual: number;
  positive_frame: number;
  negative_frame: number;
  critical: number;
}

export interface ToneBreakdownData {
  total: { factual: number; positive_frame: number; negative_frame: number; critical: number };
  weekly_trend: ToneWeek[];
  period_days: number;
  brand_id: string;
}

// ── Divergence Summary (Phase 1) ──────────────────────────────────────────────

export interface DivergentArticleItem {
  title: string;
  url: string;
  published_at: string | null;
  headline_sentiment_score: number;
  body_sentiment_score: number;
  sentiment_label: "positive" | "negative" | "neutral";
}

export interface DivergenceSummaryData {
  total_divergent_count: number;
  divergent_pct: number;
  articles: DivergentArticleItem[];
  period_days: number;
}

// ── YouTube Creator vs Audience Sentiment Split ───────────────────────────────

export interface YTSentimentBucket {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
  avg_score: number;
}

export interface YTDivergentVideo {
  title: string;
  url: string;
  portal_name: string;
  creator_label: string;
  audience_label: string;
  comment_count: number;
}

export interface YTSentimentSplitData {
  creator: YTSentimentBucket;
  audience: YTSentimentBucket;
  divergent_videos: YTDivergentVideo[];
  period_days: number;
  brand_id: string;
}

export interface IssueCategoryItem {
  category: string;
  count: number;
  positive_count: number;
  negative_count: number;
}

export interface IssueCategoriesData {
  categories: IssueCategoryItem[];
  period_days: number;
  brand_id: string;
}

// ── Screen 2: Top Influential Sources + Top Brand Advocates ───────────────────

export interface InfluentialSource {
  portal_name: string;
  impact_score: number;
  sentiment: "positive" | "negative" | "neutral";
  article_count: number;
}

export interface TopSourcesData {
  sources: InfluentialSource[];
}

export interface BrandAdvocate {
  name: string;
  source_type: string;
  article_count: number;
  total_reach: number;
}

export interface TopAdvocatesData {
  advocates: BrandAdvocate[];
}

// ── Screen 3: Competitor Sentiment Comparison ─────────────────────────────────

export interface BrandSentimentEntry {
  name: string;
  is_brand: boolean;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  count: number;
}

export interface CompetitorSentimentData {
  brands: BrandSentimentEntry[];
}

// ── Virality Alerts ───────────────────────────────────────────────────────────

export interface ViralityFlag {
  article_id: string;
  title: string;
  url: string;
  flag_level: 1 | 2 | 3;
  triggered_metrics: string[];
  history_days: number;
}

export interface ViralityAlertsData {
  flags: ViralityFlag[];
  brand_id: string;
  period_days: number;
}
