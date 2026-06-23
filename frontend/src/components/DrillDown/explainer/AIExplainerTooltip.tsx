
interface ExplainResponse {
  headline: string;
  drivers: string[];
  evidence: string[];
  confidence: "high" | "medium" | "low";
  confidence_pct: number;
  suggested_action: string;
  drill_tab: "A" | "B" | "C";
}

interface Props {
  data: ExplainResponse;
  onClose: () => void;
  onDrillTab?: (tab: string) => void;
}

const CONFIDENCE_BADGE: Record<ExplainResponse["confidence"], string> = {
  high: "bg-green-500/20 text-green-300",
  medium: "bg-yellow-500/20 text-yellow-300",
  low: "bg-red-500/20 text-red-300",
};

export function AIExplainerTooltip({ data, onClose, onDrillTab }: Props) {
  const badgeClass = CONFIDENCE_BADGE[data.confidence] ?? CONFIDENCE_BADGE.medium;
  const pct = Math.max(0, Math.min(100, data.confidence_pct));

  return (
    <div
      className="absolute z-50 mt-1 w-72 bg-[#0d1626] border border-white/10 rounded-xl p-3 shadow-xl"
      role="dialog"
      aria-modal="false"
      aria-label="AI Explanation"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-start gap-1.5 min-w-0">
          <span className="text-sm flex-shrink-0" aria-hidden="true">🧠</span>
          <p className="text-[11px] font-semibold text-white/90 leading-snug">{data.headline}</p>
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 text-white/40 hover:text-white/70 transition-colors text-xs leading-none p-0.5"
          aria-label="Close explanation"
        >
          ✕
        </button>
      </div>

      {/* Confidence bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-white/50">Confidence</span>
          <span
            className={`text-[9px] font-medium px-1.5 py-0.5 rounded-full ${badgeClass}`}
          >
            {data.confidence}
          </span>
        </div>
        <div className="relative h-1 rounded-full bg-blue-500/30 overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 h-1 rounded-full bg-blue-400 transition-all duration-500"
            style={{ width: `${pct}%` }}
            aria-valuenow={pct}
            aria-valuemin={0}
            aria-valuemax={100}
            role="progressbar"
          />
        </div>
        <span className="text-[9px] text-white/40 mt-0.5 block">{pct}%</span>
      </div>

      {/* Drivers */}
      {data.drivers.length > 0 && (
        <div className="mb-2">
          <p className="text-[10px] font-semibold text-white/60 uppercase tracking-wide mb-1">
            Why this happened
          </p>
          <ul className="space-y-0.5">
            {data.drivers.map((driver, i) => (
              <li key={i} className="flex items-start gap-1 text-[11px] text-white/70">
                <span className="flex-shrink-0 text-blue-400/70 mt-px">•</span>
                <span>{driver}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Evidence */}
      {data.evidence.length > 0 && (
        <div className="mb-2">
          <p className="text-[10px] font-semibold text-white/60 uppercase tracking-wide mb-1">
            Evidence
          </p>
          <ul className="space-y-0.5">
            {data.evidence.map((item, i) => (
              <li key={i} className="flex items-start gap-1 text-[10px] text-white/50 italic">
                <span className="flex-shrink-0 text-white/30 mt-px">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggested action */}
      <div className="mb-2.5 flex items-start gap-1">
        <span className="flex-shrink-0 text-xs" aria-hidden="true">✅</span>
        <p className="text-[11px] text-emerald-300 font-medium leading-snug">
          <span className="text-white/40 font-normal">Suggested action: </span>
          {data.suggested_action}
        </p>
      </div>

      {/* Drill tab button */}
      <div className="flex justify-end">
        <button
          onClick={() => onDrillTab?.(data.drill_tab)}
          className="text-[10px] px-2 py-1 rounded-lg bg-blue-600/30 text-blue-300 hover:bg-blue-600/50 transition-colors"
        >
          View in Tab {data.drill_tab} →
        </button>
      </div>
    </div>
  );
}
