import { useQuery } from "@tanstack/react-query";
import { fetchTopics, fetchIssueClusters } from "../lib/api";
import { formatCount } from "../lib/utils";
import type { IssueCluster } from "../lib/types";

interface Props {
  brandId: string;
  compact?: boolean;
  onClick?: () => void;
}

/* ── Cluster row used in both compact and expanded modes ── */
function ClusterRow({ c, maxCount, compact }: { c: IssueCluster; maxCount: number; compact: boolean }) {
  const barPct = Math.min(100, Math.round((c.article_count / maxCount) * 100));
  const isNeg = c.net_sentiment_pct < 0;
  const netLabel = isNeg ? `${c.net_sentiment_pct}%` : `+${c.net_sentiment_pct}%`;
  const barColor = isNeg ? "bg-red-400" : "bg-green-400";
  const netColor = isNeg ? "text-red-500" : "text-green-600";

  if (compact) {
    return (
      <div className="flex items-center gap-1.5">
        <span className="text-[8px] text-gray-600 truncate flex-1 capitalize">
          {c.cluster_name.replace(/_/g, " ")}
        </span>
        {c.trend === "rising" && (
          <span className="text-[7px] text-amber-500 font-semibold shrink-0">↑</span>
        )}
        <span className={`text-[8px] font-semibold shrink-0 ${netColor}`}>{netLabel}</span>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-[12px] text-gray-700 font-medium truncate capitalize">
            {c.cluster_name.replace(/_/g, " ")}
          </span>
          {c.trend === "rising" && (
            <span className="text-[10px] bg-amber-50 text-amber-600 border border-amber-200 rounded px-1 py-px font-semibold shrink-0">
              ↑ Rising
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[11px] text-gray-400">{formatCount(c.article_count)}</span>
          <span className={`text-[12px] font-semibold w-12 text-right ${netColor}`}>{netLabel}</span>
        </div>
      </div>
      <div className="h-1.5 rounded-full bg-gray-100">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${barPct}%` }} />
      </div>
    </div>
  );
}

export function TopIssuesTable({ brandId, compact, onClick }: Props) {
  const { data: topicsData, isLoading: topicsLoading } = useQuery({
    queryKey: ["topics", brandId],
    queryFn: () => fetchTopics(brandId),
    staleTime: 5 * 60_000,
  });

  const { data: clusterData, isLoading: clustersLoading } = useQuery({
    queryKey: ["issue-clusters", brandId],
    queryFn: () => fetchIssueClusters(brandId, 30),
    staleTime: 5 * 60_000,
  });

  const isLoading = topicsLoading || clustersLoading;
  const clusters = clusterData?.clusters ?? [];
  const hasClusters = clusters.length > 0;
  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  /* ── Compact ── */
  if (compact) {
    const visibleClusters = clusters.slice(0, 5);
    const maxCount = clusters[0]?.article_count ?? 1;

    /* fallback to topic-based pos/neg split when no clusters */
    const allTopics = topicsData ?? [];
    const withNet = allTopics.map(t => {
      const total = t.positive + t.neutral + t.negative || 1;
      const posPct = Math.round((t.positive / total) * 100);
      const negPct = Math.round((t.negative / total) * 100);
      return { ...t, posPct, negPct, net: posPct - negPct };
    });
    const positiveTopics = withNet.filter(t => t.net >= 0).slice(0, 5);
    const negativeTopics = withNet.filter(t => t.net < 0).slice(0, 5);

    return (
      <div onClick={onClick} className={`bg-white border border-gray-200 rounded-lg p-2 shadow-sm h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="flex items-center justify-between mb-1 flex-none">
          <span className="text-[11px] font-semibold text-gray-800">Top Issues</span>
          <span className="text-[9px] text-gray-400">{hasClusters ? "Clusters" : "All Sources"}</span>
        </div>

        {isLoading ? (
          <div className="space-y-1.5 flex-1">
            {[1,2,3,4].map(i => <div key={i} className="h-3 bg-gray-100 rounded animate-pulse" />)}
          </div>
        ) : hasClusters ? (
          <div className="flex-1 min-h-0 overflow-hidden space-y-1">
            {visibleClusters.map(c => (
              <ClusterRow key={c.cluster_name} c={c} maxCount={maxCount} compact />
            ))}
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-hidden grid grid-cols-2 gap-x-2">
            <div className="overflow-hidden">
              <div className="text-[8px] font-bold text-green-600 uppercase tracking-wide mb-1">Positive</div>
              <div className="space-y-1">
                {positiveTopics.map(t => (
                  <div key={t.topic} className="flex items-center gap-1">
                    <span className="text-[8px] text-gray-600 truncate flex-1 capitalize">{t.topic.replace(/_/g, " ")}</span>
                    <span className="text-[8px] font-semibold text-green-600 shrink-0">+{t.net}%</span>
                  </div>
                ))}
                {positiveTopics.length === 0 && <span className="text-[8px] text-gray-400">None yet</span>}
              </div>
            </div>
            <div className="overflow-hidden">
              <div className="text-[8px] font-bold text-red-500 uppercase tracking-wide mb-1">Negative</div>
              <div className="space-y-1">
                {negativeTopics.map(t => (
                  <div key={t.topic} className="flex items-center gap-1">
                    <span className="text-[8px] text-gray-600 truncate flex-1 capitalize">{t.topic.replace(/_/g, " ")}</span>
                    <span className="text-[8px] font-semibold text-red-500 shrink-0">{t.net}%</span>
                  </div>
                ))}
                {negativeTopics.length === 0 && <span className="text-[8px] text-gray-400">None yet</span>}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  /* ── Expanded ── */
  const allTopics = topicsData ?? [];
  const withNet = allTopics.map(t => {
    const total = t.positive + t.neutral + t.negative || 1;
    const posPct = Math.round((t.positive / total) * 100);
    const negPct = Math.round((t.negative / total) * 100);
    return { ...t, posPct, negPct, net: posPct - negPct };
  });
  const positiveTopics = withNet.filter(t => t.net >= 0).slice(0, 7);
  const negativeTopics = withNet.filter(t => t.net < 0).slice(0, 7);
  const maxTopicCount = Math.max(allTopics[0]?.count ?? 1, 1);

  const visibleClusters = clusters.slice(0, 10);
  const maxClusterCount = Math.max(clusters[0]?.article_count ?? 1, 1);

  return (
    <div onClick={onClick} className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${clickable}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm font-semibold text-gray-800">Top Issues</div>
        <span className="text-[10px] text-gray-400">{hasClusters ? "Issue Clusters · 30d" : "All Sources"}</span>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1,2,3,4,5].map(i => <div key={i} className="h-4 bg-gray-100 rounded animate-pulse" />)}
        </div>
      ) : hasClusters ? (
        <div className="space-y-3">
          {visibleClusters.map(c => (
            <ClusterRow key={c.cluster_name} c={c} maxCount={maxClusterCount} compact={false} />
          ))}
        </div>
      ) : allTopics.length === 0 ? (
        <div className="text-xs text-gray-400 py-6 text-center">No topic data yet.</div>
      ) : (
        <div className="grid grid-cols-2 gap-x-6">
          <div>
            <div className="text-[10px] font-bold text-green-600 uppercase tracking-wide mb-3">Top Positive Issues</div>
            <div className="space-y-2.5">
              {positiveTopics.map(t => (
                <div key={t.topic}>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-[12px] text-gray-700 font-medium truncate capitalize">{t.topic.replace(/_/g, " ")}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[11px] text-gray-400">{formatCount(t.count)}</span>
                      <span className="text-[12px] font-semibold text-green-600 w-10 text-right">+{t.net}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 rounded-full bg-gray-100">
                    <div className="h-full rounded-full bg-green-400" style={{ width: `${(t.count / maxTopicCount) * 100}%` }} />
                  </div>
                </div>
              ))}
              {positiveTopics.length === 0 && <div className="text-[11px] text-gray-400 py-2">No positive issues found.</div>}
            </div>
          </div>
          <div>
            <div className="text-[10px] font-bold text-red-500 uppercase tracking-wide mb-3">Top Negative Issues</div>
            <div className="space-y-2.5">
              {negativeTopics.map(t => (
                <div key={t.topic}>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-[12px] text-gray-700 font-medium truncate capitalize">{t.topic.replace(/_/g, " ")}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[11px] text-gray-400">{formatCount(t.count)}</span>
                      <span className="text-[12px] font-semibold text-red-500 w-10 text-right">{t.net}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 rounded-full bg-gray-100">
                    <div className="h-full rounded-full bg-red-400" style={{ width: `${(t.count / maxTopicCount) * 100}%` }} />
                  </div>
                </div>
              ))}
              {negativeTopics.length === 0 && <div className="text-[11px] text-gray-400 py-2">No negative issues found.</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
