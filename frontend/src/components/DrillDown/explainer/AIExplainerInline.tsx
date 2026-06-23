import { useState, useEffect } from "react";
import { useExplainer } from "../../../hooks/useExplainer";
import type { ExplainResponse } from "../../../hooks/useExplainer";

// ── Types ──────────────────────────────────────────────────────────────────────

interface Props {
  metric: string;
  brandId: string;
  value?: number;
  days?: number;
  autoLoad?: boolean;
  className?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

const CONFIDENCE_COLOR: Record<ExplainResponse["confidence"], string> = {
  high: "bg-emerald-400",
  medium: "bg-amber-400",
  low: "bg-red-400",
};

const CONFIDENCE_LABEL: Record<ExplainResponse["confidence"], string> = {
  high: "HIGH",
  medium: "MED",
  low: "LOW",
};

const CONFIDENCE_LABEL_COLOR: Record<ExplainResponse["confidence"], string> = {
  high: "text-emerald-400",
  medium: "text-amber-400",
  low: "text-red-400",
};

// ── Component ─────────────────────────────────────────────────────────────────

export function AIExplainerInline({
  metric,
  brandId,
  value,
  days = 7,
  autoLoad = false,
  className = "",
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const { explain, isLoading, data, error } = useExplainer({ brandId, days });

  // Auto-fetch on mount if requested
  useEffect(() => {
    if (autoLoad) {
      explain({ metric, value }).then(() => setExpanded(true)).catch(() => {});
    }
    // Only run on mount — intentionally empty dep array except autoLoad guard
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLoadClick = () => {
    if (data) {
      // Already fetched — just toggle
      setExpanded((prev) => !prev);
      return;
    }
    explain({ metric, value })
      .then(() => setExpanded(true))
      .catch(() => {});
  };

  const handleHeaderClick = () => {
    if (data) {
      setExpanded((prev) => !prev);
    }
  };

  // ── Collapsed (no data yet, not loading) ─────────────────────────────────
  const showCollapsed = !isLoading && !data && !error;
  const showLoading = isLoading;
  const showExpanded = !isLoading && !!data && expanded;
  const showError = !isLoading && !!error;

  return (
    <div
      className={`${className} bg-[#1a2744]/50 border border-white/8 rounded-xl overflow-hidden`}
    >
      {/* ── Header row ─────────────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-white/5"
        onClick={handleHeaderClick}
      >
        {/* Brain icon + label */}
        <div className="flex items-center gap-1.5 text-xs font-medium text-blue-300">
          <span aria-hidden="true">🧠</span>
          <span>AI Analysis{showCollapsed ? " available" : ""}</span>
        </div>

        {/* Right side control */}
        {showCollapsed && (
          <button
            className="text-[10px] text-white/40 hover:text-white/70 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              handleLoadClick();
            }}
          >
            Load explanation ▾
          </button>
        )}

        {showLoading && (
          <span className="text-[10px] text-white/40 flex items-center gap-1">
            <svg
              className="animate-spin w-3 h-3 text-blue-400"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Analyzing…
          </span>
        )}

        {showError && (
          <span className="text-[10px] text-red-400/70">Failed — retry?</span>
        )}

        {!isLoading && data && (
          <button
            className="text-[10px] text-white/40 hover:text-white/70 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded((prev) => !prev);
            }}
          >
            {expanded ? "▲ Hide" : "▾ Show"}
          </button>
        )}
      </div>

      {/* ── Error retry ────────────────────────────────────────────────────── */}
      {showError && (
        <div className="px-3 pb-2 border-t border-white/8">
          <p className="text-[10px] text-red-400/70 mt-2">{error}</p>
          <button
            className="mt-1 text-[10px] text-blue-400 hover:text-blue-300 underline-offset-2 hover:underline"
            onClick={handleLoadClick}
          >
            Try again
          </button>
        </div>
      )}

      {/* ── Expanded content ────────────────────────────────────────────────── */}
      {showExpanded && data && (
        <div className="px-3 pb-3 space-y-3 border-t border-white/8">
          {/* Headline */}
          <p className="text-sm text-white/90 pt-2 leading-snug">{data.headline}</p>

          {/* Confidence bar */}
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${CONFIDENCE_COLOR[data.confidence]}`}
                style={{ width: `${data.confidence_pct}%` }}
              />
            </div>
            <span className="text-[10px] text-white/50 tabular-nums w-7 text-right shrink-0">
              {data.confidence_pct}%
            </span>
            <span
              className={`text-[9px] font-bold tracking-wide px-1.5 py-0.5 rounded-full bg-white/8 shrink-0 ${CONFIDENCE_LABEL_COLOR[data.confidence]}`}
            >
              {CONFIDENCE_LABEL[data.confidence]}
            </span>
          </div>

          {/* Key drivers */}
          {data.drivers.length > 0 && (
            <div>
              <div className="text-[9px] text-white/40 uppercase tracking-wider font-medium mb-1.5">
                Key drivers
              </div>
              <div className="flex flex-wrap gap-1.5">
                {data.drivers.map((driver, i) => (
                  <span
                    key={i}
                    className="inline-flex text-[10px] bg-white/8 text-white/60 px-2 py-0.5 rounded-full"
                  >
                    {driver}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Suggested action */}
          {data.suggested_action && (
            <p className="text-xs text-emerald-300 flex items-start gap-1.5">
              <span className="shrink-0 mt-0.5">✅</span>
              <span>
                <span className="text-white/40">Action: </span>
                &ldquo;{data.suggested_action}&rdquo;
              </span>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
