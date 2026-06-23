interface Props {
  pct: number;
  label?: string;
}

export function AIConfidenceMeter({ pct, label = "AI Confidence" }: Props) {
  const clamped = Math.max(0, Math.min(100, pct));
  // 180-degree arc: full arc circumference = π * r = π * 40 ≈ 125.66
  const r = 40;
  const circumference = Math.PI * r;
  const filled = (clamped / 100) * circumference;
  const color = clamped >= 70 ? "#22c55e" : clamped >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center justify-center gap-1">
      <svg width="88" height="52" viewBox="0 0 88 52">
        {/* Track arc */}
        <path
          d="M 4 48 A 40 40 0 0 1 84 48"
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Filled arc */}
        <path
          d="M 4 48 A 40 40 0 0 1 84 48"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
        {/* Center percentage */}
        <text x="44" y="46" textAnchor="middle" fill="white" fontSize="14" fontWeight="700">
          {clamped}%
        </text>
      </svg>
      <span className="text-[10px] text-white/40 uppercase tracking-wider">{label}</span>
    </div>
  );
}
