import { useQuery } from "@tanstack/react-query";
import { fetchSourceCategories } from "../lib/api";

interface Props {
  brandId: string;
  dateFrom?: string;
  dateTo?: string;
  compact?: boolean;
  onClick?: () => void;
}

export function SentimentBySourceTable({ brandId, dateFrom, dateTo, compact, onClick }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["source-categories", brandId, dateFrom, dateTo],
    queryFn: () => fetchSourceCategories(brandId, { date_from: dateFrom, date_to: dateTo }),
    staleTime: 5 * 60_000,
  });

  const cats = data?.categories ?? [];

  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";
  const displayCats = compact ? cats.slice(0, 4) : cats;

  if (compact) {
    const totalAll = cats.reduce((s, c) => s + c.count, 0);
    return (
      <div onClick={onClick} className={`bg-[#1a2744] border border-white/10 rounded-lg p-2 h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="text-[11px] font-semibold text-white mb-1.5 flex-none">Sentiment by Source</div>
        {isLoading ? (
          <div className="space-y-2">
            {[1,2,3].map(i => <div key={i} className="h-5 bg-white/8 rounded animate-pulse" />)}
          </div>
        ) : displayCats.length === 0 ? (
          <div className="text-[10px] text-white/40 py-2 text-center">No data yet.</div>
        ) : (
          <div className="flex-1 min-h-0 overflow-hidden space-y-2">
            {displayCats.map(cat => {
              const total = cat.positive + cat.neutral + cat.negative || 1;
              const posPct = Math.round((cat.positive / total) * 100);
              const neuPct = Math.round((cat.neutral / total) * 100);
              const negPct = Math.round((cat.negative / total) * 100);
              const score = Math.round(posPct * 0.6 + neuPct * 0.3 + (100 - negPct) * 0.1);
              return (
                <div key={cat.category}>
                  <div className="flex items-center justify-between text-[10px] mb-0.5">
                    <span className="text-white/70 font-medium truncate">{cat.label}</span>
                    <div className="flex items-center gap-1.5 shrink-0 ml-1">
                      <span className="text-white/40 text-[9px]">{cat.count} mentions</span>
                      <span className="text-white font-bold">{score}</span>
                    </div>
                  </div>
                  <div className="flex rounded-full overflow-hidden h-2">
                    <div className="bg-green-400" style={{ width: `${posPct}%` }} />
                    <div className="bg-white/15" style={{ width: `${neuPct}%` }} />
                    <div className="bg-red-400" style={{ width: `${negPct}%` }} />
                  </div>
                  <div className="flex justify-between text-[8px] mt-0.5 text-white/40">
                    <span className="text-green-600">{posPct}% pos</span>
                    <span>{neuPct}% neu</span>
                    <span className="text-red-500">{negPct}% neg</span>
                  </div>
                </div>
              );
            })}
            {totalAll > 0 && cats.length > 0 && (
              <div className="pt-1 border-t border-white/8 flex justify-between text-[9px] text-white/40">
                <span>All sources</span>
                <span className="font-medium text-white/60">{totalAll} total mentions</span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div onClick={onClick} className={`bg-[#1a2744] border border-white/10 rounded-xl p-4 ${clickable}`}>
      <div className="text-sm font-semibold text-white mb-3">Sentiment by Source</div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="animate-pulse space-y-1">
              <div className="h-3 bg-white/8 rounded w-24" />
              <div className="h-2 bg-white/8 rounded" />
            </div>
          ))}
        </div>
      ) : cats.length === 0 ? (
        <div className="text-xs text-white/40 py-4 text-center">No source data yet.</div>
      ) : (
        <>
          {/* Column headers */}
          <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 text-[10px] text-white/40 uppercase font-medium mb-2 px-1">
            <span>Source</span>
            <span className="text-green-400 text-right">Positive</span>
            <span className="text-white/40 text-right">Neutral</span>
            <span className="text-red-400 text-right">Negative</span>
            <span className="text-right">Score</span>
          </div>

          <div className="space-y-3">
            {cats.map(cat => {
              const total = cat.positive + cat.neutral + cat.negative || 1;
              const posPct = Math.round((cat.positive / total) * 100);
              const neuPct = Math.round((cat.neutral / total) * 100);
              const negPct = Math.round((cat.negative / total) * 100);
              const score = Math.round(posPct * 0.6 + neuPct * 0.3 + (100 - negPct) * 0.1);

              return (
                <div key={cat.category} className="space-y-1">
                  <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 items-center">
                    <span className="text-xs font-medium text-white/70 truncate">{cat.label}</span>
                    <span className="text-xs text-green-400 font-medium w-9 text-right">{posPct}%</span>
                    <span className="text-xs text-white/50 w-9 text-right">{neuPct}%</span>
                    <span className="text-xs text-red-400 w-9 text-right">{negPct}%</span>
                    <span className="text-xs font-bold text-white w-7 text-right">{score}</span>
                  </div>
                  {/* Stacked bar */}
                  <div className="flex rounded-full overflow-hidden h-1.5 bg-white/8">
                    <div className="bg-green-400 h-full" style={{ width: `${posPct}%` }} />
                    <div className="bg-white/20 h-full" style={{ width: `${neuPct}%` }} />
                    <div className="bg-red-400 h-full" style={{ width: `${negPct}%` }} />
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
