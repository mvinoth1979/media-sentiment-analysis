import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchEntityGraph, type EntityNode } from "../../../lib/api";

interface Props {
  brandId: string;
  days?: number;
  onEntityDrill?: (entity: string) => void;
}

function sentimentBar(node: EntityNode) {
  const total = node.count || 1;
  const posPct = Math.round((node.positive_count / total) * 100);
  const negPct = Math.round((node.negative_count / total) * 100);
  const neuPct = 100 - posPct - negPct;
  return { posPct, negPct, neuPct };
}

function EntityRow({ node, onDrill }: { node: EntityNode; onDrill?: (e: string) => void }) {
  const { posPct, negPct } = sentimentBar(node);
  const dominantColor = negPct > 50 ? "text-red-400" : posPct > 50 ? "text-emerald-400" : "text-white/40";

  return (
    <div
      className={`flex items-center gap-2 py-1.5 group ${onDrill ? "cursor-pointer hover:bg-white/3 rounded" : ""}`}
      onClick={() => onDrill?.(node.entity)}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-medium text-white/80 truncate">{node.entity}</span>
          <span className={`text-[8px] font-semibold ${dominantColor}`}>{node.count}</span>
        </div>
        {/* Stacked sentiment bar */}
        <div className="flex h-1 rounded-full overflow-hidden mt-0.5 bg-white/10">
          {posPct > 0 && <div className="bg-emerald-500" style={{ width: `${posPct}%` }} />}
          {negPct > 0 && <div className="bg-red-500" style={{ width: `${negPct}%` }} />}
        </div>
      </div>
      <div className="text-[8px] text-white/20 shrink-0 flex gap-1.5">
        <span className="text-emerald-400/70">{posPct}%</span>
        <span className="text-red-400/70">{negPct}%</span>
      </div>
      {onDrill && (
        <span className="text-[8px] text-white/20 group-hover:text-white/50 transition-colors shrink-0">↗</span>
      )}
    </div>
  );
}

export function EntityIntelligence({ brandId, days = 30, onEntityDrill }: Props) {
  const [open, setOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["entity-graph", brandId, days],
    queryFn: () => fetchEntityGraph(brandId, days),
    staleTime: 15 * 60_000,
    retry: 1,
    enabled: open,  // lazy-load until expanded
  });

  const nodes = data?.nodes ?? [];

  return (
    <div className="border border-white/8 rounded-lg overflow-hidden">
      {/* Toggle header */}
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-white/3 transition-colors"
      >
        <span className="text-[10px] font-semibold text-white/60">🔗 Entity Intelligence</span>
        {nodes.length > 0 && <span className="text-[9px] text-white/25">{nodes.length} entities</span>}
        <span className="ml-auto text-[9px] text-white/25">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="border-t border-white/5 px-3 py-2 max-h-48 overflow-y-auto" style={{ scrollbarWidth: "none" }}>
          {isLoading ? (
            <div className="space-y-1.5">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-6 bg-white/5 rounded animate-pulse" />
              ))}
            </div>
          ) : nodes.length === 0 ? (
            <span className="text-[10px] text-white/25">No entity data for this period</span>
          ) : (
            <div className="divide-y divide-white/4">
              {nodes.slice(0, 12).map(n => (
                <EntityRow key={n.entity} node={n} onDrill={onEntityDrill} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
