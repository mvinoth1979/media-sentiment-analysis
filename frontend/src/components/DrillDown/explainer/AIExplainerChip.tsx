import { useState, useEffect, useRef } from "react";
import { supabase } from "../../../lib/supabase";
import { AIExplainerTooltip } from "./AIExplainerTooltip";

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
}

// Inline sparkle/brain SVG icon — lucide-react is not in this project
function SparkleIcon() {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 3l1.9 5.8L20 10l-6.1 1.2L12 21l-1.9-5.8L4 14l6.1-1.2z" />
    </svg>
  );
}

export function AIExplainerChip({ metric, brandId, value, days }: Props) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  // Close tooltip on click outside
  useEffect(() => {
    if (!open) return;

    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  async function handleClick() {
    if (open && data) { setOpen(false); return; }
    if (data) { setOpen(true); return; }

    setLoading(true);
    setError(false);

    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;

      const baseUrl = (import.meta.env.VITE_API_URL as string) ?? "";
      // brand_id must be a query param — require_brand_role reads it from FastAPI path/query params
      const url = `${baseUrl}/dashboard/explain?days=${days ?? 7}&brand_id=${encodeURIComponent(brandId)}`;

      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ metric, brand_id: brandId, value, context: {} }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const json: ExplainResponse = await res.json();
      setData(json);
      setOpen(true);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div ref={containerRef} className="relative inline-block">
      <button
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-blue-500/15 text-blue-300 hover:bg-blue-500/25 cursor-pointer transition-colors border border-blue-500/20 disabled:opacity-60 disabled:cursor-not-allowed"
        aria-label={`Explain ${metric}`}
      >
        {loading ? (
          <span
            className="animate-spin border-2 border-blue-400 border-t-transparent rounded-full w-3 h-3 flex-shrink-0"
            aria-hidden="true"
          />
        ) : error ? (
          <span className="text-red-400 font-bold leading-none" aria-label="Error">!</span>
        ) : (
          <SparkleIcon />
        )}
        {!loading && <span>{error ? "Retry" : "Explain"}</span>}
      </button>

      {open && data && (
        <AIExplainerTooltip
          data={data}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}
