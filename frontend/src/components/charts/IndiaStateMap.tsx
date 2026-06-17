import { useState } from "react";
import { ComposableMap, Geographies, Geography, ZoomableGroup } from "react-simple-maps";
import type { StateStat } from "../../lib/types";

// Well-maintained public TopoJSON for India states.
// NAME_1 property matches official state names used in NLP extraction.
const GEO_URL =
  "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/india/india-states.json";

// NLP uses official names; TopoJSON NAME_1 may differ slightly — normalise both sides.
const NORMALISE = (s: string) =>
  s.toLowerCase()
   .replace(/&/g, "and")
   .replace(/jammu and kashmir/g, "jammu kashmir")
   .replace(/\s+/g, " ")
   .trim();

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

function sentimentColor(stat: StateStat | undefined): string {
  if (!stat || stat.count === 0) return "#1f2937"; // gray-800 — no data

  const positivePct = stat.positive / stat.count;
  const negativePct = stat.negative / stat.count;

  if (positivePct >= 0.6) return "#166534";   // strong positive — green-800
  if (positivePct >= 0.4) return "#15803d";   // positive — green-700
  if (negativePct >= 0.6) return "#991b1b";   // strong negative — red-800
  if (negativePct >= 0.4) return "#b91c1c";   // negative — red-700
  return "#374151";                           // mostly neutral — gray-700
}

export function IndiaStateMap({ data, onStateClick }: Props) {
  const [tooltip, setTooltip] = useState<Tooltip | null>(null);

  const statMap = new Map<string, StateStat>();
  for (const s of data) {
    statMap.set(NORMALISE(s.state), s);
  }

  return (
    <div className="relative bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-sm font-semibold text-gray-200 mb-1">State-level Sentiment</div>
      <p className="text-xs text-gray-500 mb-3">
        Hover a state to see breakdown · Click to filter mentions
      </p>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mb-3">
        {[
          { color: "#166534", label: "Strong positive" },
          { color: "#15803d", label: "Positive" },
          { color: "#374151", label: "Neutral" },
          { color: "#b91c1c", label: "Negative" },
          { color: "#991b1b", label: "Strong negative" },
          { color: "#1f2937", label: "No data" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm border border-gray-600" style={{ background: color }} />
            <span className="text-xs text-gray-500">{label}</span>
          </div>
        ))}
      </div>

      <div className="w-full" style={{ height: 420 }}>
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{ center: [82, 22], scale: 900 }}
          width={600}
          height={420}
          style={{ width: "100%", height: "100%" }}
        >
          <ZoomableGroup>
            <Geographies geography={GEO_URL}>
              {({ geographies }) =>
                geographies.map((geo) => {
                  const geoName: string = geo.properties.NAME_1 ?? "";
                  const stat = statMap.get(NORMALISE(geoName));
                  const fill = sentimentColor(stat);

                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={fill}
                      stroke="#374151"
                      strokeWidth={0.5}
                      style={{
                        default: { outline: "none", cursor: stat ? "pointer" : "default" },
                        hover:   { outline: "none", fill: "#6366f1", cursor: "pointer" },
                        pressed: { outline: "none" },
                      }}
                      onMouseEnter={(e) => {
                        setTooltip({
                          name: geoName,
                          total: stat?.count ?? 0,
                          positive: stat?.positive ?? 0,
                          negative: stat?.negative ?? 0,
                          neutral: stat?.neutral ?? 0,
                          x: e.clientX,
                          y: e.clientY,
                        });
                      }}
                      onMouseMove={(e) => {
                        setTooltip(prev => prev ? { ...prev, x: e.clientX, y: e.clientY } : prev);
                      }}
                      onMouseLeave={() => setTooltip(null)}
                      onClick={() => {
                        if (stat && onStateClick) onStateClick(geoName);
                      }}
                    />
                  );
                })
              }
            </Geographies>
          </ZoomableGroup>
        </ComposableMap>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-xl"
          style={{ left: tooltip.x + 12, top: tooltip.y - 10 }}
        >
          <div className="font-semibold text-gray-100 mb-1">{tooltip.name}</div>
          {tooltip.total > 0 ? (
            <div className="space-y-0.5 text-gray-400">
              <div>{tooltip.total} mention{tooltip.total !== 1 ? "s" : ""}</div>
              <div className="text-emerald-400">+{tooltip.positive} positive</div>
              <div className="text-red-400">−{tooltip.negative} negative</div>
              <div className="text-gray-500">~{tooltip.neutral} neutral</div>
            </div>
          ) : (
            <div className="text-gray-500">No mentions yet</div>
          )}
        </div>
      )}

      {data.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-xs text-gray-600 bg-gray-900/80 px-3 py-1.5 rounded-lg">
            State data will appear after the next pipeline run
          </p>
        </div>
      )}
    </div>
  );
}
