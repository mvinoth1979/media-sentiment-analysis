import { useCallback, useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { fetchCompetitorSoV, discoverCompetitors } from "../lib/api";
import type { CompetitorSoVData, SoVEntry } from "../lib/types";

interface Props {
  brandId: string;
  brandName?: string;
  compact?: boolean;
  onClick?: () => void;
}

interface TooltipEntry { payload: SoVEntry }
interface SovTooltipProps { active?: boolean; payload?: TooltipEntry[] }

function SovTooltip({ active, payload }: SovTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs shadow-md">
      <div className="font-semibold text-gray-700">{d.name}</div>
      <div className="text-blue-600 font-bold">{d.pct}% share</div>
      <div className="text-gray-400">{d.count.toLocaleString()} mentions</div>
    </div>
  );
}

const FALLBACK_ENTRIES: SoVEntry[] = [
  { name: "Brand", count: 0, pct: 100, color: "#3b82f6", is_brand: true },
];

export function CompetitorShareOfVoice({ brandId, compact, onClick }: Props) {
  const [data, setData] = useState<CompetitorSoVData | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [discovered, setDiscovered] = useState<string[] | null>(null);
  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  const load = useCallback(() => {
    fetchCompetitorSoV(brandId).then(setData).catch(() => {});
  }, [brandId]);

  useEffect(() => { load(); }, [load]);

  const handleDiscover = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setDiscovering(true);
    setDiscovered(null);
    try {
      const result = await discoverCompetitors(brandId);
      setDiscovered(result.competitors);
      load(); // refresh SoV with newly saved competitors
    } catch {
      setDiscovered([]);
    } finally {
      setDiscovering(false);
    }
  };

  const entries = data?.entries ?? FALLBACK_ENTRIES;
  const source = data?.source ?? "entity_fallback";

  if (compact) {
    return (
      <div onClick={onClick} className={`bg-white border border-gray-200 rounded-lg p-2 shadow-sm h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="text-[11px] font-semibold text-gray-800 mb-1 flex-none">Share of Voice</div>
        <div className="flex items-center gap-2 flex-1 min-h-0">
          <div className="relative w-[70px] h-[70px] shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={entries} dataKey="pct" cx="50%" cy="50%" innerRadius={20} outerRadius={32} paddingAngle={2} startAngle={90} endAngle={-270}>
                  {entries.map(d => <Cell key={d.name} fill={d.color} strokeWidth={0} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <span className="text-[8px] text-gray-500">SoV</span>
            </div>
          </div>
          <div className="flex-1 space-y-1 min-w-0 overflow-hidden">
            {entries.slice(0, 4).map(d => (
              <div key={d.name} className="flex items-center gap-1 text-[9px]">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
                <span className="text-gray-600 truncate flex-1">{d.name}</span>
                <span className="font-bold text-gray-700 shrink-0">{d.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div onClick={onClick} className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${clickable}`}>
      <div className="text-sm font-semibold text-gray-800 mb-3">Competitor Share of Voice</div>

      <div className="flex items-center gap-3">
        <div className="relative w-[110px] h-[110px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={entries} dataKey="pct"
                cx="50%" cy="50%"
                innerRadius={32} outerRadius={52}
                paddingAngle={2}
                startAngle={90} endAngle={-270}
              >
                {entries.map(d => <Cell key={d.name} fill={d.color} strokeWidth={0} />)}
              </Pie>
              <Tooltip content={<SovTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-[10px] text-gray-500">Share of</span>
            <span className="text-[10px] font-bold text-gray-700">Voice</span>
          </div>
        </div>

        <div className="flex-1 space-y-1.5">
          {entries.map(d => (
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

      <div className="mt-3 flex items-start justify-between gap-3">
        <p className="text-[10px] text-gray-400 leading-relaxed">
          {source === "configured"
            ? "Based on competitor mentions in brand coverage"
            : "Showing top co-mentioned entities — no competitors configured yet"}
        </p>
        <div className="shrink-0 text-right">
          {discovered !== null && discovered.length > 0 && (
            <p className="text-[10px] text-green-600 mb-1">
              Saved: {discovered.join(", ")}
            </p>
          )}
          {discovered !== null && discovered.length === 0 && (
            <p className="text-[10px] text-red-400 mb-1">Discovery failed — try again</p>
          )}
          <button
            onClick={handleDiscover}
            disabled={discovering}
            className="text-[10px] font-medium px-2 py-1 rounded border border-blue-200 text-blue-600 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {discovering ? "Detecting…" : "✦ Auto-detect with AI"}
          </button>
        </div>
      </div>
    </div>
  );
}
