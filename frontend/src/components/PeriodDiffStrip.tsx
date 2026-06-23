import { useQuery } from "@tanstack/react-query";
import { fetchPeriodDiff } from "../lib/api";

interface Props {
  brandId: string;
  days?: number;
}

interface DeltaChipProps {
  label: string;
  value: number;
  unit?: string;
  invertColors?: boolean;   // true = positive delta is bad (e.g. risk)
  format?: (v: number) => string;
}

function DeltaChip({ label, value, unit = "", invertColors = false, format }: DeltaChipProps) {
  const positive = invertColors ? value < 0 : value > 0;
  const negative = invertColors ? value > 0 : value < 0;
  const colorClass = positive ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
    : negative ? "text-red-400 bg-red-500/10 border-red-500/20"
    : "text-white/40 bg-white/5 border-white/10";
  const arrow = value > 0 ? "↑" : value < 0 ? "↓" : "→";
  const displayVal = format ? format(Math.abs(value)) : `${Math.abs(value)}${unit}`;

  return (
    <div className={`flex items-center gap-1.5 border rounded-lg px-2.5 py-1 ${colorClass}`}>
      <span className="text-[9px] text-white/30 uppercase tracking-wide">{label}</span>
      <span className="text-[11px] font-semibold">{arrow} {displayVal}</span>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex gap-2">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-7 w-24 bg-white/5 rounded-lg animate-pulse" />
      ))}
    </div>
  );
}

export function PeriodDiffStrip({ brandId, days = 7 }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["period-diff", brandId, days],
    queryFn: () => fetchPeriodDiff(brandId, days),
    staleTime: 20 * 60_000,
    retry: 1,
  });

  if (isLoading) return <Skeleton />;
  if (!data) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-[9px] text-white/25 uppercase tracking-widest shrink-0">{data.period_label}</span>
      <DeltaChip
        label="Mentions"
        value={data.mention_delta}
        format={v => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : `${v}`}
      />
      <DeltaChip
        label="Sentiment"
        value={data.sentiment_delta}
        unit="%"
        format={v => `${v.toFixed(1)}%`}
      />
      <DeltaChip
        label="Risk"
        value={data.risk_delta}
        invertColors
        format={v => `${v.toFixed(1)} pts`}
      />
      {data.top_gained.length > 0 && (
        <div className="flex items-center gap-1 text-[9px] text-white/30">
          <span className="text-emerald-400">↑</span>
          <span className="truncate max-w-[120px]">{data.top_gained.slice(0, 2).join(", ")}</span>
        </div>
      )}
      {data.top_lost.length > 0 && (
        <div className="flex items-center gap-1 text-[9px] text-white/30">
          <span className="text-red-400">↓</span>
          <span className="truncate max-w-[120px]">{data.top_lost.slice(0, 2).join(", ")}</span>
        </div>
      )}
    </div>
  );
}
