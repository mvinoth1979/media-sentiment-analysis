import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { TrendPoint } from "../../lib/types";

export function SentimentTrendChart({ data }: { data: TrendPoint[] }) {
  const formatted = data.map(d => ({
    time: new Date(d.time).toLocaleDateString("en-IN", { weekday: "short" }),
    score: Math.round(d.value),
  }));
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-sm font-semibold text-gray-200 mb-3">Perception Score — 7 Days</div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={formatted}>
          <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 11 }} />
          <YAxis domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#1f2937", border: "none" }} />
          <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
