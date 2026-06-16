import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

interface Props {
  positive: number;
  negative: number;
  neutral: number;
  total: number;
}

const SLICES = [
  { key: "positive", label: "Positive", color: "#22c55e", bar: "bg-green-500", text: "text-green-400" },
  { key: "negative", label: "Negative", color: "#ef4444", bar: "bg-red-500",   text: "text-red-400"   },
  { key: "neutral",  label: "Neutral",  color: "#eab308", bar: "bg-yellow-500", text: "text-yellow-400" },
] as const;

export function SentimentPieChart({ positive, negative, neutral, total }: Props) {
  const values: Record<string, number> = { positive, negative, neutral };
  const data = SLICES.map(s => ({ ...s, value: values[s.key] })).filter(d => d.value > 0);
  const pct = (n: number) => total > 0 ? `${Math.round((n / total) * 100)}%` : "0%";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 h-full">
      <div className="text-sm font-semibold text-gray-200 mb-3">Sentiment Breakdown</div>
      <div className="flex items-center gap-4">
        <div className="shrink-0 w-[140px] h-[140px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} cx="50%" cy="50%"
                   innerRadius={42} outerRadius={62}
                   dataKey="value" paddingAngle={2} startAngle={90} endAngle={-270}>
                {data.map(entry => <Cell key={entry.key} fill={entry.color} strokeWidth={0} />)}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
                formatter={(value, _name, props) => {
                  const v = Number(value) || 0;
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  return [`${v} (${pct(v)})`, (props as any).payload?.label ?? ""];
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="flex-1 space-y-3 min-w-0">
          {SLICES.map(s => (
            <div key={s.key}>
              <div className="flex justify-between text-xs mb-1">
                <span className={s.text}>{s.label}</span>
                <span className="text-gray-400">
                  {values[s.key]}
                  <span className="text-gray-600 ml-1">({pct(values[s.key])})</span>
                </span>
              </div>
              <div className="bg-gray-800 rounded-full h-1.5">
                <div className={`${s.bar} h-full rounded-full transition-all`}
                     style={{ width: pct(values[s.key]) }} />
              </div>
            </div>
          ))}
          <div className="text-xs text-gray-600 pt-1">{total} total mentions</div>
        </div>
      </div>
    </div>
  );
}
