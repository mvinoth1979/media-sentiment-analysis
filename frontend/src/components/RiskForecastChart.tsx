import {
  ComposedChart, Area, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import type { RiskDayPoint, RiskForecastPoint } from "../lib/api";

interface Props {
  historical: RiskDayPoint[];
  forecasts: RiskForecastPoint[];
}

interface ChartPoint {
  label: string;
  actual?: number;
  predicted?: number;
  lower?: number;
  upper?: number;
  isForecast: boolean;
}

function shortDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00Z");
  return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

interface TooltipPayload {
  dataKey: string;
  value: number;
  color: string;
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayload[]; label?: string }) {
  if (!active || !payload?.length) return null;
  const point = payload[0];
  const isForecast = payload.some(p => p.dataKey === "predicted");

  return (
    <div className="bg-[#1a2744] border border-white/15 rounded-lg p-2 text-[10px] space-y-0.5 shadow-xl">
      <div className="text-white/50 font-medium">{label}</div>
      {!isForecast && point && (
        <div className="text-white">Risk: <span className="font-semibold">{point.value?.toFixed(0)}</span>/100</div>
      )}
      {isForecast && payload.map((p) => {
        if (p.dataKey === "predicted") return <div key="pred" className="text-amber-300">Forecast: <span className="font-semibold">{p.value?.toFixed(0)}</span>/100</div>;
        if (p.dataKey === "upper") return <div key="upper" className="text-white/30">Upper: {p.value?.toFixed(0)}</div>;
        if (p.dataKey === "lower") return <div key="lower" className="text-white/30">Lower: {p.value?.toFixed(0)}</div>;
        return null;
      })}
    </div>
  );
}

export function RiskForecastChart({ historical, forecasts }: Props) {
  const today = new Date();
  const histPoints: ChartPoint[] = historical.slice(-10).map(p => ({
    label: shortDate(p.date),
    actual: p.risk_score,
    isForecast: false,
  }));

  const forecastPoints: ChartPoint[] = forecasts.map(f => {
    const d = new Date(today);
    d.setDate(d.getDate() + f.days_ahead);
    return {
      label: shortDate(d.toISOString().slice(0, 10)),
      predicted: f.predicted_risk,
      lower: f.lower,
      upper: f.upper,
      isForecast: true,
    };
  });

  const data: ChartPoint[] = [...histPoints, ...forecastPoints];
  const todayLabel = histPoints.at(-1)?.label ?? "";

  return (
    <div style={{ height: 90 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <XAxis
            dataKey="label"
            tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 7 }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 7 }}
            tickLine={false}
            axisLine={false}
            width={24}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Historical actual risk */}
          <Area
            dataKey="actual"
            type="monotone"
            stroke="#ef4444"
            strokeWidth={1.5}
            fill="#ef444422"
            dot={false}
            connectNulls
          />

          {/* Forecast uncertainty band */}
          <Area
            dataKey="upper"
            type="monotone"
            stroke="transparent"
            fill="#f9731622"
            dot={false}
            connectNulls
          />
          <Area
            dataKey="lower"
            type="monotone"
            stroke="transparent"
            fill="#f9731600"
            dot={false}
            connectNulls
          />

          {/* Forecast center line */}
          <Line
            dataKey="predicted"
            type="monotone"
            stroke="#f97316"
            strokeWidth={1.5}
            strokeDasharray="4 2"
            dot={{ r: 2, fill: "#f97316" }}
            connectNulls
          />

          {/* Divider: today */}
          <ReferenceLine
            x={todayLabel}
            stroke="rgba(255,255,255,0.2)"
            strokeDasharray="2 2"
            label={{ value: "now", fill: "rgba(255,255,255,0.25)", fontSize: 7, position: "insideTopRight" }}
          />

          {/* Risk threshold line */}
          <ReferenceLine
            y={60}
            stroke="rgba(239,68,68,0.25)"
            strokeDasharray="3 3"
            label={{ value: "threshold", fill: "rgba(239,68,68,0.3)", fontSize: 6, position: "insideTopLeft" }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
