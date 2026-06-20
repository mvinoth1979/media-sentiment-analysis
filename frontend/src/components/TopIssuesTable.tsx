import { useQuery } from "@tanstack/react-query";
import { fetchTopics } from "../lib/api";
import { formatCount } from "../lib/utils";

interface Props {
  brandId: string;
  compact?: boolean;
  onClick?: () => void;
}

export function TopIssuesTable({ brandId, compact, onClick }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["topics", brandId],
    queryFn: () => fetchTopics(brandId),
    staleTime: 5 * 60_000,
  });

  const limit = compact ? 8 : 10;
  const topics = (data ?? []).slice(0, limit);
  const maxCount = topics[0]?.count ?? 1;
  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  if (compact) {
    return (
      <div onClick={onClick} className={`bg-white border border-gray-200 rounded-lg p-2 shadow-sm h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="flex items-center justify-between mb-1 flex-none">
          <span className="text-[11px] font-semibold text-gray-800">Top Issues</span>
          <span className="text-[9px] text-gray-400">All Sources</span>
        </div>
        {isLoading ? (
          <div className="space-y-1.5">
            {[1,2,3,4,5].map(i => <div key={i} className="h-3 bg-gray-100 rounded animate-pulse" />)}
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-hidden space-y-1">
            {topics.map(t => {
              const total = t.positive + t.neutral + t.negative || 1;
              const negPct = Math.round((t.negative / total) * 100);
              const posPct = Math.round((t.positive / total) * 100);
              const net = posPct - negPct;
              const isPos = net >= 0;
              return (
                <div key={t.topic} className="flex items-center gap-1">
                  <span className="text-[9px] text-gray-700 truncate flex-1 capitalize">{t.topic.replace(/_/g, " ")}</span>
                  <span className="text-[8px] text-gray-400 shrink-0 w-5 text-right">{t.count}</span>
                  <div className="w-8 h-1 bg-gray-100 rounded-full shrink-0">
                    <div className={`h-full rounded-full ${isPos ? "bg-green-400" : "bg-red-400"}`} style={{ width: `${(t.count / maxCount) * 100}%` }} />
                  </div>
                  <span className={`text-[9px] font-semibold w-7 text-right shrink-0 ${isPos ? "text-green-600" : "text-red-500"}`}>{isPos?"+":""}{net}%</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <div onClick={onClick} className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${clickable}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-800">Top Issues</div>
        <span className="text-[10px] text-gray-400">(All Sources)</span>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="animate-pulse flex gap-3 items-center">
              <div className="h-3 bg-gray-100 rounded flex-1" />
              <div className="h-3 bg-gray-100 rounded w-12" />
              <div className="h-3 bg-gray-100 rounded w-10" />
            </div>
          ))}
        </div>
      ) : topics.length === 0 ? (
        <div className="text-xs text-gray-400 py-4 text-center">No topic data yet.</div>
      ) : (
        <>
          <div className="grid grid-cols-[1fr_auto_auto] gap-x-3 text-[10px] text-gray-400 uppercase font-medium mb-2 px-1">
            <span>Issue</span>
            <span className="text-right">Mentions</span>
            <span className="text-right">Sentiment</span>
          </div>
          <div className="space-y-2.5">
            {topics.map(t => {
              const total = t.positive + t.neutral + t.negative || 1;
              const negPct = Math.round((t.negative / total) * 100);
              const posPct = Math.round((t.positive / total) * 100);
              const netSentiment = posPct - negPct;
              const isPositive = netSentiment >= 0;

              return (
                <div key={t.topic} className="space-y-1">
                  <div className="grid grid-cols-[1fr_auto_auto] gap-x-3 items-center">
                    <span className="text-xs text-gray-700 font-medium truncate capitalize">
                      {t.topic.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-gray-600 font-medium w-12 text-right">
                      {formatCount(t.count)}
                    </span>
                    <span className={`text-xs font-semibold w-12 text-right ${
                      isPositive ? "text-green-600" : "text-red-500"
                    }`}>
                      {isPositive ? "+" : ""}{netSentiment}%
                    </span>
                  </div>
                  {/* Rank bar */}
                  <div className="h-1 rounded-full bg-gray-100">
                    <div
                      className={`h-full rounded-full ${isPositive ? "bg-green-400" : "bg-red-400"}`}
                      style={{ width: `${(t.count / maxCount) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
