import { useRef, useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchOverview, fetchAlerts, createAlert, deleteAlert, fetchDivergenceSummary } from "../lib/api";
import type { AlertConfig, DivergenceSummaryData } from "../lib/types";
import { KPICard } from "../components/cards/KPICard";
import { SentimentTrendChart } from "../components/charts/SentimentTrendChart";
import { MentionsBySourceDonut } from "../components/charts/MentionsBySourceDonut";
import { MentionsList } from "../components/mentions/MentionsList";
import { TopHeadlines } from "../components/TopHeadlines";
import { SentimentBySourceTable } from "../components/SentimentBySourceTable";
import { TopIssuesTable } from "../components/TopIssuesTable";
import { ReviewSitesSummary } from "../components/ReviewSitesSummary";
import { CompetitorShareOfVoice } from "../components/CompetitorShareOfVoice";
import { EditorialToneChart } from "../components/EditorialToneChart";
import { YouTubeSentimentSplit } from "../components/YouTubeSentimentSplit";
import { IndiaStateMap } from "../components/charts/IndiaStateMap";
import { formatCount } from "../lib/utils";

type ActivePanel =
  | null
  | "mentions" | "mentions-positive" | "mentions-negative" | "mentions-neutral"
  | "sentiment-trend" | "mentions-donut" | "top-headlines"
  | "review-sites" | "top-issues" | "sentiment-by-source"
  | "competitor-sov" | "alerts" | "state-map"
  | "mentions-drill";

interface DrillFilter {
  label: string;
  topic?: string;
  sourceCategory?: string;
  issueCategory?: string;
  q?: string;
  entity?: string;
}

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
  "mentions-drill":     "Filtered Mentions",
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
  syndication_spike:      "Syndication spike (portals) ≥",
  journalist_beat:        "Journalist beat (neg. articles) ≥",
};

const ALERT_THRESHOLD_HINTS: Record<string, string> = {
  perception_score_below: "e.g. 40",
  negative_pct_above:     "e.g. 30",
  mention_spike:          "e.g. 200",
  syndication_spike:      "e.g. 10",
  journalist_beat:        "e.g. 2",
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
          placeholder={ALERT_THRESHOLD_HINTS[alertType] ?? "threshold"}
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
    syndication_spike:      "border-l-purple-500",
    journalist_beat:        "border-l-rose-500",
  };
  const RISK_BG: Record<string, string> = {
    perception_score_below: "bg-red-50",
    negative_pct_above:     "bg-amber-50",
    mention_spike:          "bg-orange-50",
    syndication_spike:      "bg-purple-50",
    journalist_beat:        "bg-rose-50",
  };
  const RISK_BADGE: Record<string, { label: string; color: string }> = {
    perception_score_below: { label: "High Risk",       color: "text-red-600 bg-red-100"       },
    negative_pct_above:     { label: "Medium Risk",     color: "text-amber-600 bg-amber-100"   },
    mention_spike:          { label: "Medium Risk",     color: "text-orange-600 bg-orange-100" },
    syndication_spike:      { label: "Amplification",   color: "text-purple-600 bg-purple-100" },
    journalist_beat:        { label: "Coverage Risk",   color: "text-rose-600 bg-rose-100"     },
  };

  const ALERT_CATEGORIES = [
    { type: "perception_score_below", label: "Reputation Score",  icon: "📊", hint: "Alert when score drops below threshold" },
    { type: "negative_pct_above",     label: "Negative %",        icon: "📉", hint: "Alert when negative % exceeds threshold" },
    { type: "mention_spike",          label: "Mention Spike",     icon: "🔔", hint: "Alert on sudden volume increase" },
    { type: "syndication_spike",      label: "Syndication Spike", icon: "📡", hint: "Alert when a story spreads to N+ portals in 24h" },
    { type: "journalist_beat",        label: "Journalist Beat",   icon: "✍️",  hint: "Alert when journalist publishes N+ negative articles in 30d" },
  ];

  const inner = alerts.length === 0 ? (
    <div className="space-y-1.5">
      {ALERT_CATEGORIES.map(cat => (
        <div key={cat.type} className="flex items-center gap-2 rounded-md border border-dashed border-gray-200 px-2 py-1.5 bg-gray-50">
          <span className="text-sm shrink-0">{cat.icon}</span>
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-medium text-gray-600 truncate">{cat.label}</div>
            <div className="text-[8px] text-gray-400 truncate">{cat.hint}</div>
          </div>
          <span className="text-[8px] text-gray-400 shrink-0 border border-gray-200 rounded px-1 py-0.5">
            {isAdmin ? "Set up" : "Not set"}
          </span>
        </div>
      ))}
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
  const [drilldown, setDrilldown] = useState<DrillFilter | null>(null);
  const [divergenceData, setDivergenceData] = useState<DivergenceSummaryData | null>(null);
  const [divOpen, setDivOpen] = useState(false);
  const mentionsRef = useRef<HTMLDivElement>(null);

  // Date range picker state
  const [days, setDays] = useState(7);
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");
  const [showCustom, setShowCustom] = useState(false);

  function openDrill(filter: DrillFilter) {
    setDrilldown(filter);
    setActivePanel("mentions-drill");
  }

  const queryParams = showCustom && customFrom && customTo
    ? { date_from: customFrom, date_to: customTo }
    : { days };

  const { data, isLoading, error } = useQuery({
    queryKey: ["overview", brandId, queryParams],
    queryFn: () => fetchOverview(brandId, queryParams),
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

  // Load divergence data when sentiment-trend detail opens
  useEffect(() => {
    if (activePanel === "sentiment-trend" && !divergenceData) {
      fetchDivergenceSummary(brandId, 14).then(setDivergenceData).catch(() => {});
    }
  }, [activePanel, brandId, divergenceData]);

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
          <h2 className="text-xs font-semibold text-gray-800">
            {activePanel === "mentions-drill" && drilldown ? drilldown.label : PANEL_TITLE[activePanel]}
          </h2>
          <div className="ml-auto flex items-center gap-1">
            {[7, 30, 90].map(d => (
              <button
                key={d}
                onClick={() => { setDays(d); setShowCustom(false); }}
                className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
                  !showCustom && days === d
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "text-gray-500 border-gray-200 hover:border-gray-300"
                }`}
              >
                {d}d
              </button>
            ))}
            <button
              onClick={() => setShowCustom(v => !v)}
              className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
                showCustom ? "bg-indigo-600 text-white border-indigo-600" : "text-gray-500 border-gray-200 hover:border-gray-300"
              }`}
            >
              Custom
            </button>
            {showCustom && (
              <div className="flex items-center gap-1 ml-1">
                <input
                  type="date"
                  value={customFrom.slice(0, 10)}
                  onChange={e => setCustomFrom(e.target.value + "T00:00:00Z")}
                  className="text-[10px] border border-gray-200 rounded px-1 py-0.5 text-gray-700"
                />
                <span className="text-[10px] text-gray-400">→</span>
                <input
                  type="date"
                  value={customTo.slice(0, 10)}
                  onChange={e => setCustomTo(e.target.value + "T23:59:59Z")}
                  className="text-[10px] border border-gray-200 rounded px-1 py-0.5 text-gray-700"
                />
              </div>
            )}
          </div>
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
            <div className="space-y-4 max-w-3xl">
              <SentimentTrendChart brandId={brandId} />
              <EditorialToneChart brandId={brandId} />
              <YouTubeSentimentSplit brandId={brandId} />
              {/* Divergent Headlines */}
              <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                <button
                  className="flex items-center justify-between w-full text-sm font-semibold text-gray-800"
                  onClick={() => setDivOpen(o => !o)}
                >
                  <span>Divergent Headlines</span>
                  <span className="text-gray-400 text-xs">{divOpen ? "▲ hide" : "▼ show"}</span>
                </button>
                {divergenceData && (
                  <p className="text-xs text-gray-500 mt-1">
                    {divergenceData.total_divergent_count} articles ({divergenceData.divergent_pct}%) had divergent headline/body sentiment in the last {divergenceData.period_days} days.
                  </p>
                )}
                {divOpen && (
                  <div className="mt-3 space-y-2">
                    {!divergenceData && <p className="text-xs text-gray-400">Loading…</p>}
                    {divergenceData && divergenceData.articles.length === 0 && (
                      <p className="text-xs text-gray-400">No divergent articles detected.</p>
                    )}
                    {divergenceData?.articles.map((a, i) => {
                      const hScore = a.headline_sentiment_score;
                      const bScore = a.body_sentiment_score;
                      const scoreChip = (v: number) => (
                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${v >= 0 ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"}`}>
                          {v >= 0 ? "+" : ""}{v.toFixed(2)}
                        </span>
                      );
                      return (
                        <div key={i} className="flex items-start gap-2 py-1 border-b border-gray-50 last:border-0">
                          <a
                            href={a.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 text-xs text-blue-600 hover:underline truncate"
                            title={a.title}
                          >
                            {a.title.slice(0, 80)}{a.title.length > 80 ? "…" : ""}
                          </a>
                          <div className="flex items-center gap-1 shrink-0">
                            <span className="text-[9px] text-gray-400">H</span>{scoreChip(hScore)}
                            <span className="text-[9px] text-gray-400">B</span>{scoreChip(bScore)}
                            <span className="text-[9px] font-medium text-amber-600 bg-amber-50 px-1 py-0.5 rounded">↕</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
          {activePanel === "mentions-donut" && (
            <div className="max-w-lg">
              <MentionsBySourceDonut
                brandId={brandId}
                onSourceClick={(category, label) =>
                  openDrill({ label: `Source: ${label}`, sourceCategory: category })
                }
              />
            </div>
          )}
          {activePanel === "top-headlines" && (
            <div className="max-w-2xl">
              <TopHeadlines brandId={brandId} onViewAll={() => setActivePanel("mentions")} />
            </div>
          )}
          {activePanel === "review-sites" && (
            <div className="max-w-lg">
              <ReviewSitesSummary
                brandId={brandId}
                onThemeClick={(topic) =>
                  openDrill({ label: `Theme: ${topic}`, topic })
                }
              />
            </div>
          )}
          {activePanel === "top-issues" && (
            <div className="max-w-lg">
              <TopIssuesTable
                brandId={brandId}
                onClusterClick={(name) =>
                  openDrill({ label: `Issue: ${name.replace(/_/g, " ")}`, issueCategory: name })
                }
                onCategoryClick={(cat) =>
                  openDrill({ label: `Category: ${cat.replace(/_/g, " ")}`, issueCategory: cat })
                }
              />
            </div>
          )}
          {activePanel === "sentiment-by-source" && (
            <div className="max-w-lg">
              <SentimentBySourceTable brandId={brandId} />
            </div>
          )}
          {activePanel === "competitor-sov" && (
            <div className="max-w-md">
              <CompetitorShareOfVoice
                brandId={brandId}
                onEntityClick={(name) =>
                  openDrill({ label: `Mentions: ${name}`, entity: name })
                }
              />
            </div>
          )}
          {activePanel === "mentions-drill" && drilldown && (
            <div ref={mentionsRef}>
              <MentionsList
                brandId={brandId}
                brandName={brandName}
                portals={data.top_sources.map(s => s.portal_id)}
                topics={data.top_topics}
                states={data.state_breakdown.map(s => s.state)}
                initialTopic={drilldown.topic ?? ""}
                initialSourceCategory={drilldown.sourceCategory ?? ""}
                initialIssueCategory={drilldown.issueCategory ?? ""}
                initialQ={drilldown.q ?? ""}
                initialEntity={drilldown.entity ?? ""}
                selectable
              />
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
          {/* Date range picker */}
          <div className="flex items-center gap-1">
            {[7, 30, 90].map(d => (
              <button
                key={d}
                onClick={() => { setDays(d); setShowCustom(false); }}
                className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
                  !showCustom && days === d
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "text-gray-500 border-gray-200 hover:border-gray-300"
                }`}
              >
                {d}d
              </button>
            ))}
            <button
              onClick={() => setShowCustom(v => !v)}
              className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
                showCustom ? "bg-indigo-600 text-white border-indigo-600" : "text-gray-500 border-gray-200 hover:border-gray-300"
              }`}
            >
              Custom
            </button>
            {showCustom && (
              <div className="flex items-center gap-1 ml-1">
                <input
                  type="date"
                  value={customFrom.slice(0, 10)}
                  onChange={e => setCustomFrom(e.target.value + "T00:00:00Z")}
                  className="text-[10px] border border-gray-200 rounded px-1 py-0.5 text-gray-700"
                />
                <span className="text-[10px] text-gray-400">→</span>
                <input
                  type="date"
                  value={customTo.slice(0, 10)}
                  onChange={e => setCustomTo(e.target.value + "T23:59:59Z")}
                  className="text-[10px] border border-gray-200 rounded px-1 py-0.5 text-gray-700"
                />
              </div>
            )}
          </div>
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
      <div className="grid grid-cols-5 gap-1.5 flex-none">
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
          <CompetitorShareOfVoice brandId={brandId} compact onClick={() => setActivePanel("competitor-sov")} />
        </div>
        <div className="col-span-2 min-h-0 cursor-pointer" onClick={() => setActivePanel("alerts")}>
          <AlertsRiskCards brandId={brandId} isAdmin={!!isAdmin} userEmail={userEmail} compact />
        </div>
      </div>

    </div>
  );
}
