import { useQuery } from "@tanstack/react-query";
import { fetchSourceCategories } from "../lib/api";

interface Props {
  brandId: string;
  dateFrom?: string;
  dateTo?: string;
}

export function SentimentBySourceTable({ brandId, dateFrom, dateTo }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["source-categories", brandId, dateFrom, dateTo],
    queryFn: () => fetchSourceCategories(brandId, { date_from: dateFrom, date_to: dateTo }),
    staleTime: 5 * 60_000,
  });

  const cats = data?.categories ?? [];

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="text-sm font-semibold text-gray-800 mb-3">Sentiment by Source</div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="animate-pulse space-y-1">
              <div className="h-3 bg-gray-100 rounded w-24" />
              <div className="h-2 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      ) : cats.length === 0 ? (
        <div className="text-xs text-gray-400 py-4 text-center">No source data yet.</div>
      ) : (
        <>
          {/* Column headers */}
          <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 text-[10px] text-gray-400 uppercase font-medium mb-2 px-1">
            <span>Source</span>
            <span className="text-green-600 text-right">Positive</span>
            <span className="text-gray-500 text-right">Neutral</span>
            <span className="text-red-500 text-right">Negative</span>
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
                    <span className="text-xs font-medium text-gray-700 truncate">{cat.label}</span>
                    <span className="text-xs text-green-600 font-medium w-9 text-right">{posPct}%</span>
                    <span className="text-xs text-gray-500 w-9 text-right">{neuPct}%</span>
                    <span className="text-xs text-red-500 w-9 text-right">{negPct}%</span>
                    <span className="text-xs font-bold text-gray-800 w-7 text-right">{score}</span>
                  </div>
                  {/* Stacked bar */}
                  <div className="flex rounded-full overflow-hidden h-1.5 bg-gray-100">
                    <div className="bg-green-400 h-full" style={{ width: `${posPct}%` }} />
                    <div className="bg-gray-300 h-full" style={{ width: `${neuPct}%` }} />
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
