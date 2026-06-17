import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LabelList } from "recharts";
import type { SourceStat } from "../../lib/types";

interface Props {
  sources: SourceStat[];
  limit?: number;
  onSelect?: (portalId: string) => void;
}

const SEGMENTS = [
  { key: "positive", label: "Positive", color: "#34d399" },
  { key: "neutral",  label: "Neutral",  color: "#fbbf24" },
  { key: "negative", label: "Negative", color: "#f87171" },
] as const;

interface TickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  nameToId: Map<string, string>;
  onSelect?: (portalId: string) => void;
}

interface BarClickPayload {
  payload?: { portal_id: string };
}

function ClickableTick({ x = 0, y = 0, payload, nameToId, onSelect }: TickProps) {
  const id = payload ? nameToId.get(payload.value) : undefined;
  const clickable = !!(id && onSelect);
  return (
    <text
      x={x}
      y={y}
      dy={4}
      textAnchor="end"
      fontSize={11.5}
      fontWeight={clickable ? 500 : 400}
      fill={clickable ? "#c4b5fd" : "#9ca3af"}
      onClick={clickable ? () => onSelect!(id!) : undefined}
      style={{ cursor: clickable ? "pointer" : "default" }}
    >
      {payload?.value}
    </text>
  );
}

interface TooltipProps {
  active?: boolean;
  payload?: { name: string; value: number; fill: string }[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s, p) => s + (p.value || 0), 0);
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3.5 py-3 shadow-xl text-xs min-w-[160px]">
      <div className="text-gray-200 font-semibold mb-2 capitalize">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="flex items-center justify-between gap-4 py-0.5">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: p.fill }} />
            <span className="text-gray-400">{p.name}</span>
          </span>
          <span className="font-mono text-gray-200">
            {p.value}
            <span className="text-gray-500 ml-1">
              ({total ? Math.round((p.value / total) * 100) : 0}%)
            </span>
          </span>
        </div>
      ))}
      <div className="border-t border-gray-700/60 mt-2 pt-2 text-gray-500 flex justify-between">
        <span>Total</span>
        <span className="font-mono text-gray-300">{total}</span>
      </div>
    </div>
  );
}

export function SourceSentimentChart({ sources, limit = 8, onSelect }: Props) {
  const data = [...sources]
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
    .map(s => ({ ...s, name: s.portal_id.replace(/_/g, " ") }));

  if (data.length === 0) return null;

  const nameToId = new Map(data.map(d => [d.name, d.portal_id]));
  const ROW_HEIGHT = 48;

  return (
    <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm font-semibold text-gray-100 tracking-wide">Sentiment by Source</div>
        <div className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
          {data.length} source{data.length !== 1 ? "s" : ""}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={Math.max(data.length * ROW_HEIGHT, 140)}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 48, top: 4, bottom: 4 }}
          barCategoryGap="30%">
          <CartesianGrid horizontal={false} stroke="#1f2937" strokeDasharray="3 3" opacity={0.6} />
          <XAxis
            type="number"
            tick={{ fill: "#4b5563", fontSize: 10.5 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={120}
            axisLine={false}
            tickLine={false}
            tick={<ClickableTick nameToId={nameToId} onSelect={onSelect} />}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
          {SEGMENTS.map((seg, i) => (
            <Bar
              key={seg.key}
              dataKey={seg.key}
              name={seg.label}
              stackId="sentiment"
              fill={seg.color}
              radius={0}
              style={onSelect ? { cursor: "pointer" } : undefined}
              onClick={onSelect ? (barData: BarClickPayload) => barData.payload && onSelect(barData.payload.portal_id) : undefined}
            >
              {i === SEGMENTS.length - 1 && (
                <LabelList
                  dataKey="count"
                  position="right"
                  style={{ fill: "#6b7280", fontSize: 10.5, fontFamily: "monospace" }}
                />
              )}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>

      <div className="flex gap-2.5 mt-3">
        {SEGMENTS.map(seg => (
          <span
            key={seg.key}
            className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full"
            style={{
              background: seg.color + "18",
              border: `1px solid ${seg.color}40`,
              color: seg.color,
            }}
          >
            {seg.label}
          </span>
        ))}
      </div>
    </div>
  );
}
