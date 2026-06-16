import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { TopicStat } from "../../lib/types";

interface Props {
  topics: TopicStat[];
  limit?: number;
}

const SEGMENTS = [
  { key: "positive", label: "Positive", color: "#22c55e" },
  { key: "neutral", label: "Neutral", color: "#eab308" },
  { key: "negative", label: "Negative", color: "#ef4444" },
] as const;

export function TopicSentimentChart({ topics, limit = 8 }: Props) {
  const data = [...topics]
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
    .map(t => ({ ...t, name: t.topic.replace(/_/g, " ") }));

  if (data.length === 0) return null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-sm font-semibold text-gray-200 mb-3">Sentiment by Topic</div>
      <ResponsiveContainer width="100%" height={Math.max(data.length * 36, 120)}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid horizontal={false} stroke="#1f2937" />
          <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }} allowDecimals={false} />
          <YAxis type="category" dataKey="name" width={110} tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#e5e7eb" }}
          />
          {SEGMENTS.map(seg => (
            <Bar key={seg.key} dataKey={seg.key} name={seg.label} stackId="sentiment" fill={seg.color} radius={0} />
          ))}
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-4 mt-2 text-[11px] text-gray-500">
        {SEGMENTS.map(seg => (
          <span key={seg.key} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: seg.color }} />
            {seg.label}
          </span>
        ))}
      </div>
    </div>
  );
}
