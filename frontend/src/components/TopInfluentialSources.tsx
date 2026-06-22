import { useQuery } from "@tanstack/react-query";
import { fetchTopSources } from "../lib/api";
import type { InfluentialSource } from "../lib/types";

interface Props {
  brandId: string;
  days?: number;
}

const SENTIMENT_STYLE: Record<string, string> = {
  negative: "bg-red-500/15 text-red-400",
  positive: "bg-emerald-500/15 text-emerald-400",
  neutral:  "bg-white/10 text-white/50",
};

const RANK_COLORS = ["text-amber-400", "text-white/60", "text-white/40", "text-white/30", "text-white/25"];

function ImpactBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-1.5 min-w-0">
      <div className="flex-1 h-1 bg-white/8 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-blue-500/60"
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-[10px] font-semibold text-white/60 shrink-0 w-6 text-right">{score}</span>
    </div>
  );
}

function SourceRow({ source, rank }: { source: InfluentialSource; rank: number }) {
  const initial = source.portal_name.charAt(0).toUpperCase();
  const sentStyle = SENTIMENT_STYLE[source.sentiment] ?? SENTIMENT_STYLE.neutral;

  return (
    <div className="flex items-center gap-2.5 py-1.5">
      <span className={`text-[11px] font-bold w-4 shrink-0 ${RANK_COLORS[rank] ?? "text-white/20"}`}>
        {rank + 1}
      </span>
      <div className="w-6 h-6 rounded-md bg-blue-500/20 flex items-center justify-center shrink-0">
        <span className="text-[10px] font-bold text-blue-300">{initial}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-medium text-white/80 truncate">{source.portal_name}</div>
        <ImpactBar score={source.impact_score} />
      </div>
      <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full shrink-0 ${sentStyle}`}>
        {source.sentiment.charAt(0).toUpperCase() + source.sentiment.slice(1)}
      </span>
    </div>
  );
}

export function TopInfluentialSources({ brandId, days = 30 }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["top-sources", brandId, days],
    queryFn: () => fetchTopSources(brandId, days),
    staleTime: 5 * 60_000,
  });

  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl p-3 min-h-0">
      <div className="flex items-center justify-between mb-2 flex-none">
        <span className="text-[10px] font-semibold text-white/40 uppercase tracking-wider">
          Top Influential Sources
        </span>
        <span className="text-[9px] text-white/25">by impact</span>
      </div>

      <div className="flex-1 min-h-0 overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 pt-1">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-7 bg-white/5 rounded-md animate-pulse" />
            ))}
          </div>
        ) : !data?.sources.length ? (
          <div className="flex items-center justify-center h-full text-[11px] text-white/25">
            No data for this period
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {data.sources.map((src, i) => (
              <SourceRow key={src.portal_name} source={src} rank={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
