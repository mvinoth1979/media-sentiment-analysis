import { useQuery } from "@tanstack/react-query";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts";
import { fetchNarrativeDNA } from "../../../lib/api";

interface Props {
  brandId: string;
  days?: number;
}

const AXES = [
  { key: "fear",          label: "Fear",          desc: "Regulatory / crisis signals" },
  { key: "criticism",     label: "Criticism",     desc: "Negative editorial tone" },
  { key: "consumer_trust",label: "Consumer Trust",desc: "Review-source sentiment" },
  { key: "political",     label: "Political",     desc: "Political / legal coverage" },
  { key: "brand_safety",  label: "Brand Safety",  desc: "Inverse of negative %" },
] as const;

interface TooltipPayload { payload: Record<string, number>; name: string }

function CustomTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-[#1a2744] border border-white/15 rounded-lg p-2 text-[9px] space-y-0.5 shadow-xl">
      {AXES.map(ax => (
        <div key={ax.key} className="flex gap-2 justify-between">
          <span className="text-white/40">{ax.label}</span>
          <span className="font-semibold text-white">{Math.round(d[ax.key] ?? 0)}</span>
        </div>
      ))}
    </div>
  );
}

function Skeleton() {
  return <div className="w-full h-36 bg-white/5 rounded animate-pulse" />;
}

export function NarrativeDNA({ brandId, days = 30 }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["narrative-dna", brandId, days],
    queryFn: () => fetchNarrativeDNA(brandId, days),
    staleTime: 15 * 60_000,
    retry: 1,
  });

  const chartData = data
    ? AXES.map(ax => ({ axis: ax.label, value: data[ax.key] }))
    : AXES.map(ax => ({ axis: ax.label, value: 0 }));

  return (
    <div className="bg-[#111e36] border border-white/10 rounded-xl flex flex-col overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[11px] font-semibold text-white">Narrative DNA</span>
        <span className="text-[9px] text-white/30">5-axis sentiment profile · {days}d</span>
      </div>

      <div className="p-2" style={{ height: 200 }}>
        {isLoading ? (
          <Skeleton />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartData}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis
                dataKey="axis"
                tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 8 }}
              />
              <Radar
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.2}
                strokeWidth={1.5}
              />
              <Tooltip content={<CustomTooltip />} />
            </RadarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Axis legend */}
      {data && (
        <div className="px-3 pb-2 grid grid-cols-1 gap-0.5">
          {AXES.map(ax => {
            const val = Math.round(data[ax.key]);
            const color = ax.key === "brand_safety" || ax.key === "consumer_trust"
              ? val > 60 ? "text-emerald-400" : val > 40 ? "text-amber-400" : "text-red-400"
              : val > 60 ? "text-red-400" : val > 30 ? "text-amber-400" : "text-emerald-400";
            return (
              <div key={ax.key} className="flex items-center justify-between text-[8px]">
                <span className="text-white/30">{ax.label}</span>
                <div className="flex items-center gap-1.5">
                  <div className="w-16 h-0.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500/60" style={{ width: `${val}%` }} />
                  </div>
                  <span className={`font-semibold w-6 text-right ${color}`}>{val}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
