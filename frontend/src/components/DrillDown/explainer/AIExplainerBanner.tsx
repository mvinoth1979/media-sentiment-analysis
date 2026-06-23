import { useState, useEffect } from "react";

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
  brandId: string;
  perceptionScoreDelta: number | null | undefined;
  days?: number;
  onOpenDrawer?: (metric: string) => void;
}

export function AIExplainerBanner({ brandId, perceptionScoreDelta, days, onOpenDrawer }: Props) {
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const shouldFire =
    perceptionScoreDelta !== null &&
    perceptionScoreDelta !== undefined &&
    perceptionScoreDelta < -10;

  useEffect(() => {
    if (!shouldFire || dismissed) return;

    let cancelled = false;
    setLoading(true);

    const run = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const qs = `?days=${days ?? 7}`;
        const resp = await fetch(`${baseUrl}/dashboard/explain${qs}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            metric: "reputation_score",
            brand_id: brandId,
            value: perceptionScoreDelta,
            context: {},
          }),
        });
        if (!resp.ok) return; // silently fail
        const json: ExplainResponse = await resp.json();
        if (!cancelled) setData(json);
      } catch {
        // silently fail — do not render banner on error
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    run();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldFire, brandId, days]);

  // Do not render if condition not met
  if (!shouldFire) return null;

  // Do not render if dismissed
  if (dismissed) return null;

  // Loading state: show pulsing skeleton
  if (loading) {
    return (
      <div className="w-full bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 mb-4 animate-pulse">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-red-500/20 shrink-0" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3 w-48 bg-red-500/15 rounded" />
            <div className="h-2.5 w-72 bg-white/8 rounded" />
          </div>
        </div>
      </div>
    );
  }

  // Error / no data: do not render banner
  if (!data) return null;

  const deltaLabel = Math.abs(Math.round(perceptionScoreDelta as number));

  return (
    <div className="w-full bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 flex items-start gap-3 mb-4">
      {/* Left icon */}
      <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
        <span className="text-sm" aria-hidden="true">⚠️</span>
      </div>

      {/* Body */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-red-300">AI Alert</span>
          <span className="text-xs text-white/50">
            Reputation dropped {deltaLabel}pts
          </span>
          <span className="text-xs text-white/70 font-medium truncate">{data.headline}</span>
        </div>
        <p className="text-xs text-white/60 mt-0.5 leading-snug">
          {data.confidence_pct}% confidence · Suggested: &ldquo;{data.suggested_action}&rdquo;
        </p>
        {onOpenDrawer && (
          <button
            onClick={() => onOpenDrawer("reputation_score")}
            className="mt-1 text-xs px-3 py-1 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-colors"
          >
            Investigate →
          </button>
        )}
      </div>

      {/* Dismiss button */}
      <button
        onClick={() => setDismissed(true)}
        className="ml-auto text-white/30 hover:text-white/60 transition-colors text-base leading-none flex-shrink-0 mt-0.5"
        aria-label="Dismiss alert"
      >
        ✕
      </button>
    </div>
  );
}
