import { useQuery } from "@tanstack/react-query";
import { fetchRegionalSummary, type StateHighlight } from "../lib/api";

interface Props {
  brandId: string;
  days: number;
  onStateExplain?: (state: string) => void;
}

const DIRECTION_ICON: Record<StateHighlight["direction"], string> = {
  improving: "🟢",
  declining:  "🔴",
  stable:     "⚪",
};

function Skeleton() {
  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl px-3 py-2.5 animate-pulse space-y-2">
      <div className="h-2 w-3/4 bg-white/10 rounded" />
      <div className="h-2 w-full bg-white/6 rounded" />
      <div className="flex gap-1.5">
        {[...Array(3)].map((_, i) => <div key={i} className="h-5 w-20 bg-white/6 rounded-full" />)}
      </div>
    </div>
  );
}

export function AIRegionalSummary({ brandId, days, onStateExplain }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["regional-summary", brandId, days],
    queryFn: () => fetchRegionalSummary(brandId, days),
    staleTime: 60 * 60_000,
    retry: 1,
  });

  if (isLoading) return <Skeleton />;
  if (!data || !data.summary) return null;

  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl px-3 py-2.5 space-y-2">
      <div className="flex items-center gap-1.5">
        <span className="text-[10px]">🗺️</span>
        <span className="text-[10px] font-semibold text-white/50 uppercase tracking-wider">AI Regional Summary</span>
      </div>

      <p className="text-[11px] text-white/75 leading-relaxed">{data.summary}</p>

      {data.state_highlights.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {data.state_highlights.map(h => (
            <div
              key={h.state}
              className="flex items-center gap-1 bg-white/5 border border-white/8 rounded-full pl-1.5 pr-1 py-0.5"
            >
              <span className="text-[10px]">{DIRECTION_ICON[h.direction]}</span>
              <span className="text-[10px] text-white/70">{h.state}</span>
              {onStateExplain && (
                <button
                  onClick={() => onStateExplain(h.state)}
                  className="text-[9px] text-blue-400/70 hover:text-blue-300 ml-0.5 transition-colors"
                  title={`Explain ${h.state} sentiment`}
                >
                  🧠
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
