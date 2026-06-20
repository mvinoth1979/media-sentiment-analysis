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
  alert_type: "perception_score_below" | "negative_pct_above" | "mention_spike";
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
