import type { RiskDayPoint } from "../lib/api";

interface Props {
  historical: RiskDayPoint[];
}

function riskColor(score: number): string {
  if (score >= 65) return "#ef4444";
  if (score >= 45) return "#f97316";
  if (score >= 25) return "#eab308";
  return "#22c55e";
}

function riskLabel(score: number): string {
  if (score >= 65) return "Crisis";
  if (score >= 45) return "High";
  if (score >= 25) return "Elevated";
  return "Low";
}

function shortDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00Z");
  return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

export function CrisisTimeline({ historical }: Props) {
  if (historical.length === 0) return null;

  const maxScore = Math.max(...historical.map(p => p.risk_score), 1);
  const maxCount = Math.max(...historical.map(p => p.article_count), 1);

  // Show last 14 points max
  const points = historical.slice(-14);

  return (
    <div className="space-y-1">
      <div className="text-[9px] text-white/30 font-medium uppercase tracking-wider px-0.5">Crisis Timeline</div>
      <div className="overflow-x-auto" style={{ scrollbarWidth: "none" }}>
        <div className="flex items-end gap-1 pb-1" style={{ minWidth: `${points.length * 36}px` }}>
          {points.map((p, i) => {
            const heightPct = (p.risk_score / maxScore) * 100;
            const barH = Math.max(4, (heightPct / 100) * 48);
            const color = riskColor(p.risk_score);
            const isPeak = p.risk_score === maxScore && p.risk_score > 20;

            return (
              <div key={i} className="flex flex-col items-center gap-0.5 flex-none" style={{ width: 32 }}>
                {/* Spike arrow for peaks */}
                {isPeak && (
                  <span className="text-[8px] text-red-400 animate-pulse">▲</span>
                )}

                {/* Article count dots */}
                <div className="flex gap-0.5 items-end" style={{ height: 8 }}>
                  {[...Array(Math.min(4, Math.ceil((p.article_count / maxCount) * 4)))].map((_, j) => (
                    <div key={j} className="w-0.5 bg-white/20 rounded-full" style={{ height: `${(j + 1) * 2}px` }} />
                  ))}
                </div>

                {/* Risk bar */}
                <div
                  className="w-full rounded-t-sm transition-all"
                  style={{
                    height: `${barH}px`,
                    backgroundColor: color,
                    opacity: 0.8,
                  }}
                  title={`${shortDate(p.date)}: Risk ${p.risk_score.toFixed(0)} (${p.negative_count}/${p.article_count} negative)`}
                />

                {/* Date label */}
                <div className="text-[7px] text-white/25 text-center leading-tight">
                  {shortDate(p.date).split(" ")[0]}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="flex gap-2 text-[8px] text-white/30">
        {[65, 45, 25, 0].map(threshold => (
          <span key={threshold} className="flex items-center gap-0.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: riskColor(threshold + 1) }} />
            {riskLabel(threshold + 1)}
          </span>
        ))}
      </div>
    </div>
  );
}
