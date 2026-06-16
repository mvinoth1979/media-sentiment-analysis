import { useQuery } from "@tanstack/react-query";
import { fetchOverview } from "../lib/api";
import { KPICard } from "../components/cards/KPICard";
import { SentimentTrendChart } from "../components/charts/SentimentTrendChart";
import { SentimentPieChart } from "../components/charts/SentimentPieChart";
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
  if (error || !data || !data.kpi) return (
    <div className="text-red-400 p-8">Failed to load dashboard. No data yet — the pipeline runs hourly.</div>
  );

  const { kpi } = data;

  return (
    <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">

      {/* Brand header */}
      {brandName && (
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-gray-100">{brandName}</h2>
          <p className="text-xs text-gray-500 mt-0.5">Media sentiment report · last 7 days</p>
        </div>
      )}

      {/* KPI row + Pie chart */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="flex flex-row sm:flex-col gap-4">
          <div className="flex-1">
            <KPICard label="Perception Score" value={kpi.perception_score.toFixed(1)} color="purple" />
          </div>
          <div className="flex-1">
            <KPICard label="Total Mentions" value={kpi.total} color="blue" />
          </div>
        </div>
        <div className="sm:col-span-2">
          <SentimentPieChart
            positive={kpi.positive}
            negative={kpi.negative}
            neutral={kpi.neutral}
            total={kpi.total}
          />
        </div>
      </div>

      {/* Trend chart + Top Sources */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
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
                       style={{ width: `${Math.min(100, (s.count / (kpi.total || 1)) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mentions table */}
      <MentionsList brandId={brandId} />

      {/* Topics + Keywords */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
