import { useQuery } from "@tanstack/react-query";
import { fetchRiskForecast } from "../lib/api";
import { CrisisTimeline } from "./CrisisTimeline";
import { RiskForecastChart } from "./RiskForecastChart";

interface Props {
  brandId: string;
  days?: number;
}

function SlopeBadge({ slope }: { slope: number }) {
  if (slope > 0.5) {
    return (
      <span className="text-[9px] font-bold text-red-300 bg-red-500/15 border border-red-500/25 px-1.5 py-0.5 rounded-full">
        ▲ +{slope.toFixed(1)}/day
      </span>
    );
  }
  if (slope < -0.5) {
    return (
      <span className="text-[9px] font-bold text-emerald-300 bg-emerald-500/15 border border-emerald-500/25 px-1.5 py-0.5 rounded-full">
        ▼ {slope.toFixed(1)}/day
      </span>
    );
  }
  return (
    <span className="text-[9px] font-bold text-white/40 bg-white/5 border border-white/10 px-1.5 py-0.5 rounded-full">
      → Stable
    </span>
  );
}

function ConfidenceDots({ pct }: { pct: number }) {
  const filled = Math.round((pct / 100) * 5);
  return (
    <div className="flex gap-0.5 items-center" title={`${pct}% confidence`}>
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className={`w-1 h-1 rounded-full ${i < filled ? "bg-blue-400" : "bg-white/10"}`}
        />
      ))}
      <span className="text-[8px] text-white/25 ml-0.5">{pct}%</span>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-3 animate-pulse p-3">
      <div className="flex gap-2 items-center">
        <div className="h-4 w-24 bg-white/10 rounded" />
        <div className="h-4 w-16 bg-white/5 rounded" />
      </div>
      <div className="h-3 w-full bg-white/8 rounded" />
      <div className="h-3 w-4/5 bg-white/5 rounded" />
      <div className="h-16 w-full bg-white/5 rounded" />
      <div className="h-20 w-full bg-white/5 rounded" />
    </div>
  );
}

export function SituationRoomPanel({ brandId, days = 14 }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["risk-forecast", brandId, days],
    queryFn: () => fetchRiskForecast(brandId, days),
    staleTime: 15 * 60_000,
    retry: 1,
  });

  return (
    <div className="bg-[#111e36] border border-white/10 rounded-xl flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[11px] font-semibold text-white">Situation Room</span>
        {data && <SlopeBadge slope={data.slope} />}
        <div className="ml-auto">
          {data && <ConfidenceDots pct={data.confidence_pct} />}
        </div>
      </div>

      {isLoading ? (
        <Skeleton />
      ) : !data ? (
        <div className="flex items-center justify-center flex-1">
          <span className="text-[11px] text-white/25">No risk data available</span>
        </div>
      ) : (
        <div className="flex-1 min-h-0 overflow-y-auto px-3 py-2 space-y-3" style={{ scrollbarWidth: "none" }}>
          {/* AI Narrative */}
          <div className="bg-[#1a2744] border border-white/8 rounded-lg p-2.5">
            <div className="flex items-center gap-1 mb-1.5">
              <span className="text-[9px] font-semibold text-blue-400">🧠 AI Risk Copilot</span>
            </div>
            <p className="text-[10px] text-white/75 leading-relaxed">{data.narrative}</p>
          </div>

          {/* 7-day forecast points */}
          <div className="grid grid-cols-3 gap-1.5">
            {data.forecasts.map(f => (
              <div key={f.days_ahead} className="bg-[#1a2744] border border-white/8 rounded-lg p-2 text-center">
                <div className="text-[8px] text-white/30">+{f.days_ahead}d</div>
                <div
                  className={`text-[14px] font-bold mt-0.5 ${
                    f.predicted_risk >= 65 ? "text-red-400" :
                    f.predicted_risk >= 45 ? "text-orange-400" :
                    f.predicted_risk >= 25 ? "text-yellow-400" :
                    "text-emerald-400"
                  }`}
                >
                  {f.predicted_risk.toFixed(0)}
                </div>
                <div className="text-[7px] text-white/20 mt-0.5">
                  {f.lower.toFixed(0)}–{f.upper.toFixed(0)}
                </div>
              </div>
            ))}
          </div>

          {/* Risk Forecast Chart */}
          <RiskForecastChart historical={data.historical} forecasts={data.forecasts} />

          {/* Crisis Timeline */}
          <CrisisTimeline historical={data.historical} />
        </div>
      )}
    </div>
  );
}
