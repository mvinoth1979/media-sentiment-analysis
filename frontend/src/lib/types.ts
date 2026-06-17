export interface KPISummary {
  perception_score: number;
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
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
  entities: string[];
  topics: string[];
  keywords: string[];
  states_mentioned: string[];
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
