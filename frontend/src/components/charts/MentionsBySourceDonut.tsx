import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useQuery } from "@tanstack/react-query";
import { fetchSourceCategories } from "../../lib/api";
import type { SourceCategoryPoint } from "../../lib/types";
import { formatCount, tierBadge } from "../../lib/utils";

interface Props {
  brandId: string;
  dateFrom?: string;
  dateTo?: string;
  compact?: boolean;
  onClick?: () => void;
}

interface SourceTooltipProps { active?: boolean; payload?: Array<{ payload: SourceCategoryPoint }> }

function SourceTooltip({ active, payload }: SourceTooltipProps) {
  if (!active || !payload?.length) return null;
  const cat = payload[0].payload;
  const td = cat.tier_distribution;
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs shadow-md min-w-[160px]">
      <div className="font-semibold text-gray-800 mb-1">{cat.label}</div>
      <div className="text-gray-500 mb-1.5">
        {formatCount(cat.count)} mentions ({cat.pct}%)
      </div>
      <div className="text-[10px] space-y-0.5">
        {td.tier1 > 0 && <div className="text-violet-600">Tier 1 (national): {td.tier1}</div>}
        {td.tier2 > 0 && <div className="text-blue-600">Tier 2 (regional): {td.tier2}</div>}
        {td.tier3 > 0 && <div className="text-gray-600">Tier 3 (trade): {td.tier3}</div>}
        {td.tier4 > 0 && <div className="text-gray-400">Tier 4 (community): {td.tier4}</div>}
        {td.youtube > 0 && <div className="text-red-500">YouTube: {td.youtube}</div>}
      </div>
      {cat.category !== "youtube" && (
        <div className="mt-1.5 text-[10px] text-gray-400">
          Avg credibility: {cat.avg_credibility.toFixed(2)}
        </div>
      )}
    </div>
  );
}

export function MentionsBySourceDonut({ brandId, dateFrom, dateTo, compact, onClick }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["source-categories", brandId, dateFrom, dateTo],
    queryFn: () => fetchSourceCategories(brandId, { date_from: dateFrom, date_to: dateTo }),
    staleTime: 5 * 60_000,
  });

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <div className="h-5 w-44 bg-gray-100 rounded animate-pulse mb-4" />
        <div className="h-[180px] bg-gray-50 rounded-lg animate-pulse" />
      </div>
    );
  }

  const cats = data?.categories ?? [];
  const total = data?.total ?? 0;

  if (cats.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <div className="text-sm font-semibold text-gray-800 mb-3">Mentions by Source</div>
        <div className="h-[140px] flex items-center justify-center text-gray-400 text-sm">
          No source data yet.
        </div>
      </div>
    );
  }

  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  if (compact) {
    return (
      <div onClick={onClick} className={`bg-white border border-gray-200 rounded-lg p-2 shadow-sm h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="text-[11px] font-semibold text-gray-800 mb-1 flex-none">Mentions by Source</div>
        <div className="flex items-center gap-2 flex-1 min-h-0">
          <div className="shrink-0 relative w-[90px] h-[90px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={cats} cx="50%" cy="50%" innerRadius={26} outerRadius={40} dataKey="count" paddingAngle={2} startAngle={90} endAngle={-270}>
                  {cats.map(cat => <Cell key={cat.category} fill={cat.color} strokeWidth={0} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[11px] font-bold text-gray-900">{formatCount(total)}</span>
              <span className="text-[8px] text-gray-400">total</span>
            </div>
          </div>
          <div className="flex-1 space-y-1.5 min-w-0 overflow-hidden">
            {cats.slice(0, 5).map(cat => {
              const t = cat.positive + cat.neutral + cat.negative || 1;
              const posPct = Math.round(cat.positive / t * 100);
              const negPct = Math.round(cat.negative / t * 100);
              const neuPct = 100 - posPct - negPct;
              return (
                <div key={cat.category}>
                  <div className="flex items-center gap-1 text-[9px] mb-0.5">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: cat.color }} />
                    <span className="text-gray-600 truncate flex-1">{cat.label}</span>
                    <span className="text-gray-500 font-medium shrink-0">{cat.pct}%</span>
                  </div>
                  <div className="flex rounded-full overflow-hidden h-1 ml-3">
                    <div className="bg-green-400" style={{ width: `${posPct}%` }} />
                    <div className="bg-gray-200" style={{ width: `${neuPct}%` }} />
                    <div className="bg-red-400" style={{ width: `${negPct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div onClick={onClick} className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${clickable}`}>
      <div className="text-sm font-semibold text-gray-800 mb-3">Mentions by Source</div>
      <div className="flex items-center gap-4">
        {/* Donut */}
        <div className="shrink-0 relative w-[140px] h-[140px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={cats}
                cx="50%" cy="50%"
                innerRadius={42} outerRadius={62}
                dataKey="count"
                paddingAngle={2}
                startAngle={90} endAngle={-270}
              >
                {cats.map(cat => (
                  <Cell key={cat.category} fill={cat.color} strokeWidth={0} />
                ))}
              </Pie>
              <Tooltip content={<SourceTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          {/* Centre label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-sm font-bold text-gray-900">{formatCount(total)}</span>
            <span className="text-[10px] text-gray-400">total</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-2 min-w-0">
          {cats.map(cat => {
            const tb = cat.avg_credibility >= 0.87
              ? tierBadge(1)
              : cat.avg_credibility >= 0.78
              ? tierBadge(2)
              : cat.category === "youtube"
              ? tierBadge(0)
              : tierBadge(3);
            return (
              <div key={cat.category} className="flex items-center gap-2 text-xs">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: cat.color }}
                />
                <span className="text-gray-700 truncate flex-1">{cat.label}</span>
                <span className="text-gray-500 shrink-0">{formatCount(cat.count)}</span>
                <span className="text-gray-400 shrink-0">{cat.pct}%</span>
                <span className={`text-[9px] px-1 rounded shrink-0 ${tb.bg} ${tb.color}`}>
                  {tb.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
