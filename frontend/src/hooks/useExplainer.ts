import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ExplainResponse {
  headline: string;
  drivers: string[];
  evidence: string[];
  confidence: "high" | "medium" | "low";
  confidence_pct: number;
  suggested_action: string;
  drill_tab: "A" | "B" | "C";
}

interface ExplainRequest {
  metric: string;
  brand_id: string;
  value?: number;
  context?: Record<string, unknown>;
}

interface CacheEntry {
  data: ExplainResponse;
  ts: number;
}

const CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes

// ── Public interfaces ─────────────────────────────────────────────────────────

export interface UseExplainerOptions {
  brandId: string;
  days?: number;
}

export interface ExplainParams {
  metric: string;
  value?: number;
  context?: Record<string, unknown>;
}

export interface UseExplainerReturn {
  explain: (params: ExplainParams) => Promise<ExplainResponse>;
  isLoading: boolean;
  data: ExplainResponse | null;
  error: string | null;
  reset: () => void;
}

// ── Hook ───────────────────────────────────────────────────────────────────────

export function useExplainer({ brandId, days = 7 }: UseExplainerOptions): UseExplainerReturn {
  const cache = useRef<Map<string, CacheEntry>>(new Map());
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation<ExplainResponse, Error, ExplainParams>({
    mutationFn: async (params: ExplainParams): Promise<ExplainResponse> => {
      const cacheKey = `${brandId}:${params.metric}:${days}:${JSON.stringify(params.context ?? {})}`;

      // Check in-memory cache first
      const cached = cache.current.get(cacheKey);
      if (cached && Date.now() - cached.ts < CACHE_TTL_MS) {
        return cached.data;
      }

      const baseUrl = import.meta.env.VITE_API_URL ?? "";
      const token = localStorage.getItem("access_token");

      const body: ExplainRequest = {
        metric: params.metric,
        brand_id: brandId,
        ...(params.value !== undefined && { value: params.value }),
        ...(params.context && { context: params.context }),
      };

      const response = await fetch(`${baseUrl}/dashboard/explain?days=${days}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const json = await response.json();
          detail = json.detail ?? detail;
        } catch {
          // ignore parse errors — keep the status-based message
        }
        throw new Error(detail);
      }

      const result: ExplainResponse = await response.json();

      // Store in cache with timestamp
      cache.current.set(cacheKey, { data: result, ts: Date.now() });

      return result;
    },
    onSuccess: (result) => {
      setData(result);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message ?? "Unknown error");
    },
  });

  const explain = async (params: ExplainParams): Promise<ExplainResponse> => {
    setError(null);
    return mutation.mutateAsync(params);
  };

  const reset = () => {
    mutation.reset();
    setData(null);
    setError(null);
  };

  return {
    explain,
    isLoading: mutation.isPending,
    data,
    error,
    reset,
  };
}
