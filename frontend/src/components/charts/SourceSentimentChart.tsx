import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { SourceStat } from "../../lib/types";

interface Props {
  sources: SourceStat[];
  limit?: number;
  onSelect?: (portalId: string) => void;
}

const SEGMENTS = [
  { key: "positive", label: "Positive", color: "#22c55e" },
  { key: "neutral", label: "Neutral", color: "#eab308" },
  { key: "negative", label: "Negative", color: "#ef4444" },
] as const;

interface TickProps {
  x: number;
  y: number;
  payload: { value: string };
  nameToId: Map<string, string>;
  onSelect?: (portalId: string) => void;
}

interface BarClickPayload {
  payload: { portal_id: string };
}

function ClickableTick({ x, y, payload, nameToId, onSelect }: TickProps) {
  const id = nameToId.get(payload.value);
  return (
    <text
      x={x}
      y={y}
      dy={4}
      textAnchor="end"
      fontSize={11}
      fill="#9ca3af"
      onClick={id && onSelect ? () => onSelect(id) : undefined}
      style={{ cursor: id && onSelect ? "pointer" : "default" }}
    >
      {payload.value}
    </text>
  );
}

export function SourceSentimentChart({ sources, limit = 8, onSelect }: Props) {
  const data = [...sources]
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
    .map(s => ({ ...s, name: s.portal_id.replace(/_/g, " ") }));

  if (data.length === 0) return null;

  const nameToId = new Map(data.map(d => [d.name, d.portal_id]));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-sm font-semibold text-gray-200 mb-3">Sentiment by Source</div>
      <ResponsiveContainer width="100%" height={Math.max(data.length * 36, 120)}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid horizontal={false} stroke="#1f2937" />
          <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }} allowDecimals={false} />
          <YAxis
            type="category"
            dataKey="name"
            width={110}
            tick={<ClickableTick nameToId={nameToId} onSelect={onSelect} />}
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
              onClick={onSelect ? (barData: BarClickPayload) => onSelect(barData.payload.portal_id) : undefined}
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
