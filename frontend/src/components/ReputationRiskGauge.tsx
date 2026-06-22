interface Props {
  score: number;
  negativePct: number;
  mentionsDelta?: number | null;
  topIssue?: string;
  compact?: boolean;
}

function getPoint(cx: number, cy: number, r: number, score: number) {
  const a = ((180 + (score / 100) * 180) * Math.PI) / 180;
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
}

function arc(cx: number, cy: number, r: number, s1: number, s2: number) {
  const p1 = getPoint(cx, cy, r, s1);
  const p2 = getPoint(cx, cy, r, s2);
  const span = ((s2 - s1) / 100) * 180;
  return `M ${p1.x.toFixed(2)} ${p1.y.toFixed(2)} A ${r} ${r} 0 ${span > 180 ? 1 : 0} 1 ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`;
}

export function ReputationRiskGauge({ score, negativePct, mentionsDelta, topIssue, compact }: Props) {
  const cx = 100, cy = 104, r = 78;
  const clampedScore = Math.max(0, Math.min(100, Math.round(score)));

  const riskLabel = clampedScore < 40 ? "Low Risk" : clampedScore < 70 ? "Medium Risk" : "High Risk";
  const riskColor = clampedScore < 40 ? "#22c55e" : clampedScore < 70 ? "#f59e0b" : "#ef4444";

  const needle = getPoint(cx, cy, r - 12, clampedScore);

  const drivers: { label: string; level: "High" | "Medium" | "Low" }[] = [];
  if (negativePct > 30)
    drivers.push({ label: "High volume of negative coverage", level: "High" });
  else if (negativePct > 15)
    drivers.push({ label: "Elevated negative coverage", level: "Medium" });
  if (clampedScore >= 70)
    drivers.push({ label: "Reputation score critically low", level: "High" });
  else if (clampedScore >= 40)
    drivers.push({ label: "Reputation score below healthy range", level: "Medium" });
  if (mentionsDelta !== null && mentionsDelta !== undefined && mentionsDelta < -15)
    drivers.push({ label: "Significant mention volume decline", level: "Medium" });
  if (topIssue && topIssue !== "other")
    drivers.push({
      label: `${topIssue.replace(/_/g, " ")} concerns rising`,
      level: negativePct > 25 ? "High" : "Medium",
    });
  while (drivers.length < 3)
    drivers.push({ label: "Continuous monitoring active", level: "Low" });

  const CHIP: Record<string, string> = {
    High: "bg-red-500/20 text-red-400",
    Medium: "bg-amber-500/20 text-amber-400",
    Low: "bg-green-500/20 text-green-400",
  };

  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl p-3 h-full flex flex-col text-white overflow-hidden">
      <div className="text-[11px] font-semibold text-white/70 mb-2 flex-none">Reputation Risk Monitor</div>

      <div className="flex gap-3 flex-1 min-h-0">
        {/* Gauge */}
        <div className="flex flex-col items-center shrink-0">
          <svg viewBox="0 0 200 112" className={compact ? "w-32 h-[56px]" : "w-40 h-[72px]"}>
            {/* Gray track */}
            <path d={arc(cx, cy, r, 0, 100)} fill="none" stroke="#1e3a5f" strokeWidth="16" strokeLinecap="butt" />
            {/* Green zone 0-39 */}
            <path d={arc(cx, cy, r, 0, 39)} fill="none" stroke="#22c55e" strokeWidth="16" strokeLinecap="butt" opacity="0.45" />
            {/* Amber zone 40-69 */}
            <path d={arc(cx, cy, r, 40, 69)} fill="none" stroke="#f59e0b" strokeWidth="16" strokeLinecap="butt" opacity="0.45" />
            {/* Red zone 70-100 */}
            <path d={arc(cx, cy, r, 70, 100)} fill="none" stroke="#ef4444" strokeWidth="16" strokeLinecap="butt" opacity="0.45" />
            {/* Filled arc to score */}
            {clampedScore > 0 && (
              <path d={arc(cx, cy, r, 0, clampedScore)} fill="none" stroke={riskColor} strokeWidth="16" strokeLinecap="butt" />
            )}
            {/* Needle */}
            <line
              x1={cx} y1={cy}
              x2={needle.x.toFixed(2)} y2={needle.y.toFixed(2)}
              stroke="white" strokeWidth="2.5" strokeLinecap="round"
            />
            <circle cx={cx} cy={cy} r="4.5" fill="white" />
            {/* Score text */}
            <text x={cx} y={cy - 6} textAnchor="middle" fill="white" fontSize="20" fontWeight="700">{clampedScore}</text>
            <text x={cx} y={cy - 1} textAnchor="middle" fill="rgba(255,255,255,0.45)" fontSize="7">/100</text>
          </svg>

          <div className="text-[11px] font-bold mt-1" style={{ color: riskColor }}>{riskLabel}</div>

          <div className="flex flex-col gap-0.5 mt-1.5">
            {[
              { c: "#22c55e", l: "Low (0–39)" },
              { c: "#f59e0b", l: "Medium (40–69)" },
              { c: "#ef4444", l: "High (70–100)" },
            ].map(z => (
              <div key={z.l} className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-sm shrink-0" style={{ background: z.c }} />
                <span className="text-[8px] text-white/40">{z.l}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Drivers */}
        <div className="flex-1 min-w-0 flex flex-col">
          <div className="text-[9px] font-semibold text-white/40 uppercase tracking-wider mb-2">Risk Drivers</div>
          <div className="space-y-2 flex-1">
            {drivers.slice(0, 4).map((d, i) => (
              <div key={i} className="flex items-center justify-between gap-2 py-1 border-b border-white/5 last:border-0">
                <span className="text-[10px] text-white/65 leading-tight">{d.label}</span>
                <span className={`text-[8px] font-semibold px-1.5 py-0.5 rounded-full shrink-0 ${CHIP[d.level]}`}>
                  {d.level}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
