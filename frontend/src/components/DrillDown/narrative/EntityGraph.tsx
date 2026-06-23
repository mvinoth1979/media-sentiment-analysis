import { useQuery } from "@tanstack/react-query";
import { fetchEntityGraph, type EntityNode, type EntityEdge } from "../../../lib/api";

interface Props {
  brandId: string;
  brandName?: string;
  days?: number;
  onEntityDrill?: (entity: string) => void;
}

const W = 480;
const H = 320;
const CX = W / 2;
const CY = H / 2;
const RADIUS = 120;

function nodeColor(n: EntityNode): string {
  const total = n.count || 1;
  const negPct = n.negative_count / total;
  const posPct = n.positive_count / total;
  if (negPct > 0.5) return "#ef4444";
  if (negPct > 0.35) return "#f97316";
  if (posPct > 0.5) return "#22c55e";
  return "#6b7280";
}

function nodeRadius(n: EntityNode, max: number): number {
  return 6 + (n.count / max) * 14;
}

interface LayoutNode extends EntityNode {
  x: number;
  y: number;
  r: number;
}

function Skeleton() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="w-full h-48 bg-white/5 rounded-xl animate-pulse" />
    </div>
  );
}

export function EntityGraph({ brandId, brandName = "Brand", days = 30, onEntityDrill }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["entity-graph", brandId, days],
    queryFn: () => fetchEntityGraph(brandId, days),
    staleTime: 15 * 60_000,
    retry: 1,
  });

  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];

  if (isLoading) return <Skeleton />;
  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-[11px] text-white/25">No entity data for this period</span>
      </div>
    );
  }

  const maxCount = Math.max(...nodes.map(n => n.count), 1);
  const top = nodes.slice(0, 16);

  // Position nodes in a radial layout around center
  const layoutNodes: LayoutNode[] = top.map((n, i) => {
    const angle = (i / top.length) * 2 * Math.PI - Math.PI / 2;
    const dist = RADIUS + (i % 2 === 0 ? 0 : 20); // slight alternation for readability
    return {
      ...n,
      x: CX + dist * Math.cos(angle),
      y: CY + dist * Math.sin(angle),
      r: nodeRadius(n, maxCount),
    };
  });

  const nodeMap = new Map<string, LayoutNode>(layoutNodes.map(n => [n.entity, n]));

  // Max co-occurrence for edge thickness
  const maxCo = Math.max(...edges.map(e => e.co_count), 1);

  return (
    <div className="bg-[#111e36] border border-white/10 rounded-xl flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[11px] font-semibold text-white">Entity Graph</span>
        <span className="text-[9px] text-white/30">co-occurrence · {days}d</span>
        <div className="ml-auto flex gap-2 text-[8px]">
          <span className="flex items-center gap-0.5"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Negative</span>
          <span className="flex items-center gap-0.5"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Positive</span>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex items-center justify-center overflow-hidden p-2">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%" style={{ maxHeight: "100%" }}>
          {/* Edges */}
          {edges.map((e: EntityEdge, i) => {
            const a = nodeMap.get(e.entity_a);
            const b = nodeMap.get(e.entity_b);
            if (!a || !b) return null;
            const thickness = 0.5 + (e.co_count / maxCo) * 2;
            return (
              <line
                key={i}
                x1={a.x} y1={a.y}
                x2={b.x} y2={b.y}
                stroke="rgba(255,255,255,0.08)"
                strokeWidth={thickness}
              />
            );
          })}

          {/* Center brand node */}
          <circle cx={CX} cy={CY} r={22} fill="#1e3a8a" stroke="#3b82f6" strokeWidth={1.5} strokeOpacity={0.6} />
          <text x={CX} y={CY + 1} textAnchor="middle" dominantBaseline="middle" fontSize={8} fill="white" fontWeight="600">
            {brandName.split(" ").slice(0, 2).join(" ")}
          </text>

          {/* Spokes from center to each entity */}
          {layoutNodes.map((n, i) => (
            <line
              key={`spoke-${i}`}
              x1={CX} y1={CY}
              x2={n.x} y2={n.y}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth={0.5}
            />
          ))}

          {/* Entity nodes */}
          {layoutNodes.map((n) => (
            <g
              key={n.entity}
              onClick={() => onEntityDrill?.(n.entity)}
              style={{ cursor: onEntityDrill ? "pointer" : "default" }}
            >
              <circle
                cx={n.x} cy={n.y} r={n.r}
                fill={nodeColor(n)}
                fillOpacity={0.75}
                stroke={nodeColor(n)}
                strokeOpacity={0.4}
                strokeWidth={1}
              />
              {/* Label — only for larger nodes or near center */}
              <text
                x={n.x}
                y={n.y + n.r + 9}
                textAnchor="middle"
                fontSize={7}
                fill="rgba(255,255,255,0.5)"
                style={{ pointerEvents: "none" }}
              >
                {n.entity.length > 14 ? n.entity.slice(0, 12) + "…" : n.entity}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}
