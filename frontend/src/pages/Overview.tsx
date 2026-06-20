import { useRef, useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchOverview, fetchAlerts, createAlert, deleteAlert } from "../lib/api";
import type { AlertConfig } from "../lib/types";
import { KPICard } from "../components/cards/KPICard";
import { SentimentTrendChart } from "../components/charts/SentimentTrendChart";
import { MentionsBySourceDonut } from "../components/charts/MentionsBySourceDonut";
import { MentionsList } from "../components/mentions/MentionsList";
import { TopHeadlines } from "../components/TopHeadlines";
import { SentimentBySourceTable } from "../components/SentimentBySourceTable";
import { TopIssuesTable } from "../components/TopIssuesTable";
import { ReviewSitesSummary } from "../components/ReviewSitesSummary";
import { CompetitorShareOfVoice } from "../components/CompetitorShareOfVoice";
import { IndiaStateMap } from "../components/charts/IndiaStateMap";
import { formatCount } from "../lib/utils";

type ActivePanel =
  | null
  | "mentions" | "mentions-positive" | "mentions-negative" | "mentions-neutral"
  | "sentiment-trend" | "mentions-donut" | "top-headlines"
  | "review-sites" | "top-issues" | "sentiment-by-source"
  | "competitor-sov" | "alerts" | "state-map";

const PANEL_TITLE: Record<NonNullable<ActivePanel>, string> = {
  "mentions":           "All Mentions",
  "mentions-positive":  "Positive Mentions",
  "mentions-negative":  "Negative Mentions",
  "mentions-neutral":   "Neutral Mentions",
  "sentiment-trend":    "Sentiment Trend",
  "mentions-donut":     "Mentions by Source",
  "top-headlines":      "Top Headlines",
  "review-sites":       "Review Sites Summary",
  "top-issues":         "Top Issues",
  "sentiment-by-source":"Sentiment by Source",
  "competitor-sov":     "Competitor Share of Voice",
  "alerts":             "Alerts & Risks",
  "state-map":          "State-level Sentiment",
};

interface Props {
  brandId: string;
  brandName?: string;
  isAdmin?: boolean;
  userEmail?: string;
  onLastUpdated?: (iso: string | null) => void;
}

const ALERT_TYPE_LABELS: Record<string, string> = {
  perception_score_below: "Perception score below",
  negative_pct_above:     "Negative % above",
  mention_spike:          "Mention spike above",
};

function formatLastProcessed(iso: string | null): string {
  if (!iso) return "—";
  const minutes = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function AlertsSection({ brandId, userEmail }: { brandId: string; userEmail?: string }) {
  const [alertType, setAlertType]     = useState("perception_score_below");
  const [threshold, setThreshold]     = useState("");
  const [notifyEmail, setNotifyEmail] = useState(userEmail ?? "");
  const [formError, setFormError]     = useState("");
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: () => createAlert(brandId, {
      alert_type: alertType,
      threshold: parseFloat(threshold),
      notify_email: notifyEmail,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts", brandId] });
      setThreshold("");
      setFormError("");
    },
    onError: (e: Error) => setFormError(e.message),
  });

  const canSubmit = threshold !== "" && !isNaN(parseFloat(threshold)) && notifyEmail.includes("@");

  return (
    <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
      <div className="text-xs font-semibold text-gray-600">Configure New Alert</div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <select
          value={alertType}
          onChange={e => setAlertType(e.target.value)}
          className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-2 focus:outline-none focus:border-blue-500"
        >
          {Object.entries(ALERT_TYPE_LABELS).map(([v, l]) => (
            <option key={v} value={v}>{l}</option>
          ))}
        </select>
        <input
          type="number"
          value={threshold}
          onChange={e => setThreshold(e.target.value)}
          placeholder="e.g. 40"
          className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-2 focus:outline-none focus:border-blue-500 placeholder:text-gray-400"
        />
        <input
          type="email"
          value={notifyEmail}
          onChange={e => setNotifyEmail(e.target.value)}
          placeholder="notify@email.com"
          className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-2 focus:outline-none focus:border-blue-500 placeholder:text-gray-400"
        />
      </div>
      {formError && <p className="text-xs text-red-500">{formError}</p>}
      <button
        onClick={() => createMutation.mutate()}
        disabled={!canSubmit || createMutation.isPending}
        className="text-xs px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg disabled:opacity-40 transition-colors"
      >
        {createMutation.isPending ? "Adding…" : "+ Add Alert"}
      </button>
      <p className="text-[10px] text-gray-400">
        Alerts fire once per 4 hours via Resend email. Requires RESEND_API_KEY in Railway.
      </p>
    </div>
  );
}

function AlertsRiskCards({
  brandId, isAdmin, userEmail, compact,
}: {
  brandId: string; isAdmin: boolean; userEmail?: string; compact?: boolean;
}) {
  const queryClient = useQueryClient();
  const { data: alerts = [] } = useQuery<AlertConfig[]>({
    queryKey: ["alerts", brandId],
    queryFn: () => fetchAlerts(brandId),
    staleTime: 60_000,
  });
  const deleteMutation = useMutation({
    mutationFn: (alertId: string) => deleteAlert(brandId, alertId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts", brandId] }),
  });

  const RISK_BORDER: Record<string, string> = {
    perception_score_below: "border-l-red-500",
    negative_pct_above:     "border-l-amber-500",
    mention_spike:          "border-l-orange-400",
  };
  const RISK_BG: Record<string, string> = {
    perception_score_below: "bg-red-50",
    negative_pct_above:     "bg-amber-50",
    mention_spike:          "bg-orange-50",
  };
  const RISK_BADGE: Record<string, { label: string; color: string }> = {
    perception_score_below: { label: "High Risk",   color: "text-red-600 bg-red-100"    },
    negative_pct_above:     { label: "Medium Risk", color: "text-amber-600 bg-amber-100" },
    mention_spike:          { label: "Medium Risk", color: "text-orange-600 bg-orange-100" },
  };

  const inner = alerts.length === 0 ? (
    <div className="text-[10px] text-gray-400 text-center py-2">
      No active alerts.{isAdmin ? "" : " Ask an admin."}
    </div>
  ) : (
    <div className={`grid ${compact ? "grid-cols-2" : "grid-cols-1 sm:grid-cols-2"} gap-2`}>
      {alerts.map(a => {
        const badge = RISK_BADGE[a.alert_type] ?? { label: "Alert", color: "text-gray-600 bg-gray-100" };
        return (
          <div
            key={a.id}
            className={`relative border border-l-4 border-gray-100 rounded-lg px-2 py-2 ${RISK_BORDER[a.alert_type] ?? "border-l-gray-400"} ${RISK_BG[a.alert_type] ?? "bg-gray-50"}`}
          >
            <button
              onClick={e => { e.stopPropagation(); deleteMutation.mutate(a.id); }}
              className="absolute top-1 right-1.5 text-gray-300 hover:text-red-400 text-sm leading-none"
            >×</button>
            <span className={`inline-block text-[8px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full mb-1 ${badge.color}`}>
              {badge.label}
            </span>
            <div className="text-[10px] text-gray-700">
              {ALERT_TYPE_LABELS[a.alert_type]}: <span className="font-semibold">{a.threshold}</span>
            </div>
          </div>
        );
      })}
    </div>
  );

  if (compact) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-2 shadow-sm h-full flex flex-col overflow-hidden">
        <div className="text-[11px] font-semibold text-gray-800 mb-1 flex-none">Alerts & Risks</div>
        <div className="flex-1 min-h-0 overflow-hidden">{inner}</div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-800">Alerts & Risks</div>
      </div>
      {inner}
      {isAdmin && <AlertsSection brandId={brandId} userEmail={userEmail} />}
    </div>
  );
}

export function Overview({ brandId, brandName, isAdmin, userEmail, onLastUpdated }: Props) {
  const [activePanel, setActivePanel] = useState<ActivePanel>(null);
  const mentionsRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["overview", brandId],
    queryFn: () => fetchOverview(brandId),
    refetchInterval: (query) =>
      query.state.data?.pipeline_status === "running" ? 10_000 : 60_000,
  });

  useEffect(() => {
    if (data?.last_processed_at !== undefined) {
      onLastUpdated?.(data.last_processed_at);
    }
  }, [data?.last_processed_at, onLastUpdated]);

  // Reset panel when brand changes
  useEffect(() => { setActivePanel(null); }, [brandId]);

  if (isLoading) return (
    <div className="flex items-center justify-center h-full text-gray-400 text-sm">Loading…</div>
  );
  if (error || !data || !data.kpi) return (
    <div className="text-red-500 p-8 text-sm">Failed to load dashboard. No data yet — the pipeline runs hourly.</div>
  );

  const { kpi } = data;

  // ── Detail panel view ───────────────────────────────────────────────────────
  if (activePanel !== null) {
    const sentimentFilter =
      activePanel === "mentions-positive" ? "positive" :
      activePanel === "mentions-negative" ? "negative" :
      activePanel === "mentions-neutral"  ? "neutral"  : "";

    return (
      <div className="h-full flex flex-col overflow-hidden bg-gray-50">
        {/* Back bar */}
        <div className="flex items-center gap-3 px-4 py-2 bg-white border-b border-gray-200 flex-none">
          <button
            onClick={() => setActivePanel(null)}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-900 transition-colors font-medium"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Executive Overview
          </button>
          <span className="text-gray-200">|</span>
          <h2 className="text-xs font-semibold text-gray-800">{PANEL_TITLE[activePanel]}</h2>
        </div>

        {/* Detail content */}
        <div className="flex-1 min-h-0 overflow-auto p-4">
          {(activePanel === "mentions" || activePanel === "mentions-positive" || activePanel === "mentions-negative" || activePanel === "mentions-neutral") && (
            <div ref={mentionsRef}>
              <MentionsList
                brandId={brandId}
                brandName={brandName}
                portals={data.top_sources.map(s => s.portal_id)}
                topics={data.top_topics}
                states={data.state_breakdown.map(s => s.state)}
                initialSentiment={sentimentFilter}
                selectable
                syncUrl
              />
            </div>
          )}
          {activePanel === "sentiment-trend" && (
            <SentimentTrendChart brandId={brandId} />
          )}
          {activePanel === "mentions-donut" && (
            <div className="max-w-lg">
              <MentionsBySourceDonut brandId={brandId} />
            </div>
          )}
          {activePanel === "top-headlines" && (
            <div className="max-w-2xl">
              <TopHeadlines brandId={brandId} onViewAll={() => setActivePanel("mentions")} />
            </div>
          )}
          {activePanel === "review-sites" && (
            <div className="max-w-lg">
              <ReviewSitesSummary brandId={brandId} />
            </div>
          )}
          {activePanel === "top-issues" && (
            <div className="max-w-lg">
              <TopIssuesTable brandId={brandId} />
            </div>
          )}
          {activePanel === "sentiment-by-source" && (
            <div className="max-w-lg">
              <SentimentBySourceTable brandId={brandId} />
            </div>
          )}
          {activePanel === "competitor-sov" && (
            <div className="max-w-md">
              <CompetitorShareOfVoice brandName={brandName} />
            </div>
          )}
          {activePanel === "alerts" && (
            <div className="max-w-2xl">
              <AlertsRiskCards brandId={brandId} isAdmin={!!isAdmin} userEmail={userEmail} />
            </div>
          )}
          {activePanel === "state-map" && (
            <IndiaStateMap
              data={data.state_breakdown}
              onStateClick={(state) => {
                const url = new URL(window.location.href);
                url.searchParams.set("state", state);
                window.history.pushState({}, "", url.toString());
                window.dispatchEvent(new PopStateEvent("popstate"));
                setActivePanel("mentions");
              }}
            />
          )}
        </div>
      </div>
    );
  }

  // ── Compact single-screen overview ──────────────────────────────────────────
  return (
    <div className="h-full flex flex-col overflow-hidden bg-gray-50 p-2 gap-1.5">

      {/* ── Page header ─────────────────────────────────────────── flex-none */}
      <div className="flex items-center justify-between flex-none">
        <div>
          <h1 className="text-sm font-bold text-gray-900 leading-tight">Executive Overview</h1>
          <p className="text-[10px] text-gray-500">
            Real-time brand sentiment across digital and news ecosystem
            {data.last_processed_at && ` · Updated ${formatLastProcessed(data.last_processed_at)}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {data.pipeline_status === "running" && (
            <span className="flex items-center gap-1 text-[10px] text-blue-600 bg-blue-50 border border-blue-200 rounded-full px-2 py-0.5">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500" />
              </span>
              Pipeline running
            </span>
          )}
          <button
            onClick={() => setActivePanel("state-map")}
            className="text-[10px] text-gray-400 hover:text-gray-700 border border-gray-200 rounded px-2 py-0.5 hover:border-gray-300 transition-colors"
          >
            State Map
          </button>
          <button
            onClick={() => setActivePanel("mentions")}
            className="text-[10px] text-blue-600 hover:text-blue-700 border border-blue-200 rounded px-2 py-0.5 hover:border-blue-300 transition-colors"
          >
            All Mentions
          </button>
        </div>
      </div>

      {/* ── Row 1: KPI cards ────────────────────────────────────── flex-none */}
      <div className="grid grid-cols-5 gap-1.5 flex-none" style={{ height: "58px" }}>
        <KPICard compact label="Total Mentions"    value={formatCount(kpi.total)}       delta={kpi.mentions_delta_pct}   deltaUnit="%" sub="vs last period" icon="📰" accentColor="blue"   onClick={() => setActivePanel("mentions")} />
        <KPICard compact label="Positive Mentions" value={formatCount(kpi.positive)}    pct={kpi.positive_pct}                                                       icon="😊" accentColor="green"  onClick={() => setActivePanel("mentions-positive")} />
        <KPICard compact label="Neutral Mentions"  value={formatCount(kpi.neutral)}     pct={kpi.neutral_pct}                                                        icon="😐" accentColor="gray"   onClick={() => setActivePanel("mentions-neutral")} />
        <KPICard compact label="Negative Mentions" value={formatCount(kpi.negative)}    pct={kpi.negative_pct}                                                       icon="😟" accentColor="red"    onClick={() => setActivePanel("mentions-negative")} />
        <KPICard compact label="Reputation Index"  value={`${kpi.perception_score.toFixed(0)} / 100`} delta={kpi.perception_score_delta} deltaUnit=" pts"          icon="📊" accentColor="purple" onClick={() => setActivePanel("alerts")} />
      </div>

      {/* ── Row 2: Sentiment Trend | Donut | Headlines ──────────── flex-[3] */}
      <div className="grid grid-cols-12 gap-1.5 flex-[3] min-h-0">
        <div className="col-span-5 min-h-0">
          <SentimentTrendChart brandId={brandId} compact onClick={() => setActivePanel("sentiment-trend")} />
        </div>
        <div className="col-span-3 min-h-0">
          <MentionsBySourceDonut brandId={brandId} compact onClick={() => setActivePanel("mentions-donut")} />
        </div>
        <div className="col-span-4 min-h-0">
          <TopHeadlines brandId={brandId} compact onClick={() => setActivePanel("top-headlines")} />
        </div>
      </div>

      {/* ── Row 3: Review Sites | Top Issues | Sentiment by Source ─ flex-[3] */}
      <div className="grid grid-cols-3 gap-1.5 flex-[3] min-h-0">
        <div className="min-h-0">
          <ReviewSitesSummary brandId={brandId} compact onClick={() => setActivePanel("review-sites")} />
        </div>
        <div className="min-h-0">
          <TopIssuesTable brandId={brandId} compact onClick={() => setActivePanel("top-issues")} />
        </div>
        <div className="min-h-0">
          <SentimentBySourceTable brandId={brandId} compact onClick={() => setActivePanel("sentiment-by-source")} />
        </div>
      </div>

      {/* ── Row 4: Competitor SoV | Alerts ──────────────────────── flex-[2] */}
      <div className="grid grid-cols-3 gap-1.5 flex-[2] min-h-0">
        <div className="min-h-0">
          <CompetitorShareOfVoice brandName={brandName} compact onClick={() => setActivePanel("competitor-sov")} />
        </div>
        <div className="col-span-2 min-h-0 cursor-pointer" onClick={() => setActivePanel("alerts")}>
          <AlertsRiskCards brandId={brandId} isAdmin={!!isAdmin} userEmail={userEmail} compact />
        </div>
      </div>

    </div>
  );
}
