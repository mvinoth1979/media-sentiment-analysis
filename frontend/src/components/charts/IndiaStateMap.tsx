import { useState } from "react";
import type { StateStat } from "../../lib/types";

interface Props {
  data: StateStat[];
  onStateClick?: (state: string) => void;
}

interface Tooltip {
  name: string;
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  x: number;
  y: number;
}

function sentimentColor(stat: StateStat): { bg: string; text: string; border: string } {
  const positivePct = stat.positive / stat.count;
  const negativePct = stat.negative / stat.count;

  if (positivePct >= 0.6) return { bg: "bg-green-900/60", text: "text-green-300", border: "border-green-700/50" };
  if (positivePct >= 0.4) return { bg: "bg-green-900/40", text: "text-green-400", border: "border-green-800/50" };
  if (negativePct >= 0.6) return { bg: "bg-red-900/60", text: "text-red-300", border: "border-red-700/50" };
  if (negativePct >= 0.4) return { bg: "bg-red-900/40", text: "text-red-400", border: "border-red-800/50" };
  return { bg: "bg-gray-800/60", text: "text-gray-300", border: "border-gray-700/50" };
}

export function IndiaStateMap({ data, onStateClick }: Props) {
  const [tooltip, setTooltip] = useState<Tooltip | null>(null);

  const sorted = [...data].sort((a, b) => b.count - a.count);

  return (
    <div className="relative bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-1">
        <div className="text-sm font-semibold text-gray-200">State-level Sentiment</div>
        {data.length > 0 && (
          <span className="text-xs text-gray-600">{data.length} state{data.length !== 1 ? "s" : ""} with mentions</span>
        )}
      </div>
      <p className="text-xs text-gray-500 mb-3">
        Click a state to filter mentions
      </p>

      {data.length === 0 ? (
        <div className="py-6 text-center">
          <p className="text-xs text-gray-600">
            State data will appear after the next pipeline run
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
          {sorted.map(stat => {
            const colors = sentimentColor(stat);
            return (
              <button
                key={stat.state}
                onClick={() => onStateClick?.(stat.state)}
                onMouseEnter={e => {
                  setTooltip({
                    name: stat.state,
                    total: stat.count,
                    positive: stat.positive,
                    negative: stat.negative,
                    neutral: stat.neutral,
                    x: e.clientX,
                    y: e.clientY,
                  });
                }}
                onMouseMove={e => {
                  setTooltip(prev => prev ? { ...prev, x: e.clientX, y: e.clientY } : prev);
                }}
                onMouseLeave={() => setTooltip(null)}
                className={`text-left px-2.5 py-2 rounded-lg border ${colors.bg} ${colors.border} hover:ring-1 hover:ring-indigo-500/50 transition-all`}
              >
                <div className={`text-xs font-medium ${colors.text} truncate`}>{stat.state}</div>
                <div className="text-[10px] text-gray-500 mt-0.5">{stat.count} mention{stat.count !== 1 ? "s" : ""}</div>
              </button>
            );
          })}
        </div>
      )}

      {/* Legend */}
      {data.length > 0 && (
        <div className="flex flex-wrap gap-3 mt-3 pt-3 border-t border-gray-800">
          {[
            { bg: "bg-green-900/60", label: "Strong positive" },
            { bg: "bg-green-900/40", label: "Positive" },
            { bg: "bg-gray-800/60", label: "Neutral" },
            { bg: "bg-red-900/40", label: "Negative" },
            { bg: "bg-red-900/60", label: "Strong negative" },
          ].map(({ bg, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div className={`w-3 h-3 rounded-sm border border-gray-600 ${bg}`} />
              <span className="text-[10px] text-gray-500">{label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-xl"
          style={{ left: tooltip.x + 12, top: tooltip.y - 10 }}
        >
          <div className="font-semibold text-gray-100 mb-1">{tooltip.name}</div>
          <div className="space-y-0.5 text-gray-400">
            <div>{tooltip.total} mention{tooltip.total !== 1 ? "s" : ""}</div>
            <div className="text-emerald-400">+{tooltip.positive} positive</div>
            <div className="text-red-400">−{tooltip.negative} negative</div>
            <div className="text-gray-500">~{tooltip.neutral} neutral</div>
          </div>
        </div>
      )}
    </div>
  );
}
