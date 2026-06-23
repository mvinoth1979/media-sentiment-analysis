import { useQuery } from "@tanstack/react-query";
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
} from "recharts";
import { fetchIssueRadar, type IssueRadarPoint } from "../../lib/api";

interface Props {
  brandId: string;
  days: number;
  onIssueDrill?: (issue: string) => void;
}

const ISSUE_LABEL: Record<string, string> = {
  product_quality:   "Product Quality",
  customer_service:  "Customer Service",
  pricing:           "Pricing",
  csr:               "CSR",
  political:         "Political",
  legal:             "Legal",
  hr_employee:       "HR / Employee",
  technology:        "Technology",
  supply_chain:      "Supply Chain",
  marketing:         "Marketing",
  financial:         "Financial",
  other:             "Other",
};

function sentimentColor(p: IssueRadarPoint): string {
  const neg_pct = p.count > 0 ? p.negative_count / p.count : 0;
  const pos_pct = p.count > 0 ? p.positive_count / p.count : 0;
  if (neg_pct > 0.5) return "#ef4444";       // dominant negative → red
  if (neg_pct > 0.35) return "#f97316";      // mixed negative → orange
  if (pos_pct > 0.5) return "#22c55e";       // dominant positive → green
  return "#6b7280";                          // neutral / mixed → grey
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: { payload: IssueRadarPoint }[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const neg_pct = d.count > 0 ? Math.round((d.negative_count / d.count) * 100) : 0;
  const pos_pct = d.count > 0 ? Math.round((d.positive_count / d.count) * 100) : 0;
  const neu_pct = 100 - neg_pct - pos_pct;
  return (
    <div className="bg-[#1a2744] border border-white/15 rounded-lg p-2.5 text-[10px] space-y-1 shadow-xl max-w-[160px]">
      <div className="font-semibold text-white text-[11px]">{ISSUE_LABEL[d.issue] ?? d.issue}</div>
      <div className="text-white/50">{d.count} mentions</div>
      <div className="flex gap-2 text-[9px]">
        <span className="text-emerald-400">↑{pos_pct}%</span>
        <span className="text-red-400">↓{neg_pct}%</span>
        <span className="text-white/30">={neu_pct}%</span>
      </div>
      <div className={`font-medium ${d.velocity >= 3 ? "text-red-400" : d.velocity >= 1.5 ? "text-amber-400" : "text-white/40"}`}>
        {d.velocity >= 3 ? "⚠ " : d.velocity >= 1.5 ? "▲ " : ""}
        {d.velocity.toFixed(1)}× vs baseline
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="w-full h-32 bg-white/5 rounded animate-pulse" />
    </div>
  );
}

export function IssueRadarBubble({ brandId, days, onIssueDrill }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["issue-radar", brandId, days],
    queryFn: () => fetchIssueRadar(brandId, days),
    staleTime: 10 * 60_000,
    retry: 1,
  });

  const points = data?.points ?? [];

  // Avg velocity for reference line
  const avgVelocity = points.length
    ? points.reduce((s, p) => s + p.velocity, 0) / points.length
    : 1;

  return (
    <div className="bg-[#111e36] border border-white/10 rounded-xl flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[11px] font-semibold text-white">Issue Radar</span>
        <span className="text-[9px] text-white/30">velocity × volume</span>
        <div className="ml-auto flex items-center gap-2 text-[8px]">
          <span className="flex items-center gap-0.5"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />Crisis risk</span>
          <span className="flex items-center gap-0.5"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />Positive</span>
          <span className="flex items-center gap-0.5"><span className="w-2 h-2 rounded-full bg-gray-500 inline-block" />Neutral</span>
        </div>
      </div>

      <div className="flex-1 min-h-0 px-1 py-2">
        {isLoading ? (
          <Skeleton />
        ) : points.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-[11px] text-white/25">No issue data for this period</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 14, right: 10, bottom: 20, left: 0 }}>
              <XAxis
                dataKey="velocity"
                type="number"
                name="Velocity"
                tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 8 }}
                tickLine={false}
                axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                label={{ value: "Velocity (× baseline)", position: "insideBottom", offset: -10, fill: "rgba(255,255,255,0.2)", fontSize: 7 }}
              />
              <YAxis
                dataKey="count"
                type="number"
                name="Volume"
                tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 8 }}
                tickLine={false}
                axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                width={28}
              />
              <ZAxis dataKey="reach" range={[30, 600]} />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(255,255,255,0.1)" }} />
              <ReferenceLine
                x={avgVelocity}
                stroke="rgba(255,255,255,0.12)"
                strokeDasharray="3 3"
                label={{ value: "avg", fill: "rgba(255,255,255,0.2)", fontSize: 7, position: "top" }}
              />
              <Scatter
                data={points}
                onClick={(d) => onIssueDrill?.((d as unknown as IssueRadarPoint).issue)}
                style={{ cursor: onIssueDrill ? "pointer" : "default" }}
                shape={(props: { cx?: number; cy?: number; payload?: IssueRadarPoint; r?: number }) => {
                  const { cx = 0, cy = 0, payload, r = 8 } = props;
                  if (!payload) return <g />;
                  return (
                    <g>
                      <circle
                        cx={cx} cy={cy} r={r}
                        fill={sentimentColor(payload)}
                        fillOpacity={0.7}
                        stroke={sentimentColor(payload)}
                        strokeOpacity={0.3}
                        strokeWidth={1}
                      />
                      <text x={cx} y={cy - r - 3} textAnchor="middle" fontSize={7} fill="rgba(255,255,255,0.45)">
                        {(ISSUE_LABEL[payload.issue] ?? payload.issue).split(" ")[0]}
                      </text>
                    </g>
                  );
                }}
              >
                {points.map((p) => (
                  <Cell key={p.issue} fill={sentimentColor(p)} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
