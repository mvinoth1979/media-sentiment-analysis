export interface KPISummary {
  perception_score: number;
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
}

export interface TrendPoint { time: string; value: number; }

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
  entities: string[];
  topics: string[];
  keywords: string[];
  model_used: string;
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

export interface OverviewData {
  kpi: KPISummary;
  trend: TrendPoint[];
  recent_mentions: ArticleItem[];
  top_sources: SourceStat[];
  top_keywords: string[];
  top_topics: string[];
  last_processed_at: string | null;
}
