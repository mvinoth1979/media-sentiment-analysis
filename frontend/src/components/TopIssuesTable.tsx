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

  const allTopics = data ?? [];
  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  /* Split topics into positive vs negative buckets by net sentiment */
  const withNet = allTopics.map(t => {
    const total = t.positive + t.neutral + t.negative || 1;
    const posPct = Math.round((t.positive / total) * 100);
    const negPct = Math.round((t.negative / total) * 100);
    return { ...t, posPct, negPct, net: posPct - negPct };
  });
  const positiveTopics = withNet.filter(t => t.net >= 0).slice(0, compact ? 5 : 7);
  const negativeTopics = withNet.filter(t => t.net < 0).slice(0, compact ? 5 : 7);
  const maxCount = Math.max(allTopics[0]?.count ?? 1, 1);

  /* ── Compact ── */
  if (compact) {
    return (
      <div onClick={onClick} className={`bg-white border border-gray-200 rounded-lg p-2 shadow-sm h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="flex items-center justify-between mb-1 flex-none">
          <span className="text-[11px] font-semibold text-gray-800">Top Issues</span>
          <span className="text-[9px] text-gray-400">All Sources</span>
        </div>

        {isLoading ? (
          <div className="space-y-1.5 flex-1">
            {[1,2,3,4].map(i => <div key={i} className="h-3 bg-gray-100 rounded animate-pulse" />)}
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-hidden grid grid-cols-2 gap-x-2">
            {/* Positive column */}
            <div className="overflow-hidden">
              <div className="text-[8px] font-bold text-green-600 uppercase tracking-wide mb-1">Positive</div>
              <div className="space-y-1">
                {positiveTopics.map(t => (
                  <div key={t.topic} className="flex items-center gap-1">
                    <span className="text-[8px] text-gray-600 truncate flex-1 capitalize">{t.topic.replace(/_/g, " ")}</span>
                    <span className="text-[8px] font-semibold text-green-600 shrink-0">+{t.net}%</span>
                  </div>
                ))}
                {positiveTopics.length === 0 && (
                  <span className="text-[8px] text-gray-400">None yet</span>
                )}
              </div>
            </div>

            {/* Negative column */}
            <div className="overflow-hidden">
              <div className="text-[8px] font-bold text-red-500 uppercase tracking-wide mb-1">Negative</div>
              <div className="space-y-1">
                {negativeTopics.map(t => (
                  <div key={t.topic} className="flex items-center gap-1">
                    <span className="text-[8px] text-gray-600 truncate flex-1 capitalize">{t.topic.replace(/_/g, " ")}</span>
                    <span className="text-[8px] font-semibold text-red-500 shrink-0">{t.net}%</span>
                  </div>
                ))}
                {negativeTopics.length === 0 && (
                  <span className="text-[8px] text-gray-400">None yet</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  /* ── Expanded — matches Review Sites two-column layout ── */
  return (
    <div onClick={onClick} className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${clickable}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm font-semibold text-gray-800">Top Issues</div>
        <span className="text-[10px] text-gray-400">All Sources</span>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-x-6">
          {[0, 1].map(col => (
            <div key={col} className="space-y-2">
              <div className="h-3 bg-gray-100 rounded w-24 animate-pulse" />
              {[1,2,3,4,5].map(i => <div key={i} className="h-3 bg-gray-100 rounded animate-pulse" />)}
            </div>
          ))}
        </div>
      ) : allTopics.length === 0 ? (
        <div className="text-xs text-gray-400 py-6 text-center">No topic data yet.</div>
      ) : (
        <div className="grid grid-cols-2 gap-x-6">
          {/* Positive issues column */}
          <div>
            <div className="text-[10px] font-bold text-green-600 uppercase tracking-wide mb-3">
              Top Positive Issues
            </div>
            <div className="space-y-2.5">
              {positiveTopics.map(t => (
                <div key={t.topic}>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-[12px] text-gray-700 font-medium truncate capitalize">
                      {t.topic.replace(/_/g, " ")}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[11px] text-gray-400">{formatCount(t.count)}</span>
                      <span className="text-[12px] font-semibold text-green-600 w-10 text-right">+{t.net}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 rounded-full bg-gray-100">
                    <div className="h-full rounded-full bg-green-400" style={{ width: `${(t.count / maxCount) * 100}%` }} />
                  </div>
                </div>
              ))}
              {positiveTopics.length === 0 && (
                <div className="text-[11px] text-gray-400 py-2">No positive issues found.</div>
              )}
            </div>
          </div>

          {/* Negative issues column */}
          <div>
            <div className="text-[10px] font-bold text-red-500 uppercase tracking-wide mb-3">
              Top Negative Issues
            </div>
            <div className="space-y-2.5">
              {negativeTopics.map(t => (
                <div key={t.topic}>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-[12px] text-gray-700 font-medium truncate capitalize">
                      {t.topic.replace(/_/g, " ")}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[11px] text-gray-400">{formatCount(t.count)}</span>
                      <span className="text-[12px] font-semibold text-red-500 w-10 text-right">{t.net}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 rounded-full bg-gray-100">
                    <div className="h-full rounded-full bg-red-400" style={{ width: `${(t.count / maxCount) * 100}%` }} />
                  </div>
                </div>
              ))}
              {negativeTopics.length === 0 && (
                <div className="text-[11px] text-gray-400 py-2">No negative issues found.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
