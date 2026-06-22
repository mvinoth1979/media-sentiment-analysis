type KPIVariant = "default" | "sparkline" | "donut";
type RiskLabel  = "Good" | "Medium" | "High" | "Critical";

interface Props {
  label: string;
  value: string | number;
  pct?: number;
  delta?: number | null;
  deltaUnit?: string;
  sub?: string;
  icon?: string;
  accentColor?: "green" | "red" | "gray" | "blue" | "purple";
  variant?: KPIVariant;
  sparklineData?: number[];
  riskLabel?: RiskLabel;
  onClick?: () => void;
}

// SVG hex colors for the donut stroke (Tailwind classes don't apply to SVG stroke)
const ACCENT_HEX: Record<string, string> = {
  green:  "#34d399",
  red:    "#f87171",
  gray:   "rgba(255,255,255,0.35)",
  blue:   "#60a5fa",
  purple: "#a78bfa",
};

const ACCENT_GLOW: Record<string, string> = {
  green:  "text-emerald-400",
  red:    "text-red-400",
  gray:   "text-white/40",
  blue:   "text-blue-400",
  purple: "text-purple-400",
};

const RISK_CHIP: Record<RiskLabel, string> = {
  Good:     "bg-emerald-500/15 text-emerald-400",
  Medium:   "bg-amber-500/15 text-amber-400",
  High:     "bg-red-500/15 text-red-400",
  Critical: "bg-red-700/20 text-red-300",
};

function DeltaBadge({ delta, unit }: { delta: number; unit: string }) {
  const isPos = delta > 0;
  const isNeg = delta < 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-[9px] font-semibold px-1.5 py-0.5 rounded-full ${
      isPos ? "bg-emerald-500/15 text-emerald-400" :
      isNeg ? "bg-red-500/15 text-red-400" :
      "bg-white/8 text-white/40"
    }`}>
      {isPos ? "▲" : isNeg ? "▼" : "—"}{Math.abs(delta).toFixed(1)}{unit}
    </span>
  );
}

// Inline SVG donut ring — pct 0..100
function Donut({ pct, color, size = 40 }: { pct: number; color: string; size?: number }) {
  const r = size / 2 - 4;
  const cx = size / 2;
  const circ = 2 * Math.PI * r;
  const filled = Math.min(Math.max(pct, 0), 100) / 100 * circ;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
      {/* Track */}
      <circle cx={cx} cy={cx} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={3.5} />
      {/* Value arc */}
      <circle
        cx={cx} cy={cx} r={r} fill="none"
        stroke={color} strokeWidth={3.5}
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circ}`}
        transform={`rotate(-90 ${cx} ${cx})`}
        style={{ transition: "stroke-dasharray 0.6s ease" }}
      />
      {/* Centre label */}
      <text x={cx} y={cx + 1} textAnchor="middle" dominantBaseline="middle"
        fill="rgba(255,255,255,0.75)" fontSize={size < 36 ? 7 : 9} fontWeight="700">
        {pct.toFixed(0)}%
      </text>
    </svg>
  );
}

// Inline SVG sparkline
function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null;

  const W = 100, H = 28;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const px = (i: number) => (i / (data.length - 1)) * W;
  const py = (v: number) => H - ((v - min) / range) * (H - 4) - 2;

  const points = data.map((v, i) => `${px(i)},${py(v)}`).join(" ");
  const lastX = px(data.length - 1);
  const lastY = py(data[data.length - 1]);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 28 }} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`sg-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {/* Area fill */}
      <path d={`M0,${py(data[0])} L${points} L${W},${py(data[data.length-1])} L${W},${H} L0,${H} Z`}
        fill={`url(#sg-${color})`} />
      {/* Line */}
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      {/* Last point dot */}
      <circle cx={lastX} cy={lastY} r={2.5} fill={color} />
    </svg>
  );
}

export function KPICard({
  label, value, pct, delta, deltaUnit = "%", sub, icon,
  accentColor = "blue", variant = "default", sparklineData = [], riskLabel, onClick,
}: Props) {
  const hex   = ACCENT_HEX[accentColor]  ?? ACCENT_HEX.blue;
  const glow  = ACCENT_GLOW[accentColor] ?? ACCENT_GLOW.blue;
  const clickable = onClick ? "cursor-pointer hover:border-white/25 hover:bg-white/[0.06] transition-all" : "";

  // ── Donut variant ──────────────────────────────────────────────────────────
  if (variant === "donut") {
    return (
      <div
        onClick={onClick}
        className={`bg-[#1a2744] border border-white/10 rounded-xl px-3 py-2.5 flex flex-col gap-1.5 ${clickable}`}
      >
        <div className="flex items-start justify-between gap-1">
          <div className="min-w-0">
            <div className="text-[9px] text-white/40 uppercase tracking-wider font-medium truncate">{label}</div>
            <div className={`text-lg font-bold leading-tight mt-0.5 ${glow}`}>{value}</div>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            {riskLabel && (
              <span className={`text-[8px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full ${RISK_CHIP[riskLabel]}`}>
                {riskLabel}
              </span>
            )}
            {pct != null && <Donut pct={pct} color={hex} size={40} />}
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap min-h-[16px]">
          {delta != null && <DeltaBadge delta={delta} unit={deltaUnit} />}
          {sub && <span className="text-[9px] text-white/30">{sub}</span>}
          {icon && <span className="ml-auto text-sm opacity-40">{icon}</span>}
        </div>
      </div>
    );
  }

  // ── Sparkline variant ──────────────────────────────────────────────────────
  if (variant === "sparkline") {
    return (
      <div
        onClick={onClick}
        className={`bg-[#1a2744] border border-white/10 rounded-xl px-3 py-2.5 flex flex-col gap-1 ${clickable}`}
      >
        <div className="flex items-start justify-between gap-1">
          <div className="min-w-0">
            <div className="text-[9px] text-white/40 uppercase tracking-wider font-medium truncate">{label}</div>
            <div className={`text-lg font-bold leading-tight mt-0.5 ${glow}`}>{value}</div>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            {riskLabel && (
              <span className={`text-[8px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full ${RISK_CHIP[riskLabel]}`}>
                {riskLabel}
              </span>
            )}
            {icon && <span className="text-base opacity-40 mt-0.5">{icon}</span>}
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap min-h-[16px]">
          {delta != null && <DeltaBadge delta={delta} unit={deltaUnit} />}
          {sub && <span className="text-[9px] text-white/30">{sub}</span>}
        </div>
        {sparklineData.length >= 2 && (
          <div className="mt-0.5">
            <Sparkline data={sparklineData} color={hex} />
          </div>
        )}
      </div>
    );
  }

  // ── Default variant ────────────────────────────────────────────────────────
  return (
    <div
      onClick={onClick}
      className={`bg-[#1a2744] border border-white/10 rounded-xl px-3 py-2.5 flex flex-col gap-1.5 ${clickable}`}
    >
      <div className="flex items-center justify-between gap-1">
        <div className="text-[9px] text-white/40 uppercase tracking-wider font-medium">{label}</div>
        {icon && <span className="text-sm opacity-40 shrink-0">{icon}</span>}
      </div>
      <div className="flex items-baseline gap-1.5 flex-wrap">
        <span className={`text-lg font-bold leading-tight ${glow}`}>{value}</span>
        {pct != null && <span className="text-[10px] text-white/40">({pct.toFixed(1)}%)</span>}
      </div>
      <div className="flex items-center gap-1.5 flex-wrap min-h-[16px]">
        {delta != null && <DeltaBadge delta={delta} unit={deltaUnit} />}
        {sub && <span className="text-[9px] text-white/30">{sub}</span>}
      </div>
    </div>
  );
}
