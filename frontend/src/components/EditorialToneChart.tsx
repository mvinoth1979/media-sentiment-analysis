import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { fetchToneBreakdown } from "../lib/api";
import type { ToneBreakdownData } from "../lib/types";

interface Props {
  brandId: string;
  compact?: boolean;
}

const TONE_CONFIG = [
  { key: "factual",        label: "Factual",         color: "#818cf8" }, // indigo-400
  { key: "positive_frame", label: "Positive Frame",  color: "#4ade80" }, // green-400
  { key: "negative_frame", label: "Negative Frame",  color: "#f59e0b" }, // amber-500
  { key: "critical",       label: "Critical",        color: "#f87171" }, // red-400
] as const;

type ToneKey = typeof TONE_CONFIG[number]["key"];

interface TooltipEntry { payload: { label: string; value: number; color: string } }
function ToneTooltip({ active, payload }: { active?: boolean; payload?: TooltipEntry[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-lg px-3 py-2 text-xs shadow-md">
      <div className="font-semibold text-white/80">{d.label}</div>
      <div className="font-bold" style={{ color: d.color }}>{d.value} articles</div>
    </div>
  );
}

export function EditorialToneChart({ brandId, compact }: Props) {
  const [data, setData] = useState<ToneBreakdownData | null>(null);

  useEffect(() => {
    fetchToneBreakdown(brandId, 30).then(setData).catch(() => {});
  }, [brandId]);

  const total = data?.total ?? { factual: 0, positive_frame: 0, negative_frame: 0, critical: 0 };
  const grandTotal = TONE_CONFIG.reduce((s, c) => s + (total[c.key] || 0), 0);

  const pieData = TONE_CONFIG
    .map(c => ({ key: c.key, label: c.label, color: c.color, value: total[c.key as ToneKey] || 0 }))
    .filter(d => d.value > 0);

  const dominant = pieData.length > 0
    ? pieData.reduce((a, b) => (a.value >= b.value ? a : b))
    : null;

  if (grandTotal === 0) {
    return (
      <div className="bg-[#1a2744] border border-white/10 rounded-xl p-4">
        <div className="text-sm font-semibold text-white mb-2">Editorial Tone</div>
        <p className="text-xs text-white/40">Tone data will populate after the next pipeline run.</p>
      </div>
    );
  }

  if (compact) {
    const top2 = [...TONE_CONFIG].sort((a, b) => (total[b.key] || 0) - (total[a.key] || 0)).slice(0, 2);
    return (
      <div className="bg-[#1a2744] border border-white/10 rounded-lg p-2 h-full flex flex-col overflow-hidden">
        <span className="text-[11px] font-semibold text-white mb-1 flex-none">Editorial Tone</span>
        <div className="flex items-center gap-2 flex-1 min-h-0">
          <div className="relative w-[70px] h-[70px] shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" cx="50%" cy="50%" innerRadius={18} outerRadius={32} paddingAngle={2}>
                  {pieData.map(d => <Cell key={d.key} fill={d.color} strokeWidth={0} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            {dominant && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span className="text-[7px] text-white/40 text-center leading-tight px-1">{dominant.label}</span>
              </div>
            )}
          </div>
          <div className="flex-1 space-y-1 min-w-0">
            {top2.map(c => {
              const count = total[c.key] || 0;
              const pct = grandTotal > 0 ? Math.round((count / grandTotal) * 100) : 0;
              return (
                <div key={c.key} className="flex items-center gap-1 text-[9px]">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                  <span className="truncate flex-1 text-white/60">{c.label}</span>
                  <span className="font-bold text-white/80 shrink-0">{pct}%</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl p-4">
      <div className="text-sm font-semibold text-white mb-3">Editorial Tone</div>
      <div className="flex items-center gap-4">
        <div className="relative w-[110px] h-[110px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData} dataKey="value"
                cx="50%" cy="50%"
                innerRadius={32} outerRadius={52}
                paddingAngle={2} startAngle={90} endAngle={-270}
              >
                {pieData.map(d => <Cell key={d.key} fill={d.color} strokeWidth={0} />)}
              </Pie>
              <Tooltip content={<ToneTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          {dominant && (
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[9px] text-white/40 text-center leading-tight px-2">{dominant.label}</span>
            </div>
          )}
        </div>

        <div className="flex-1 space-y-2">
          {TONE_CONFIG.map(c => {
            const count = total[c.key] || 0;
            const pct = grandTotal > 0 ? Math.round((count / grandTotal) * 100) : 0;
            return (
              <div key={c.key}>
                <div className="flex items-center justify-between text-xs mb-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                    <span className="text-white/60">{c.label}</span>
                  </div>
                  <span className="font-semibold text-white/80">{count} <span className="text-white/40 font-normal">({pct}%)</span></span>
                </div>
                <div className="h-1.5 bg-white/8 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: c.color }} />
                </div>
              </div>
            );
          })}
          <div className="text-[10px] text-white/40 pt-1">Based on {grandTotal} articles · last 30 days</div>
        </div>
      </div>
    </div>
  );
}
