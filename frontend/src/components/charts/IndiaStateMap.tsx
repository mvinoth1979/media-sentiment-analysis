import { useState } from "react";
import type { StateStat } from "../../lib/types";

interface Props {
  data: StateStat[];
  onStateClick?: (state: string) => void;
  onExplain?: (zone: string) => void;
  variant?: "states" | "regions";
}

interface Tooltip {
  name: string;
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  x: number;
  y: number;
}

// ── State → zone mapping ──────────────────────────────────────────────────────
const STATE_ZONE: Record<string, "North" | "South" | "East" | "West"> = {
  "Delhi": "North", "Haryana": "North", "Punjab": "North", "Rajasthan": "North",
  "Uttar Pradesh": "North", "Himachal Pradesh": "North", "Uttarakhand": "North",
  "Jammu & Kashmir": "North", "J&K": "North", "Chandigarh": "North",
  "Ladakh": "North",
  "Tamil Nadu": "South", "Kerala": "South", "Karnataka": "South",
  "Andhra Pradesh": "South", "Telangana": "South", "Puducherry": "South",
  "Goa": "South",
  "West Bengal": "East", "Bihar": "East", "Odisha": "East", "Jharkhand": "East",
  "Assam": "East", "Meghalaya": "East", "Nagaland": "East", "Manipur": "East",
  "Mizoram": "East", "Tripura": "East", "Arunachal Pradesh": "East",
  "Sikkim": "East",
  "Maharashtra": "West", "Gujarat": "West", "Madhya Pradesh": "West",
  "Chhattisgarh": "West",
};

const ZONES = ["North", "South", "East", "West"] as const;
type Zone = typeof ZONES[number];

const ZONE_COLOR: Record<Zone, { active: string; ring: string; hex: string }> = {
  North:  { active: "bg-blue-500/20 border-blue-500/30 text-blue-300",   ring: "text-blue-400",   hex: "#60a5fa" },
  South:  { active: "bg-emerald-500/20 border-emerald-500/30 text-emerald-300", ring: "text-emerald-400", hex: "#34d399" },
  East:   { active: "bg-amber-500/20 border-amber-500/30 text-amber-300",  ring: "text-amber-400",  hex: "#fbbf24" },
  West:   { active: "bg-purple-500/20 border-purple-500/30 text-purple-300", ring: "text-purple-400", hex: "#a78bfa" },
};

function sentimentColor(stat: StateStat): { bg: string; text: string; border: string } {
  const posPct = stat.positive / (stat.count || 1);
  const negPct = stat.negative / (stat.count || 1);
  if (posPct >= 0.6) return { bg: "bg-emerald-900/60", text: "text-emerald-300", border: "border-emerald-700/50" };
  if (posPct >= 0.4) return { bg: "bg-emerald-900/40", text: "text-emerald-400", border: "border-emerald-800/50" };
  if (negPct >= 0.6) return { bg: "bg-red-900/60",     text: "text-red-300",     border: "border-red-700/50"     };
  if (negPct >= 0.4) return { bg: "bg-red-900/40",     text: "text-red-400",     border: "border-red-800/50"     };
  return                    { bg: "bg-white/5",         text: "text-white/60",    border: "border-white/10"       };
}

// Tiny inline donut — same strokeDasharray approach as KPICard
function ZoneDonut({ pos, total, hex, size = 36 }: { pos: number; total: number; hex: string; size?: number }) {
  const r    = size / 2 - 3.5;
  const cx   = size / 2;
  const circ = 2 * Math.PI * r;
  const posFrac = total > 0 ? pos / total : 0;
  const filled  = posFrac * circ;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
      <circle cx={cx} cy={cx} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={3} />
      <circle cx={cx} cy={cx} r={r} fill="none" stroke={hex} strokeWidth={3}
        strokeLinecap="round" strokeDasharray={`${filled} ${circ}`}
        transform={`rotate(-90 ${cx} ${cx})`} />
      <text x={cx} y={cx + 1} textAnchor="middle" dominantBaseline="middle"
        fill="rgba(255,255,255,0.65)" fontSize={8} fontWeight="700">
        {total > 0 ? `${Math.round(posFrac * 100)}%` : "—"}
      </text>
    </svg>
  );
}

export function IndiaStateMap({ data, onStateClick, onExplain, variant = "states" }: Props) {
  const [tooltip, setTooltip] = useState<Tooltip | null>(null);

  const sorted = [...data].sort((a, b) => b.count - a.count);

  // ── Regions variant ─────────────────────────────────────────────────────────
  if (variant === "regions") {
    const zoneStats: Record<Zone, { count: number; positive: number; negative: number; neutral: number; states: string[] }> = {
      North: { count: 0, positive: 0, negative: 0, neutral: 0, states: [] },
      South: { count: 0, positive: 0, negative: 0, neutral: 0, states: [] },
      East:  { count: 0, positive: 0, negative: 0, neutral: 0, states: [] },
      West:  { count: 0, positive: 0, negative: 0, neutral: 0, states: [] },
    };

    for (const s of data) {
      const zone = STATE_ZONE[s.state];
      if (zone) {
        zoneStats[zone].count    += s.count;
        zoneStats[zone].positive += s.positive;
        zoneStats[zone].negative += s.negative;
        zoneStats[zone].neutral  += s.neutral;
        zoneStats[zone].states.push(s.state);
      }
    }

    const total = ZONES.reduce((sum, z) => sum + zoneStats[z].count, 0);

    return (
      <div className="bg-[#1a2744] border border-white/10 rounded-xl p-3 h-full flex flex-col overflow-hidden">
        <div className="flex items-center justify-between mb-2 flex-none">
          <span className="text-[11px] font-semibold text-white">Geographic Sentiment</span>
          {total > 0 && <span className="text-[9px] text-white/30">{data.length} states</span>}
        </div>

        {total === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <span className="text-[10px] text-white/30">No state data yet</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2 flex-1 min-h-0">
            {ZONES.map(zone => {
              const z   = zoneStats[zone];
              const col = ZONE_COLOR[zone];
              const pct = total > 0 ? Math.round((z.count / total) * 100) : 0;
              return (
                <div
                  key={zone}
                  className={`flex flex-col items-start p-2.5 rounded-lg border transition-all ${col.active}`}
                >
                  <button
                    className="w-full text-left"
                    onClick={() => z.states.forEach(s => onStateClick?.(s))}
                  >
                    <div className="flex items-center justify-between w-full mb-1">
                      <span className="text-[11px] font-bold">{zone}</span>
                      <ZoneDonut pos={z.positive} total={z.count} hex={col.hex} size={34} />
                    </div>
                    <div className="text-[13px] font-bold leading-none">{z.count.toLocaleString()}</div>
                    <div className="text-[9px] opacity-60 mt-0.5">{pct}% of total · {z.states.length} state{z.states.length !== 1 ? "s" : ""}</div>
                    <div className="flex items-center gap-1.5 mt-1.5 text-[8px] opacity-70">
                      <span className="text-emerald-400">+{z.positive}</span>
                      <span className="text-white/30">·</span>
                      <span className="text-red-400">−{z.negative}</span>
                      <span className="text-white/30">·</span>
                      <span className="text-white/40">~{z.neutral}</span>
                    </div>
                  </button>
                  {onExplain && (
                    <button
                      onClick={e => { e.stopPropagation(); onExplain(zone); }}
                      className="mt-1.5 text-[9px] text-blue-400/60 hover:text-blue-300 transition-colors"
                    >
                      🧠 Explain
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // ── States variant (default) ────────────────────────────────────────────────
  return (
    <div className="relative bg-[#1a2744] border border-white/10 rounded-xl p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] font-semibold text-white">State-level Sentiment</span>
        {data.length > 0 && (
          <span className="text-[9px] text-white/30">{data.length} state{data.length !== 1 ? "s" : ""}</span>
        )}
      </div>
      <p className="text-[9px] text-white/30 mb-2">Click a state to filter mentions</p>

      {data.length === 0 ? (
        <div className="py-6 text-center">
          <p className="text-[10px] text-white/30">State data will appear after the next pipeline run</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
          {sorted.map(stat => {
            const colors = sentimentColor(stat);
            return (
              <button
                key={stat.state}
                onClick={() => onStateClick?.(stat.state)}
                onMouseEnter={e => setTooltip({ name: stat.state, total: stat.count, positive: stat.positive, negative: stat.negative, neutral: stat.neutral, x: e.clientX, y: e.clientY })}
                onMouseMove={e => setTooltip(prev => prev ? { ...prev, x: e.clientX, y: e.clientY } : prev)}
                onMouseLeave={() => setTooltip(null)}
                className={`text-left px-2.5 py-2 rounded-lg border ${colors.bg} ${colors.border} hover:ring-1 hover:ring-blue-500/40 transition-all`}
              >
                <div className={`text-[10px] font-medium ${colors.text} truncate`}>{stat.state}</div>
                <div className="text-[9px] text-white/30 mt-0.5">{stat.count}</div>
              </button>
            );
          })}
        </div>
      )}

      {/* Legend */}
      {data.length > 0 && (
        <div className="flex flex-wrap gap-3 mt-3 pt-3 border-t border-white/8">
          {[
            { bg: "bg-emerald-900/60", label: "Strong positive" },
            { bg: "bg-emerald-900/40", label: "Positive" },
            { bg: "bg-white/5",        label: "Neutral" },
            { bg: "bg-red-900/40",     label: "Negative" },
            { bg: "bg-red-900/60",     label: "Strong negative" },
          ].map(({ bg, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div className={`w-2.5 h-2.5 rounded-sm border border-white/10 ${bg}`} />
              <span className="text-[9px] text-white/35">{label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none bg-[#1a2744] border border-white/15 rounded-lg px-3 py-2 text-xs shadow-xl"
          style={{ left: tooltip.x + 12, top: tooltip.y - 10 }}
        >
          <div className="font-semibold text-white mb-1">{tooltip.name}</div>
          <div className="space-y-0.5">
            <div className="text-white/50">{tooltip.total} mention{tooltip.total !== 1 ? "s" : ""}</div>
            <div className="text-emerald-400">+{tooltip.positive} positive</div>
            <div className="text-red-400">−{tooltip.negative} negative</div>
            <div className="text-white/30">~{tooltip.neutral} neutral</div>
          </div>
        </div>
      )}
    </div>
  );
}
