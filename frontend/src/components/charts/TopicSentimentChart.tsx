import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { TopicStat } from "../../lib/types";

interface Props {
  topics: TopicStat[];
  limit?: number;
  onSelect?: (topic: string) => void;
}

const SEGMENTS = [
  { key: "positive", label: "Positive", color: "#22c55e" },
  { key: "neutral", label: "Neutral", color: "#eab308" },
  { key: "negative", label: "Negative", color: "#ef4444" },
] as const;

interface TickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  nameToTopic: Map<string, string>;
  onSelect?: (topic: string) => void;
}

interface BarClickPayload {
  payload?: { topic: string };
}

function ClickableTick({ x = 0, y = 0, payload, nameToTopic, onSelect }: TickProps) {
  const topic = payload ? nameToTopic.get(payload.value) : undefined;
  return (
    <text
      x={x}
      y={y}
      dy={4}
      textAnchor="end"
      fontSize={11}
      fill="#9ca3af"
      onClick={topic && onSelect ? () => onSelect(topic) : undefined}
      style={{ cursor: topic && onSelect ? "pointer" : "default" }}
    >
      {payload?.value}
    </text>
  );
}

export function TopicSentimentChart({ topics, limit = 8, onSelect }: Props) {
  const data = [...topics]
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
    .map(t => ({ ...t, name: t.topic.replace(/_/g, " ") }));

  if (data.length === 0) return null;

  const nameToTopic = new Map(data.map(d => [d.name, d.topic]));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-sm font-semibold text-gray-200 mb-3">Sentiment by Topic</div>
      <ResponsiveContainer width="100%" height={Math.max(data.length * 36, 120)}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid horizontal={false} stroke="#1f2937" />
          <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }} allowDecimals={false} />
          <YAxis
            type="category"
            dataKey="name"
            width={110}
            tick={<ClickableTick nameToTopic={nameToTopic} onSelect={onSelect} />}
          />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#e5e7eb" }}
          />
          {SEGMENTS.map(seg => (
            <Bar
              key={seg.key}
              dataKey={seg.key}
              name={seg.label}
              stackId="sentiment"
              fill={seg.color}
              radius={0}
              style={onSelect ? { cursor: "pointer" } : undefined}
              onClick={onSelect ? (barData: BarClickPayload) => barData.payload && onSelect(barData.payload.topic) : undefined}
            />
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
