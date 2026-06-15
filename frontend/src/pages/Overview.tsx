import { useQuery } from "@tanstack/react-query";
import { fetchOverview } from "../lib/api";
import { KPICard } from "../components/cards/KPICard";
import { SentimentTrendChart } from "../components/charts/SentimentTrendChart";
import { SentimentBadge } from "../components/ui/SentimentBadge";
import type { ArticleItem } from "../lib/types";

const BRAND_ID = import.meta.env.VITE_BRAND_ID || "";

export function Overview() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["overview", BRAND_ID],
    queryFn: () => fetchOverview(BRAND_ID),
    refetchInterval: 60_000,
  });

  if (isLoading) return <div className="text-gray-400 p-8">Loading...</div>;
  if (error || !data || !data.kpi) return <div className="text-red-400 p-8">Failed to load dashboard. No data yet — the pipeline runs hourly.</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-5 gap-4">
        <KPICard label="Perception Score" value={data.kpi.perception_score.toFixed(1)} color="purple" />
        <KPICard label="Total Mentions"   value={data.kpi.total} color="blue" />
        <KPICard label="Positive"  value={`${data.kpi.positive_pct}%`} sub={`${data.kpi.positive} articles`}  color="green" />
        <KPICard label="Negative"  value={`${data.kpi.negative_pct}%`} sub={`${data.kpi.negative} articles`}  color="red" />
        <KPICard label="Neutral"   value={`${data.kpi.neutral_pct}%`}  sub={`${data.kpi.neutral} articles`}   color="yellow" />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <SentimentTrendChart data={data.trend} />
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-200 mb-3">Top Sources</div>
          <div className="space-y-2">
            {data.top_sources.map(s => (
              <div key={s.portal_id}>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>{s.portal_id.replace(/_/g, " ")}</span>
                  <span>{s.count}</span>
                </div>
                <div className="bg-gray-800 rounded h-1.5">
                  <div className="bg-indigo-500 h-full rounded"
                       style={{ width: `${Math.min(100, (s.count / (data.kpi.total || 1)) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div className="text-sm font-semibold text-gray-200 mb-3">Recent Mentions</div>
        <div className="space-y-3">
          {data.recent_mentions.map((a: ArticleItem) => (
            <div key={a.id} className="border-l-2 border-gray-700 pl-3">
              <div className="text-xs text-gray-500 mb-1">
                {a.portal_id.replace(/_/g, " ")} · {a.language.toUpperCase()} ·{" "}
                {a.published_at ? new Date(a.published_at).toLocaleString("en-IN") : ""}
              </div>
              <a href={a.url} target="_blank" rel="noreferrer"
                 className="text-sm text-gray-200 hover:text-indigo-400 line-clamp-2">
                {a.title}
              </a>
              <div className="mt-1">
                <SentimentBadge label={a.sentiment_label} />
                <span className="text-xs text-gray-600 ml-2">{a.sentiment_score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-200 mb-3">Topics</div>
          <div className="flex flex-wrap gap-2">
            {data.top_topics.map(t => (
              <span key={t} className="bg-blue-900/30 text-blue-300 text-xs px-2 py-1 rounded-full border border-blue-800">
                {t.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-200 mb-3">Keywords</div>
          <div className="flex flex-wrap gap-2">
            {data.top_keywords.map(k => (
              <span key={k} className="bg-gray-800 text-gray-300 text-xs px-2 py-1 rounded-full">
                {k}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
