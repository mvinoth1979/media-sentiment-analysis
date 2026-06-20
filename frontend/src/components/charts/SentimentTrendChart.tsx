import { useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, Legend,
  ReferenceLine, Label, ResponsiveContainer,
} from "recharts";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAnnotations, createAnnotation, fetchSentimentTrend } from "../../lib/api";
import type { Annotation, SentimentTrendPoint } from "../../lib/types";
import { sentimentIntensity } from "../../lib/utils";

interface Props {
  brandId: string;
  dateFrom?: string;
  dateTo?: string;
}

interface ChartPoint {
  date: string;
  _iso: string;
  positive: number;
  negative: number;
  neutral: number;
  t1_positive?: number;
  t1_negative?: number;
  t1_neutral?: number;
}

function formatChartData(
  points: SentimentTrendPoint[],
  window_: "1d" | "1h",
  tier1Points?: SentimentTrendPoint[],
): ChartPoint[] {
  const t1Map = new Map((tier1Points ?? []).map(p => [p.time.slice(0, 10), p]));
  return points.map(p => {
    const iso = p.time.slice(0, 10);
    const t1 = t1Map.get(iso);
    return {
      date:
        window_ === "1d"
          ? new Date(p.time).toLocaleDateString("en-IN", { day: "numeric", month: "short" })
          : new Date(p.time).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      _iso: iso,
      positive: p.positive,
      negative: p.negative,
      neutral:  p.neutral,
      ...(t1 ? { t1_positive: t1.positive, t1_negative: t1.negative, t1_neutral: t1.neutral } : {}),
    };
  });
}

interface TooltipEntry { dataKey: string; value: number; }
interface CustomTooltipProps { active?: boolean; payload?: TooltipEntry[]; label?: string; }

function SentimentTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const pos = payload.find((p: TooltipEntry) => p.dataKey === "positive")?.value ?? 0;
  const neg = payload.find((p: TooltipEntry) => p.dataKey === "negative")?.value ?? 0;
  const neu = payload.find((p: TooltipEntry) => p.dataKey === "neutral")?.value ?? 0;
  const total = pos + neg + neu;
  const dominant =
    pos >= neg && pos >= neu ? "positive" :
    neg >= pos && neg >= neu ? "negative" : "neutral";
  const domScore = total > 0
    ? dominant === "positive" ? pos / total
    : dominant === "negative" ? 1 - (pos / total)
    : 0.5
    : 0.5;
  const { text } = sentimentIntensity(dominant, domScore);

  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs shadow-md">
      <div className="text-gray-500 mb-1">{label}</div>
      <div className="text-blue-600 text-[10px] mb-1.5 font-medium">{text}</div>
      <div className="text-indigo-600">+{pos} positive</div>
      <div className="text-red-500">−{neg} negative</div>
      <div className="text-amber-500">~{neu} neutral</div>
    </div>
  );
}

export function SentimentTrendChart({ brandId, dateFrom, dateTo }: Props) {
  const queryClient = useQueryClient();
  const [showForm,   setShowForm]   = useState(false);
  const [draftDate,  setDraftDate]  = useState("");
  const [draftLabel, setDraftLabel] = useState("");
  const [showTier1,  setShowTier1]  = useState(false);

  // ── Data ──────────────────────────────────────────────────────────────────
  const { data: trendData, isLoading } = useQuery({
    queryKey: ["sentiment-trend", brandId, dateFrom, dateTo],
    queryFn: () => fetchSentimentTrend(brandId, { date_from: dateFrom, date_to: dateTo, days: 30 }),
    staleTime: 5 * 60_000,
  });

  // F08 annotation queries — identical to v1.0, preserved exactly
  const { data: annotations = [] } = useQuery<Annotation[]>({
    queryKey: ["annotations", brandId],
    queryFn: () => fetchAnnotations(brandId),
    staleTime: 60_000,
  });

  const addAnnotation = useMutation({
    mutationFn: () => createAnnotation(brandId, draftDate, draftLabel.trim()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["annotations", brandId] });
      setDraftDate("");
      setDraftLabel("");
      setShowForm(false);
    },
  });

  // ── Chart data ────────────────────────────────────────────────────────────
  const window_ = trendData?.window ?? "1d";
  const chartData: ChartPoint[] = trendData
    ? formatChartData(trendData.points, window_, trendData.points_tier1)
    : [];
  const chartDates = new Set(chartData.map(p => p._iso));

  // Find formatted x-axis label matching annotation date (F08 preserved)
  function formattedDateOf(isoDate: string): string {
    return chartData.find(d => d._iso === isoDate)?.date ?? isoDate;
  }

  // ── Skeleton ──────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <div className="h-5 w-48 bg-gray-100 rounded animate-pulse mb-4" />
        <div className="h-[220px] bg-gray-50 rounded-lg animate-pulse" />
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">

      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-800">Sentiment Trend</div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowTier1(s => !s)}
            title="Overlay showing only Tier 1+2 national/major-regional sources"
            className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
              showTier1
                ? "bg-violet-50 border-violet-300 text-violet-600"
                : "border-gray-200 text-gray-400 hover:border-gray-300 hover:text-gray-600"
            }`}
          >
            Tier 1+2 only
          </button>
          <button
            onClick={() => setShowForm(s => !s)}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            {showForm ? "Cancel" : "+ Annotate"}
          </button>
        </div>
      </div>

      {/* F08 annotation form — identical to v1.0 */}
      {showForm && (
        <form
          onSubmit={e => { e.preventDefault(); if (draftDate && draftLabel.trim()) addAnnotation.mutate(); }}
          className="flex flex-wrap items-center gap-2 mb-3"
        >
          <input
            type="date"
            value={draftDate}
            onChange={e => setDraftDate(e.target.value)}
            required
            className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-1.5 focus:outline-none focus:border-blue-500"
          />
          <input
            type="text"
            value={draftLabel}
            onChange={e => setDraftLabel(e.target.value)}
            placeholder="What happened on this date?"
            required
            className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2.5 py-1.5 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 flex-1 min-w-[160px]"
          />
          <button
            type="submit"
            disabled={addAnnotation.isPending}
            className="text-xs px-3 py-1.5 bg-blue-600 rounded-lg text-white hover:bg-blue-500 disabled:opacity-50"
          >
            Save
          </button>
        </form>
      )}

      {chartData.length === 0 ? (
        <div className="h-[220px] flex items-center justify-center text-gray-400 text-sm">
          No trend data yet — the pipeline runs hourly.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData} margin={{ top: 5, right: 16, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="gradPos" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.45} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="gradNeg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="gradNeu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#f59e0b" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 11 }} />
            <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} allowDecimals={false} />
            <Tooltip content={<SentimentTooltip />} />
            <Legend iconSize={8} wrapperStyle={{ fontSize: 11, paddingTop: 8, color: "#6b7280" }} />

            {/* Area fills — all sources (indigo=positive, amber=neutral, red=negative) */}
            <Area type="monotone" dataKey="positive" stroke="#6366f1" strokeWidth={2} fill="url(#gradPos)" dot={false} name="Positive" />
            <Area type="monotone" dataKey="neutral"  stroke="#f59e0b" strokeWidth={2} fill="url(#gradNeu)" dot={false} name="Neutral"  />
            <Area type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2} fill="url(#gradNeg)" dot={false} name="Negative" />

            {/* Dashed Tier 1+2 overlay */}
            {showTier1 && (
              <>
                <Area type="monotone" dataKey="t1_positive" stroke="#6366f1" strokeWidth={1} strokeDasharray="4 2" fill="none" dot={false} legendType="none" connectNulls />
                <Area type="monotone" dataKey="t1_neutral"  stroke="#f59e0b" strokeWidth={1} strokeDasharray="4 2" fill="none" dot={false} legendType="none" connectNulls />
                <Area type="monotone" dataKey="t1_negative" stroke="#ef4444" strokeWidth={1} strokeDasharray="4 2" fill="none" dot={false} legendType="none" connectNulls />
              </>
            )}

            {/* F08 annotations — ReferenceLine per annotation, preserved exactly */}
            {annotations
              .filter(a => chartDates.has(a.date))
              .map(a => (
                <ReferenceLine key={a.id} x={formattedDateOf(a.date)} stroke="#f59e0b" strokeDasharray="3 3">
                  <Label value={a.label} position="insideTopLeft" fill="#d97706" fontSize={10} />
                </ReferenceLine>
              ))}
          </AreaChart>
        </ResponsiveContainer>
      )}

      {/* F08 annotation chips — preserved exactly */}
      {annotations.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {annotations.map(a => (
            <span
              key={a.id}
              className="text-[10px] text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5"
            >
              {new Date(a.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })} · {a.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
