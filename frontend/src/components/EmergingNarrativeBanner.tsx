import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchEmergingTopics } from "../lib/api";

interface Props {
  brandId: string;
  days?: number;
}

export function EmergingNarrativeBanner({ brandId, days = 7 }: Props) {
  const [expanded, setExpanded] = useState(false);

  const { data } = useQuery({
    queryKey: ["emerging-topics", brandId, days],
    queryFn: () => fetchEmergingTopics(brandId, days),
    staleTime: 15 * 60_000,
    retry: 1,
  });

  const emerging = data?.emerging ?? [];
  if (emerging.length === 0) return null;

  const topTopic = emerging[0];
  const extra = emerging.length - 1;

  return (
    <div className="bg-amber-500/10 border border-amber-500/25 rounded-lg px-3 py-2 relative">
      <div className="flex items-start gap-2">
        <span className="text-amber-400 text-[13px] mt-0.5 flex-none">🧠</span>
        <div className="flex-1 min-w-0">
          <span className="text-[11px] font-semibold text-amber-300">AI discovered new narrative: </span>
          <span className="text-[11px] text-amber-200 font-medium">{topTopic.topic}</span>
          <div className="text-[9px] text-amber-400/60 mt-0.5">
            {topTopic.novelty_score.toFixed(1)}× above baseline · {topTopic.current_count} mentions in {days}d
          </div>
        </div>
        {extra > 0 && (
          <button
            onClick={() => setExpanded(v => !v)}
            className="text-[9px] text-amber-400/70 hover:text-amber-300 border border-amber-500/20 rounded px-1.5 py-0.5 flex-none transition-colors"
          >
            {expanded ? "▲ hide" : `+${extra} more`}
          </button>
        )}
      </div>
      {/* Absolute dropdown — does not affect parent layout height */}
      {expanded && extra > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 z-40 bg-[#1a2a0e] border border-amber-500/30 rounded-lg p-2 space-y-1.5 shadow-xl">
          {emerging.slice(1).map(e => (
            <div key={e.topic} className="flex items-center gap-2">
              <span className="text-[9px] text-amber-400/50 font-medium">{e.novelty_score.toFixed(1)}×</span>
              <span className="text-[10px] text-amber-200/70 font-medium">{e.topic}</span>
              <span className="text-[8px] text-amber-500/40">{e.current_count} mentions</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
