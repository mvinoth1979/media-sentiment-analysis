import { useState, useEffect, useCallback } from "react";

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
  metric: string;
  brandId: string;
  value?: number;
  days?: number;
  open: boolean;
  onClose: () => void;
}

const CONFIDENCE_COLORS: Record<ExplainResponse["confidence"], string> = {
  high: "bg-emerald-400",
  medium: "bg-amber-400",
  low: "bg-red-400",
};

const CONFIDENCE_BADGE: Record<ExplainResponse["confidence"], string> = {
  high: "bg-emerald-500/20 text-emerald-300",
  medium: "bg-amber-500/20 text-amber-300",
  low: "bg-red-500/20 text-red-300",
};

const NUMBERED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"];

function DrawerSkeleton() {
  return (
    <div className="flex flex-col gap-5 animate-pulse px-4 py-4">
      <div className="space-y-2">
        <div className="h-2 w-16 bg-white/10 rounded" />
        <div className="h-4 w-full bg-white/10 rounded" />
        <div className="h-4 w-4/5 bg-white/10 rounded" />
      </div>
      <div className="space-y-2">
        <div className="h-2 w-20 bg-white/10 rounded" />
        <div className="h-2 w-full bg-white/10 rounded" />
      </div>
      <div className="space-y-2">
        <div className="h-2 w-24 bg-white/10 rounded" />
        <div className="h-3 w-full bg-white/10 rounded" />
        <div className="h-3 w-full bg-white/10 rounded" />
        <div className="h-3 w-3/4 bg-white/10 rounded" />
      </div>
    </div>
  );
}

export function AIExplainerDrawer({ metric, brandId, value, days, open, onClose }: Props) {
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchExplanation = useCallback(async () => {
    setLoading(true);
    setError(null);
    setData(null);
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
          metric,
          brand_id: brandId,
          ...(value !== undefined ? { value } : {}),
          context: {},
        }),
      });
      if (!resp.ok) {
        const msg = await resp.text().catch(() => `HTTP ${resp.status}`);
        throw new Error(msg || `HTTP ${resp.status}`);
      }
      const json: ExplainResponse = await resp.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load explanation.");
    } finally {
      setLoading(false);
    }
  }, [metric, brandId, value, days]);

  useEffect(() => {
    if (open) {
      fetchExplanation();
    } else {
      // Reset when closed so next open starts fresh
      setData(null);
      setError(null);
      setCopied(false);
    }
  }, [open, fetchExplanation]);

  const handleCopy = async () => {
    if (!data) return;
    const summary = [
      `Metric: ${metric}`,
      `Headline: ${data.headline}`,
      `Confidence: ${data.confidence.toUpperCase()} (${data.confidence_pct}%)`,
      "",
      "Why This Happened:",
      ...data.drivers.map((d, i) => `  ${i + 1}. ${d}`),
      "",
      "Evidence:",
      ...data.evidence.map(e => `  • ${e}`),
      "",
      `Recommended Action: ${data.suggested_action}`,
    ].join("\n");
    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard errors silently
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <div
        className={`fixed right-0 top-0 h-full w-[400px] bg-[#0d1626] border-l border-white/10 z-50 flex flex-col transition-transform duration-300 ${open ? "translate-x-0" : "translate-x-full"}`}
        role="dialog"
        aria-modal="true"
        aria-label={`AI Explainer: ${metric}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-none">
          <div className="flex items-center gap-2">
            <span className="text-base" aria-hidden="true">✨</span>
            <span className="text-sm font-semibold text-white/85">AI Explainer</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-white/40 font-medium truncate max-w-[140px]">{metric}</span>
            <button
              onClick={onClose}
              className="text-white/30 hover:text-white/70 transition-colors text-lg leading-none"
              aria-label="Close drawer"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {loading && <DrawerSkeleton />}

          {error && !loading && (
            <div className="px-4 py-6 flex flex-col items-start gap-3">
              <p className="text-sm text-red-400">{error}</p>
              <button
                onClick={fetchExplanation}
                className="text-xs px-3 py-1.5 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {data && !loading && (
            <div className="px-4 py-4 space-y-5">

              {/* Headline */}
              <section>
                <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-1.5">Headline</div>
                <p className="text-sm font-semibold text-white leading-snug">{data.headline}</p>
              </section>

              {/* Confidence */}
              <section>
                <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-2">Confidence</div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${CONFIDENCE_COLORS[data.confidence]}`}
                      style={{ width: `${data.confidence_pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-white/60 tabular-nums w-8 text-right">{data.confidence_pct}%</span>
                  <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full ${CONFIDENCE_BADGE[data.confidence]}`}>
                    {data.confidence}
                  </span>
                </div>
              </section>

              {/* Why This Happened */}
              <section>
                <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-2">Why This Happened</div>
                <ol className="space-y-1.5">
                  {data.drivers.map((driver, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-white/80">
                      <span className="shrink-0 text-white/40">{NUMBERED[i] ?? `${i + 1}.`}</span>
                      <span>{driver}</span>
                    </li>
                  ))}
                </ol>
              </section>

              {/* Evidence */}
              {data.evidence.length > 0 && (
                <section>
                  <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-2">Evidence</div>
                  <ul className="space-y-1.5">
                    {data.evidence.map((item, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-white/50 italic">
                        <span className="shrink-0 text-white/30 not-italic">▸</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Recommended Action */}
              <section>
                <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-2">Recommended Action</div>
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-sm text-emerald-300 flex items-start gap-2">
                  <span className="shrink-0 mt-0.5">✅</span>
                  <span>{data.suggested_action}</span>
                </div>
              </section>

            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-white/10 flex gap-2 flex-none">
          {data && (
            <button
              onClick={() => {
                // Surface the suggested drill tab to parent via onClose with context
                // — parent may read data.drill_tab if needed; for now just close
                onClose();
              }}
              className="flex-1 text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-colors text-center"
            >
              View Tab {data.drill_tab} →
            </button>
          )}
          <button
            onClick={handleCopy}
            disabled={!data}
            className="flex-1 text-xs px-3 py-1.5 bg-white/5 text-white/60 border border-white/10 rounded-lg hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-center"
          >
            {copied ? "Copied!" : "Copy Summary"}
          </button>
          <button
            onClick={onClose}
            className="flex-1 text-xs px-3 py-1.5 bg-white/5 text-white/50 border border-white/10 rounded-lg hover:bg-white/10 transition-colors text-center"
          >
            Close
          </button>
        </div>
      </div>
    </>
  );
}
