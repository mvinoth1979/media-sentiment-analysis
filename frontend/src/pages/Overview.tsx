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

function formatDelta(value: number | null, unit: string): string | undefined {
  if (value == null) return undefined;
  const sign = value > 0 ? "+" : "";
  return `${sign}${value}${unit} vs last week`;
}

function formatLastProcessed(iso: string | null): string {
  if (!iso) return "—";
  const minutes = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function Overview({ brandId, brandName }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["overview", brandId],
    queryFn: () => fetchOverview(brandId),
    refetchInterval: (query) =>
      query.state.data?.pipeline_status === "running" ? 10_000 : 60_000,
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
          <p className="text-xs text-gray-500 mt-0.5">
            Media sentiment report · last 7 days · Last updated {formatLastProcessed(data.last_processed_at)}
          </p>
        </div>
      )}

      {/* Pipeline status banner */}
      {data.pipeline_status === "running" && (
        <div className="flex items-center gap-3 bg-indigo-950/60 border border-indigo-800/60 rounded-lg px-4 py-2.5 text-sm">
          <span className="relative flex h-2.5 w-2.5 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500" />
          </span>
          <span className="text-indigo-300 font-medium">Pipeline running</span>
          <span className="text-indigo-500">— collecting and analysing new articles…</span>
        </div>
      )}
      {data.pipeline_status === "idle" && data.pipeline_last_stats?.processed > 0 && (
        <div className="flex items-center gap-3 bg-gray-900/40 border border-gray-800 rounded-lg px-4 py-2 text-xs text-gray-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
          Last run: collected {data.pipeline_last_stats.collected}, processed {data.pipeline_last_stats.processed}
          {data.pipeline_last_stats.errors > 0 && (
            <span className="text-amber-500">, {data.pipeline_last_stats.errors} errors</span>
          )}
        </div>
      )}

      {/* KPI row + Pie chart */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="flex flex-row sm:flex-col gap-4">
          <div className="flex-1">
            <KPICard
              label="Perception Score"
              value={kpi.perception_score.toFixed(1)}
              color="purple"
              sub={formatDelta(kpi.perception_score_delta, " pts")}
            />
          </div>
          <div className="flex-1">
            <KPICard
              label="Total Mentions"
              value={kpi.total}
              color="blue"
              sub={formatDelta(kpi.mentions_delta_pct, "%")}
            />
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
          <SentimentTrendChart brandId={brandId} data={data.trend} />
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
      <MentionsList
        brandId={brandId}
        portals={data.top_sources.map(s => s.portal_id)}
        topics={data.top_topics}
        selectable
      />

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
