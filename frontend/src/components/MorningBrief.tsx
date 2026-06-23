import { useQuery } from "@tanstack/react-query";
import { fetchMorningBrief } from "../lib/api";
import { AIConfidenceMeter } from "./AIConfidenceMeter";

interface Props {
  brandId: string;
  days: number;
}

function Skeleton() {
  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl px-4 py-3 animate-pulse">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <div className="h-3.5 w-3/4 bg-white/10 rounded" />
          <div className="h-2.5 w-full bg-white/6 rounded" />
          <div className="h-2.5 w-5/6 bg-white/6 rounded" />
          <div className="h-2.5 w-4/6 bg-white/6 rounded" />
        </div>
        <div className="w-20 h-12 bg-white/6 rounded" />
      </div>
    </div>
  );
}

function ScoreBadge({ change, direction }: { change: number; direction: string }) {
  const abs = Math.abs(change);
  if (direction === "stable") {
    return (
      <span className="text-[11px] text-white/40 border border-white/10 rounded-full px-2 py-0.5">
        → Stable
      </span>
    );
  }
  const isUp = direction === "up";
  return (
    <span
      className={`text-[11px] font-semibold rounded-full px-2 py-0.5 ${
        isUp ? "text-emerald-400 bg-emerald-500/10" : "text-red-400 bg-red-500/10"
      }`}
    >
      {isUp ? "▲" : "▼"} {abs.toFixed(1)} pts
    </span>
  );
}

export function MorningBrief({ brandId, days }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["morning-brief", brandId, days],
    queryFn: () => fetchMorningBrief(brandId, days),
    staleTime: 60 * 60_000,
    retry: 1,
  });

  if (isLoading) return <Skeleton />;
  if (isError || !data) return null;

  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl px-4 py-3 flex items-start gap-4 flex-none">
      {/* Left: greeting + highlights */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <h3 className="text-sm font-semibold text-white leading-tight">{data.greeting}</h3>
          {/* Speaker + Expand stubs */}
          <button className="text-white/20 hover:text-white/50 transition-colors text-[11px]" title="Read aloud (coming soon)">🔊</button>
          <button className="text-white/20 hover:text-white/50 transition-colors text-[11px]" title="Full report (coming soon)">⛶</button>
        </div>
        <ul className="space-y-0.5">
          {data.highlights.map((h, i) => (
            <li key={i} className="flex items-start gap-1.5 text-[11px] text-white/60">
              <span className="text-white/25 mt-px shrink-0">•</span>
              <span>{h}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Right: score badge + confidence meter */}
      <div className="flex flex-col items-center gap-1.5 shrink-0">
        <ScoreBadge change={data.score_change} direction={data.score_direction} />
        <AIConfidenceMeter pct={data.confidence_pct} />
      </div>
    </div>
  );
}
