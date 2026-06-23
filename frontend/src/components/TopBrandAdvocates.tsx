import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAdvocatesScored, type ScoredAdvocate } from "../lib/api";

interface Props {
  brandId: string;
  days?: number;
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(Math.round(n));
}

const SOURCE_STYLE: Record<string, { bg: string; text: string }> = {
  YouTube: { bg: "bg-red-500/15",     text: "text-red-400" },
  Blog:    { bg: "bg-emerald-500/15", text: "text-emerald-400" },
  Reddit:  { bg: "bg-orange-500/15",  text: "text-orange-400" },
  Media:   { bg: "bg-blue-500/15",    text: "text-blue-400" },
};

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[8px] text-white/30 w-12 shrink-0">{label}</span>
      <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-[8px] text-white/40 w-6 text-right">{value}</span>
    </div>
  );
}

type AdvocateAction = "engaged" | "monitoring" | null;

function AdvocateRow({ advocate }: { advocate: ScoredAdvocate }) {
  const [action, setAction] = useState<AdvocateAction>(null);
  const initial = advocate.name.charAt(0).toUpperCase();
  const style = SOURCE_STYLE[advocate.source_type] ?? SOURCE_STYLE.Media;

  return (
    <div className="py-2 space-y-1.5">
      {/* Row 1: avatar + name + badges */}
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
          <span className="text-[10px] font-bold text-emerald-300">{initial}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 flex-wrap">
            <span className="text-[11px] font-medium text-white/80 truncate max-w-[120px]">{advocate.name}</span>
            {advocate.emerging && (
              <span className="text-[7px] font-bold text-amber-300 bg-amber-500/15 border border-amber-500/25 px-1 py-0.5 rounded-full leading-none">NEW</span>
            )}
          </div>
          <div className="text-[8px] text-white/30">{fmt(advocate.total_reach)} reach · {advocate.article_count} posts</div>
        </div>
        <div className="flex flex-col items-end gap-0.5 shrink-0">
          <span className={`text-[7px] font-semibold px-1.5 py-0.5 rounded-full ${style.bg} ${style.text}`}>
            {advocate.source_type}
          </span>
          <span className="text-[9px] font-bold text-white/60">{advocate.total_score}</span>
        </div>
      </div>

      {/* Row 2: 3 score bars */}
      <div className="space-y-0.5 pl-8">
        <ScoreBar label="Affinity"  value={advocate.affinity}  color="bg-emerald-500" />
        <ScoreBar label="Influence" value={advocate.influence} color="bg-blue-500" />
        <ScoreBar label="Trust"     value={advocate.trust}     color="bg-purple-500" />
      </div>

      {/* Row 3: suggested engagement + actions */}
      <div className="pl-8 flex items-center gap-2 flex-wrap">
        <span className="text-[8px] text-white/25 flex-1 min-w-0 truncate">💡 {advocate.suggested_engagement}</span>
        {action ? (
          <span className={`text-[7px] font-semibold px-1.5 py-0.5 rounded-full ${action === "engaged" ? "bg-blue-500/15 text-blue-400" : "bg-white/10 text-white/35"}`}>
            {action === "engaged" ? "✓ Engaged" : "👁 Monitoring"}
          </span>
        ) : (
          <div className="flex gap-1 shrink-0">
            <button
              onClick={() => setAction("engaged")}
              className="text-[7px] border border-blue-500/25 text-blue-400/60 hover:text-blue-400 hover:border-blue-400/50 rounded px-1.5 py-0.5 transition-colors"
            >
              Engage
            </button>
            <button
              onClick={() => setAction("monitoring")}
              className="text-[7px] border border-white/10 text-white/30 hover:text-white/50 rounded px-1.5 py-0.5 transition-colors"
            >
              Monitor
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export function TopBrandAdvocates({ brandId, days = 30 }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["advocates-scored", brandId, days],
    queryFn: () => fetchAdvocatesScored(brandId, days),
    staleTime: 10 * 60_000,
    retry: 1,
  });

  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl p-3 min-h-0">
      <div className="flex items-center justify-between mb-1.5 flex-none">
        <span className="text-[10px] font-semibold text-white/40 uppercase tracking-wider">Advocacy Hub</span>
        <span className="text-[9px] text-white/25">Affinity · Influence · Trust</span>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto divide-y divide-white/5" style={{ scrollbarWidth: "none" }}>
        {isLoading ? (
          <div className="space-y-2 pt-1">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-white/5 rounded-md animate-pulse" />
            ))}
          </div>
        ) : !data?.advocates.length ? (
          <div className="flex items-center justify-center h-full text-[11px] text-white/25">
            No advocates found
          </div>
        ) : (
          data.advocates.slice(0, 5).map(a => (
            <AdvocateRow key={a.name} advocate={a} />
          ))
        )}
      </div>
    </div>
  );
}
