import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchTopics, fetchIssueClusters, fetchIssueCategories } from "../lib/api";
import { formatCount } from "../lib/utils";
import type { IssueCluster, IssueCategoryItem } from "../lib/types";

interface Props {
  brandId: string;
  compact?: boolean;
  onClick?: () => void;
  onClusterClick?: (clusterName: string) => void;
  onCategoryClick?: (category: string) => void;
}

/* ── Expanded-mode cluster row ── */
function ClusterRow({ c, maxCount }: { c: IssueCluster; maxCount: number }) {
  const barPct = Math.min(100, Math.round((c.article_count / maxCount) * 100));
  const isNeg = c.net_sentiment_pct < 0;
  const netLabel = isNeg ? `${c.net_sentiment_pct}%` : `+${c.net_sentiment_pct}%`;
  const barColor = isNeg ? "bg-red-400" : "bg-green-400";
  const netColor = isNeg ? "text-red-500" : "text-green-600";

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

const CATEGORY_LABELS: Record<string, string> = {
  financial_performance:  "Financial Performance",
  regulatory_compliance:  "Regulatory & Compliance",
  product_quality:        "Product Quality",
  leadership_governance:  "Leadership & Governance",
  crisis_controversy:     "Crisis & Controversy",
  awards_recognition:     "Awards & Recognition",
  csr_sustainability:     "CSR & Sustainability",
  policy_government:      "Policy & Government",
  competitive_landscape:  "Competitive Landscape",
  customer_experience:    "Customer Experience",
  brand_advocacy:         "Brand Advocacy",
  market_opportunity:     "Market Opportunity",
  other:                  "Other",
};

const CATEGORY_ACCENTS: Record<string, string> = {
  crisis_controversy:    "border-l-red-400",
  regulatory_compliance: "border-l-red-400",
  awards_recognition:    "border-l-green-400",
  brand_advocacy:        "border-l-green-400",
  financial_performance: "border-l-indigo-400",
};

function CategoryRow({ c, maxCount }: { c: IssueCategoryItem; maxCount: number }) {
  const total = c.count || 1;
  const posPct = Math.round((c.positive_count / total) * 100);
  const negPct = Math.round((c.negative_count / total) * 100);
  const barPct = Math.min(100, Math.round((c.count / maxCount) * 100));
  const accent = CATEGORY_ACCENTS[c.category] ?? "border-l-gray-300";
  const label = CATEGORY_LABELS[c.category] ?? c.category.replace(/_/g, " ");

  return (
    <div className={`pl-2 border-l-2 ${accent}`}>
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-[12px] text-gray-700 font-medium">{label}</span>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] text-green-600">{posPct}%▲</span>
          <span className="text-[10px] text-red-500">{negPct}%▼</span>
          <span className="text-[11px] text-gray-400">{formatCount(c.count)}</span>
        </div>
      </div>
      <div className="h-1.5 rounded-full bg-gray-100">
        <div className="h-full rounded-full bg-indigo-400" style={{ width: `${barPct}%` }} />
      </div>
    </div>
  );
}

export function TopIssuesTable({ brandId, compact, onClick, onClusterClick, onCategoryClick }: Props) {
  const [viewMode, setViewMode] = useState<"clusters" | "categories">("clusters");

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

  const { data: categoryData, isLoading: categoriesLoading } = useQuery({
    queryKey: ["issue-categories", brandId],
    queryFn: () => fetchIssueCategories(brandId, 30),
    staleTime: 5 * 60_000,
  });

  const isLoading = topicsLoading || clustersLoading || (viewMode === "categories" && categoriesLoading);
  const clusters = clusterData?.clusters ?? [];
  const hasClusters = clusters.length > 0;
  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  /* ── Compact — mirrors expanded ClusterRow design ── */
  if (compact) {
    const compactRows = hasClusters ? clusters.slice(0, 6) : [];
    const maxCount = Math.max(compactRows[0]?.article_count ?? 1, 1);
    // Only block on clusters; topics loading is irrelevant for compact
    const compactLoading = clustersLoading;

    return (
      <div
        onClick={onClick}
        className={`bg-white border border-gray-200 rounded-lg p-2.5 shadow-sm h-full flex flex-col overflow-hidden ${clickable}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-1.5 flex-none">
          <span className="text-[11px] font-semibold text-gray-800">Top Issues</span>
          <span className="text-[10px] text-gray-400">(All Sources)</span>
        </div>

        {/* Column headers */}
        <div className="flex items-center justify-between mb-1 pb-1 border-b border-gray-100 flex-none">
          <span className="text-[9px] font-semibold text-gray-400 uppercase tracking-wide">Issue</span>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[9px] font-semibold text-gray-400 uppercase tracking-wide">Mentions</span>
            <span className="text-[9px] font-semibold text-gray-400 uppercase tracking-wide w-10 text-right">Sentiment</span>
          </div>
        </div>

        {compactLoading ? (
          <div className="space-y-2 flex-1 pt-1">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="space-y-1">
                <div className="h-2.5 bg-gray-100 rounded animate-pulse w-3/4" />
                <div className="h-1.5 bg-gray-100 rounded animate-pulse w-1/2" />
              </div>
            ))}
          </div>
        ) : compactRows.length > 0 ? (
          <div className="flex-1 min-h-0 overflow-hidden space-y-2">
            {compactRows.map(c => {
              const barPct = Math.min(100, Math.round((c.article_count / maxCount) * 100));
              const isNeg = c.net_sentiment_pct < 0;
              const netLabel = isNeg ? `${c.net_sentiment_pct}%` : `+${c.net_sentiment_pct}%`;
              const barColor = isNeg ? "bg-red-400" : "bg-green-400";
              const netColor = isNeg ? "text-red-500" : "text-green-600";
              return (
                <div key={c.cluster_name}>
                  <div className="flex items-center justify-between gap-2 mb-0.5">
                    <div className="flex items-center gap-1 min-w-0">
                      <span className="text-[11px] text-gray-700 font-medium truncate capitalize">
                        {c.cluster_name.replace(/_/g, " ")}
                      </span>
                      {c.trend === "rising" && (
                        <span className="text-[9px] text-amber-500 font-semibold shrink-0">↑</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] text-gray-400">{formatCount(c.article_count)}</span>
                      <span className={`text-[10px] font-semibold w-10 text-right ${netColor}`}>{netLabel}</span>
                    </div>
                  </div>
                  <div className="h-1.5 rounded-full bg-gray-100">
                    <div className={`h-full rounded-full ${barColor}`} style={{ width: `${barPct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <span className="text-[9px] text-gray-400 text-center">
              Populates after next pipeline run
            </span>
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

  const categoryItems = categoryData?.categories ?? [];
  const maxCatCount = categoryItems[0]?.count ?? 1;

  return (
    <div onClick={onClick} className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${clickable}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm font-semibold text-gray-800">Top Issues</div>
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
          <button
            onClick={e => { e.stopPropagation(); setViewMode("clusters"); }}
            className={`text-[11px] px-2.5 py-1 rounded-md transition-colors ${viewMode === "clusters" ? "bg-white text-gray-800 shadow-sm font-medium" : "text-gray-500 hover:text-gray-700"}`}
          >Clusters</button>
          <button
            onClick={e => { e.stopPropagation(); setViewMode("categories"); }}
            className={`text-[11px] px-2.5 py-1 rounded-md transition-colors ${viewMode === "categories" ? "bg-white text-gray-800 shadow-sm font-medium" : "text-gray-500 hover:text-gray-700"}`}
          >Categories</button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-4 bg-gray-100 rounded animate-pulse" />)}
        </div>
      ) : viewMode === "categories" ? (
        categoryItems.length > 0 ? (
          <div className="space-y-3">
            {categoryItems.map(c => (
              <div
                key={c.category}
                className={onCategoryClick ? "cursor-pointer rounded hover:bg-blue-50 px-1 -mx-1" : ""}
                onClick={onCategoryClick ? (e) => { e.stopPropagation(); onCategoryClick(c.category); } : undefined}
              >
                <CategoryRow c={c} maxCount={maxCatCount} />
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-gray-400 py-8 text-center">
            Issue category data will populate after the next pipeline run.
          </div>
        )
      ) : hasClusters ? (
        <div className="space-y-3">
          {visibleClusters.map(c => (
            <div
              key={c.cluster_name}
              className={onClusterClick ? "cursor-pointer rounded hover:bg-blue-50 px-1 -mx-1" : ""}
              onClick={onClusterClick ? (e) => { e.stopPropagation(); onClusterClick(c.cluster_name); } : undefined}
            >
              <ClusterRow c={c} maxCount={maxClusterCount} />
            </div>
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
