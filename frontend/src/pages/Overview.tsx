import { useQuery } from "@tanstack/react-query";
import { fetchOverview } from "../lib/api";
import { KPICard } from "../components/cards/KPICard";
import { SentimentTrendChart } from "../components/charts/SentimentTrendChart";
import { MentionsList } from "../components/mentions/MentionsList";

interface Props {
  brandId: string;
  brandName?: string;
}

export function Overview({ brandId, brandName }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["overview", brandId],
    queryFn: () => fetchOverview(brandId),
    refetchInterval: 60_000,
  });

  if (isLoading) return <div className="text-gray-400 p-8">Loading...</div>;
  if (error || !data || !data.kpi) return <div className="text-red-400 p-8">Failed to load dashboard. No data yet — the pipeline runs hourly.</div>;

  return (
    <div className="p-6 space-y-6">
      {brandName && (
        <div>
          <h2 className="text-xl font-bold text-gray-100">{brandName}</h2>
          <p className="text-xs text-gray-500 mt-0.5">Media sentiment report · last 7 days</p>
        </div>
      )}
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
                  <span className="truncate max-w-[140px]">{s.portal_id.replace(/_/g, " ")}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-[10px] font-mono px-1 rounded ${
                      s.avg_credibility >= 0.85
                        ? "bg-green-900/40 text-green-400"
                        : s.avg_credibility >= 0.75
                        ? "bg-yellow-900/40 text-yellow-400"
                        : "bg-gray-800 text-gray-500"
                    }`}>
                      {s.avg_credibility.toFixed(2)}
                    </span>
                    <span>{s.count}</span>
                  </div>
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

      <MentionsList brandId={brandId} />

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
