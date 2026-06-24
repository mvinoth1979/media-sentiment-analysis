import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { fetchCompetitorSoV, discoverCompetitors } from "../lib/api";
import type { CompetitorSoVData, SoVEntry } from "../lib/types";

interface Props {
  brandId: string;
  compact?: boolean;
  onClick?: () => void;
  onEntityClick?: (name: string) => void;
}

interface TooltipEntry { payload: SoVEntry }
interface SovTooltipProps { active?: boolean; payload?: TooltipEntry[] }

function SovTooltip({ active, payload }: SovTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-lg px-3 py-2 text-xs shadow-md">
      <div className="font-semibold text-white/80">{d.name}</div>
      <div className="text-blue-400 font-bold">{d.pct}% share</div>
      <div className="text-white/40">{d.count.toLocaleString()} mentions</div>
    </div>
  );
}

const FALLBACK_ENTRIES: SoVEntry[] = [
  { name: "Brand", count: 0, pct: 100, color: "#3b82f6", is_brand: true },
];

export function CompetitorShareOfVoice({ brandId, compact, onClick, onEntityClick }: Props) {
  const queryClient = useQueryClient();
  const autoTriggered = useRef(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  const { data, isLoading } = useQuery<CompetitorSoVData>({
    queryKey: ["competitor-sov", brandId],
    queryFn: async () => {
      const result = await fetchCompetitorSoV(brandId);
      // Auto-discover competitors once when in entity_fallback mode
      if (result.source === "entity_fallback" && !autoTriggered.current) {
        autoTriggered.current = true;
        discoverCompetitors(brandId)
          .then(r => {
            if (r.saved) {
              // Invalidate both this component's cache and the KPI card's cache
              queryClient.invalidateQueries({ queryKey: ["competitor-sov", brandId] });
              queryClient.invalidateQueries({ queryKey: ["competitor-sov-kpi", brandId] });
            }
          })
          .catch(() => {});
      }
      return result;
    },
    staleTime: 5 * 60_000,
  });

  const handleRefresh = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isRefreshing) return;
    autoTriggered.current = false;
    setIsRefreshing(true);
    try {
      const r = await discoverCompetitors(brandId);
      if (r.saved) {
        queryClient.invalidateQueries({ queryKey: ["competitor-sov", brandId] });
        queryClient.invalidateQueries({ queryKey: ["competitor-sov-kpi", brandId] });
      }
    } catch {
      // silent
    } finally {
      setIsRefreshing(false);
    }
  };

  const entries = data?.entries ?? FALLBACK_ENTRIES;
  const source = data?.source ?? "entity_fallback";

  if (compact) {
    return (
      <div onClick={onClick} className={`bg-[#1a2744] border border-white/10 rounded-lg p-2 h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="flex items-center justify-between mb-1 flex-none">
          <span className="text-[11px] font-semibold text-white">Share of Voice</span>
          {isLoading && (
            <span className="text-[8px] text-blue-400 animate-pulse">detecting…</span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-1 min-h-0">
          <div className="relative w-[80px] h-[80px] shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={entries} dataKey="pct" cx="50%" cy="50%" innerRadius={22} outerRadius={36} paddingAngle={2} startAngle={90} endAngle={-270}>
                  {entries.map(d => <Cell key={d.name} fill={d.color} strokeWidth={0} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[8px] text-white/40">SoV</span>
            </div>
          </div>
          <div className="flex-1 space-y-1 min-w-0 overflow-hidden">
            {entries.slice(0, 5).map(d => (
              <div key={d.name} className="flex items-center gap-1 text-[9px]">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
                <span className={`truncate flex-1 ${d.is_brand ? "font-semibold text-white" : "text-white/60"}`}>{d.name}</span>
                <span className="font-bold text-white/80 shrink-0">{d.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div onClick={onClick} className={`bg-[#1a2744] border border-white/10 rounded-xl p-4 ${clickable}`}>
      <div className="flex items-center gap-1.5 mb-3">
        <span className="text-sm font-semibold text-white">Competitor Share of Voice</span>
        <div className="relative group">
          <button
            onClick={e => e.stopPropagation()}
            className="w-4 h-4 rounded-full bg-white/10 text-white/40 hover:text-white/70 hover:bg-white/15 flex items-center justify-center text-[10px] font-bold leading-none transition-colors"
            aria-label="Coverage scope information"
          >
            i
          </button>
          <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 rounded-lg bg-[#0d1626] border border-white/10 px-3 py-2 text-[11px] text-white/80 leading-snug shadow-lg opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-20">
            Based on YouTube and news portal coverage only. Twitter/X, Instagram, and Facebook are not yet monitored.
            <span className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-x-4 border-x-transparent border-t-4 border-t-[#0d1626]" />
          </div>
        </div>
        {isLoading && (
          <span className="text-[9px] text-blue-400 animate-pulse ml-auto">Auto-detecting…</span>
        )}
      </div>

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
            <span className="text-[10px] text-white/40">Share of</span>
            <span className="text-[10px] font-bold text-white/60">Voice</span>
          </div>
        </div>

        <div className="flex-1 space-y-1.5">
          {entries.map(d => (
            <div
              key={d.name}
              className={`flex items-center justify-between gap-2 rounded px-1 -mx-1 py-0.5 ${onEntityClick ? "cursor-pointer hover:bg-white/5" : ""}`}
              onClick={onEntityClick ? (e) => { e.stopPropagation(); onEntityClick(d.name); } : undefined}
            >
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
                <span className="text-xs text-white/60 truncate">{d.name}</span>
              </div>
              <span className="text-xs font-bold text-white shrink-0">{d.pct}%</span>
            </div>
          ))}
        </div>
      </div>

      <p className="mt-2 text-[10px] text-white/40 italic">
        YouTube &amp; news coverage only — social media channels excluded.
      </p>

      <div className="mt-2 flex items-center justify-between gap-3">
        <p className="text-[10px] text-white/40 leading-relaxed">
          {source === "configured"
            ? "Based on competitor mentions in brand coverage"
            : "Showing top co-mentioned entities — competitors auto-detecting…"}
        </p>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className={`shrink-0 text-[9px] border rounded px-1.5 py-0.5 transition-colors ${isRefreshing ? "text-blue-400 border-blue-500/30 cursor-not-allowed" : "text-white/25 hover:text-white/50 border-white/10 hover:border-white/20"}`}
          title="Re-run competitor detection"
        >
          {isRefreshing ? <span className="flex items-center gap-1"><span className="w-2 h-2 border border-blue-400 border-t-transparent rounded-full animate-spin inline-block" /> detecting…</span> : "↺ refresh"}
        </button>
      </div>
    </div>
  );
}
