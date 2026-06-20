interface Props {
  label: string;
  value: string | number;
  pct?: number;
  delta?: number | null;
  deltaUnit?: string;
  sub?: string;
  icon?: string;
  accentColor?: "green" | "red" | "gray" | "blue" | "purple";
  color?: string;
}

const ACCENT: Record<string, { icon: string }> = {
  green:  { icon: "bg-green-100 text-green-600"   },
  red:    { icon: "bg-red-100 text-red-500"        },
  gray:   { icon: "bg-gray-100 text-gray-500"      },
  blue:   { icon: "bg-blue-100 text-blue-600"      },
  purple: { icon: "bg-purple-100 text-purple-600"  },
};

export function KPICard({ label, value, pct, delta, deltaUnit = "%", sub, icon, accentColor = "blue" }: Props) {
  const accent = ACCENT[accentColor] ?? ACCENT.blue;
  const isPos = delta != null && delta > 0;
  const isNeg = delta != null && delta < 0;

  return (
    <div className="bg-white border border-gray-200 rounded-xl px-3 py-2.5 flex flex-col gap-1 shadow-sm">
      <div className="flex items-center justify-between gap-1">
        <div className="text-[11px] text-gray-500 font-medium leading-tight">{label}</div>
        {icon && (
          <div className={`w-6 h-6 rounded-md flex items-center justify-center text-sm shrink-0 ${accent.icon}`}>
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-1.5 flex-wrap">
        <span className="text-xl font-bold text-gray-900 leading-tight">{value}</span>
        {pct != null && (
          <span className="text-xs text-gray-500 font-medium">({pct.toFixed(1)}%)</span>
        )}
      </div>

      {delta != null && (
        <div className="flex items-center gap-1.5">
          <span className={`inline-flex items-center gap-0.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
            isPos ? "bg-green-50 text-green-600" :
            isNeg ? "bg-red-50 text-red-500" :
            "bg-gray-100 text-gray-500"
          }`}>
            {isPos ? "▲" : isNeg ? "▼" : "—"} {Math.abs(delta).toFixed(1)}{deltaUnit}
          </span>
          {sub && <span className="text-[10px] text-gray-400">{sub}</span>}
        </div>
      )}
      {delta == null && sub && (
        <div className="text-[10px] text-gray-400">{sub}</div>
      )}
    </div>
  );
}
