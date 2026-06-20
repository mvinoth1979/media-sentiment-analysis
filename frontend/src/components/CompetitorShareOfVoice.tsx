import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

interface Props {
  brandName?: string;
}

const COMPETITORS = [
  { name: "CIPET",        pct: 40.2, color: "#3b82f6" },
  { name: "Competitor A", pct: 33.3, color: "#8b5cf6" },
  { name: "Competitor B", pct: 18.9, color: "#06b6d4" },
  { name: "Competitor C", pct: 5.1,  color: "#f59e0b" },
  { name: "Others",       pct: 3.3,  color: "#d1d5db" },
];

interface TooltipEntry { payload: { name: string; pct: number } }
interface SovTooltipProps { active?: boolean; payload?: TooltipEntry[] }

function SovTooltip({ active, payload }: SovTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs shadow-md">
      <div className="font-semibold text-gray-700">{d.name}</div>
      <div className="text-blue-600 font-bold">{d.pct}% share</div>
    </div>
  );
}

export function CompetitorShareOfVoice({ brandName }: Props) {
  const data = brandName
    ? COMPETITORS.map(c => ({ ...c, name: c.name === "CIPET" ? brandName : c.name }))
    : COMPETITORS;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="text-sm font-semibold text-gray-800 mb-3">Competitor Share of Voice</div>

      <div className="flex items-center gap-3">
        {/* Donut */}
        <div className="relative w-[110px] h-[110px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data} dataKey="pct"
                cx="50%" cy="50%"
                innerRadius={32} outerRadius={52}
                paddingAngle={2}
                startAngle={90} endAngle={-270}
              >
                {data.map(d => <Cell key={d.name} fill={d.color} strokeWidth={0} />)}
              </Pie>
              <Tooltip content={<SovTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-[10px] text-gray-500">Share of</span>
            <span className="text-[10px] font-bold text-gray-700">Voice</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-1.5">
          {data.map(d => (
            <div key={d.name} className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
                <span className="text-xs text-gray-600 truncate">{d.name}</span>
              </div>
              <span className="text-xs font-bold text-gray-800 shrink-0">{d.pct}%</span>
            </div>
          ))}
        </div>
      </div>

      <p className="text-[10px] text-gray-400 mt-3">
        Placeholder data — connect competitor brand IDs to enable live tracking.
      </p>
    </div>
  );
}
