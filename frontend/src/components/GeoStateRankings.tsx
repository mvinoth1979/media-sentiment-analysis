import type { StateStat } from "../lib/types";

interface Props {
  stateBreakdown: StateStat[];
  onStateDrill: (state: string) => void;
}

const STATE_ABBR: Record<string, string> = {
  "Tamil Nadu": "TN", "Maharashtra": "MH", "Delhi": "DL", "Karnataka": "KA",
  "Kerala": "KL", "Telangana": "TG", "Andhra Pradesh": "AP", "Gujarat": "GJ",
  "Rajasthan": "RJ", "Uttar Pradesh": "UP", "West Bengal": "WB", "Punjab": "PB",
  "Haryana": "HR", "Madhya Pradesh": "MP", "Bihar": "BR", "Odisha": "OD",
};

function SentimentBar({ positive, negative, count }: { positive: number; negative: number; count: number }) {
  const pos = count ? Math.round((positive / count) * 100) : 0;
  const neg = count ? Math.round((negative / count) * 100) : 0;
  const neu = 100 - pos - neg;
  return (
    <div className="flex h-1 w-full rounded-full overflow-hidden gap-px">
      <div className="bg-emerald-500/70" style={{ width: `${pos}%` }} />
      <div className="bg-white/15" style={{ width: `${neu}%` }} />
      <div className="bg-red-500/70" style={{ width: `${neg}%` }} />
    </div>
  );
}

export function GeoStateRankings({ stateBreakdown, onStateDrill }: Props) {
  if (!stateBreakdown?.length) {
    return (
      <div className="bg-[#111e36] border border-white/10 rounded-xl p-4 flex items-center justify-center h-full">
        <p className="text-[11px] text-white/30 italic">No geo data available for this period.</p>
      </div>
    );
  }

  const sorted = [...stateBreakdown].sort((a, b) => b.count - a.count).slice(0, 12);
  const topPositive = [...stateBreakdown]
    .filter(s => s.count >= 3)
    .sort((a, b) => (b.positive / b.count) - (a.positive / a.count))
    .slice(0, 4);
  const topNegative = [...stateBreakdown]
    .filter(s => s.count >= 3)
    .sort((a, b) => (b.negative / b.count) - (a.negative / a.count))
    .slice(0, 4);

  return (
    <div className="bg-[#111e36] border border-white/10 rounded-xl flex flex-col overflow-hidden h-full">
      <div className="px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[11px] font-semibold text-white">State Intelligence</span>
        <span className="text-[9px] text-white/30 ml-2">· {stateBreakdown.length} states tracked</span>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-3" style={{ scrollbarWidth: "none" }}>

        {/* All states by volume */}
        <div>
          <div className="text-[8px] uppercase tracking-widest text-white/25 mb-1.5 px-1">By Coverage Volume</div>
          <div className="space-y-0.5">
            {sorted.map((s) => {
              const posPct = s.count ? Math.round((s.positive / s.count) * 100) : 0;
              const negPct = s.count ? Math.round((s.negative / s.count) * 100) : 0;
              const label = posPct >= 60 ? "text-emerald-400" : negPct >= 40 ? "text-red-400" : "text-white/50";
              const abbr = STATE_ABBR[s.state] ?? s.state.slice(0, 2).toUpperCase();
              return (
                <button
                  key={s.state}
                  onClick={() => onStateDrill(s.state)}
                  className="w-full flex items-center gap-2 px-2 py-1 rounded hover:bg-white/5 transition-colors text-left"
                >
                  <span className="text-[9px] text-white/25 w-5 shrink-0 tabular-nums">{abbr}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-[10px] text-white/70 truncate">{s.state}</span>
                      <span className={`text-[9px] font-semibold ml-1 shrink-0 ${label}`}>
                        {posPct > negPct ? `${posPct}% pos` : `${negPct}% neg`}
                      </span>
                    </div>
                    <SentimentBar positive={s.positive} negative={s.negative} count={s.count} />
                  </div>
                  <span className="text-[9px] text-white/25 shrink-0 w-7 text-right">{s.count}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Quick league tables */}
        <div className="grid grid-cols-2 gap-2 mt-2">
          <div className="bg-[#0d1626] rounded-lg p-2">
            <div className="text-[8px] text-emerald-400/70 uppercase tracking-widest mb-1.5">Most Positive</div>
            {topPositive.map((s) => (
              <button
                key={s.state}
                onClick={() => onStateDrill(s.state)}
                className="flex w-full justify-between text-[9px] py-0.5 hover:text-white transition-colors"
              >
                <span className="text-white/50 truncate">{s.state.replace(" Pradesh", " Pr.")}</span>
                <span className="text-emerald-400 font-semibold ml-1 shrink-0">
                  {Math.round((s.positive / s.count) * 100)}%
                </span>
              </button>
            ))}
          </div>
          <div className="bg-[#0d1626] rounded-lg p-2">
            <div className="text-[8px] text-red-400/70 uppercase tracking-widest mb-1.5">Highest Risk</div>
            {topNegative.map((s) => (
              <button
                key={s.state}
                onClick={() => onStateDrill(s.state)}
                className="flex w-full justify-between text-[9px] py-0.5 hover:text-white transition-colors"
              >
                <span className="text-white/50 truncate">{s.state.replace(" Pradesh", " Pr.")}</span>
                <span className="text-red-400 font-semibold ml-1 shrink-0">
                  {Math.round((s.negative / s.count) * 100)}%
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
