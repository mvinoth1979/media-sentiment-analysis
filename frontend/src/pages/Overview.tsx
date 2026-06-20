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
          placeholder={alertType === "perception_score_below" ? "e.g. 40" : alertType === "negative_pct_above" ? "e.g. 50" : "e.g. 30"}
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

function AlertsRiskCards({ brandId, isAdmin, userEmail }: { brandId: string; isAdmin: boolean; userEmail?: string }) {
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
    perception_score_below: { label: "High Risk",    color: "text-red-600 bg-red-100"    },
    negative_pct_above:     { label: "Medium Risk",  color: "text-amber-600 bg-amber-100" },
    mention_spike:          { label: "Medium Risk",  color: "text-orange-600 bg-orange-100" },
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-800">Alerts & Risks</div>
        <button className="text-[11px] text-blue-600 hover:text-blue-700 font-medium">View All</button>
      </div>

      {alerts.length === 0 ? (
        <div className="py-4 text-xs text-gray-400 text-center">
          No active alerts configured.{isAdmin ? "" : " Ask an admin to add alerts."}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {alerts.map(a => {
            const badge = RISK_BADGE[a.alert_type] ?? { label: "Alert", color: "text-gray-600 bg-gray-100" };
            return (
              <div
                key={a.id}
                className={`relative border border-l-4 border-gray-100 rounded-lg px-3 py-2.5 ${RISK_BORDER[a.alert_type] ?? "border-l-gray-400"} ${RISK_BG[a.alert_type] ?? "bg-gray-50"}`}
              >
                <button
                  onClick={() => deleteMutation.mutate(a.id)}
                  disabled={deleteMutation.isPending}
                  className="absolute top-2 right-2 text-gray-300 hover:text-red-400 text-sm leading-none"
                  title="Remove alert"
                >×</button>
                <span className={`inline-block text-[9px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full mb-1.5 ${badge.color}`}>
                  {badge.label}
                </span>
                <div className="text-xs text-gray-700">
                  {ALERT_TYPE_LABELS[a.alert_type]} threshold: <span className="font-semibold">{a.threshold}</span>
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">{a.notify_email}</div>
                {a.last_triggered_at && (
                  <div className="text-[10px] text-gray-400 mt-0.5">
                    Last fired: {new Date(a.last_triggered_at).toLocaleDateString()}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {isAdmin && <AlertsSection brandId={brandId} userEmail={userEmail} />}
    </div>
  );
}

export function Overview({ brandId, brandName, isAdmin, userEmail, onLastUpdated }: Props) {
  const [mentionsSentimentFilter, setMentionsSentimentFilter] = useState("");
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

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-gray-400 text-sm">Loading…</div>
  );
  if (error || !data || !data.kpi) return (
    <div className="text-red-500 p-8 text-sm">Failed to load dashboard. No data yet — the pipeline runs hourly.</div>
  );

  const { kpi } = data;

  return (
    <div className="p-5 space-y-4 bg-gray-50 min-h-screen">

      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Executive Overview</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Real-time overview of brand sentiment across digital and news ecosystem
            {data.last_processed_at && ` · Last updated ${formatLastProcessed(data.last_processed_at)}`}
          </p>
        </div>
        {data.pipeline_status === "running" && (
          <span className="flex items-center gap-1.5 text-xs text-blue-600 bg-blue-50 border border-blue-200 rounded-full px-3 py-1 shrink-0">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
            </span>
            Pipeline running
          </span>
        )}
      </div>

      {/* ── Row 1: 5 KPI Cards ────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <KPICard
          label="Total Mentions"
          value={formatCount(kpi.total)}
          delta={kpi.mentions_delta_pct}
          deltaUnit="%"
          sub="vs last period"
          icon="📰"
          accentColor="blue"
        />
        <KPICard
          label="Positive Mentions"
          value={formatCount(kpi.positive)}
          pct={kpi.positive_pct}
          icon="😊"
          accentColor="green"
        />
        <KPICard
          label="Neutral Mentions"
          value={formatCount(kpi.neutral)}
          pct={kpi.neutral_pct}
          icon="😐"
          accentColor="gray"
        />
        <KPICard
          label="Negative Mentions"
          value={formatCount(kpi.negative)}
          pct={kpi.negative_pct}
          icon="😟"
          accentColor="red"
        />
        <KPICard
          label="Reputation Index"
          value={`${kpi.perception_score.toFixed(0)} / 100`}
          delta={kpi.perception_score_delta}
          deltaUnit=" pts"
          icon="📊"
          accentColor="purple"
        />
      </div>

      {/* ── Row 2: Sentiment Trend | Mentions Donut | Top Headlines ──────── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className="xl:col-span-5">
          <SentimentTrendChart brandId={brandId} />
        </div>
        <div className="xl:col-span-3">
          <MentionsBySourceDonut brandId={brandId} />
        </div>
        <div className="xl:col-span-4">
          <TopHeadlines
            brandId={brandId}
            onViewAll={(tab) => {
              mentionsRef.current?.scrollIntoView({ behavior: "smooth" });
              setMentionsSentimentFilter(tab === "trending" ? "" : tab);
            }}
          />
        </div>
      </div>

      {/* ── Row 3: Review Sites | Top Issues | Sentiment by Source ────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ReviewSitesSummary brandId={brandId} />
        <TopIssuesTable brandId={brandId} />
        <SentimentBySourceTable brandId={brandId} />
      </div>

      {/* ── Row 4: Competitor SoV | Alerts & Risks ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <CompetitorShareOfVoice brandName={brandName} />
        <div className="lg:col-span-2">
          <AlertsRiskCards brandId={brandId} isAdmin={!!isAdmin} userEmail={userEmail} />
        </div>
      </div>

      {/* ── India state map ────────────────────────────────────────────────── */}
      <IndiaStateMap
        data={data.state_breakdown}
        onStateClick={(state) => {
          const url = new URL(window.location.href);
          url.searchParams.set("state", state);
          window.history.pushState({}, "", url.toString());
          window.dispatchEvent(new PopStateEvent("popstate"));
        }}
      />

      {/* ── Top Sources ────────────────────────────────────────────────────── */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <div className="text-sm font-semibold text-gray-800 mb-3">Top Sources</div>
        <div className="space-y-2">
          {data.top_sources.map(s => (
            <div key={s.portal_id}>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span className="truncate max-w-[140px]">{s.portal_id.replace(/_/g, " ")}</span>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`text-[10px] font-mono px-1 rounded ${
                    s.avg_credibility >= 0.85 ? "bg-green-50 text-green-600" :
                    s.avg_credibility >= 0.75 ? "bg-yellow-50 text-yellow-600" :
                    "bg-gray-100 text-gray-500"
                  }`}>
                    {s.avg_credibility.toFixed(2)}
                  </span>
                  <span>{s.count}</span>
                </div>
              </div>
              <div className="bg-gray-100 rounded h-1.5">
                <div className="bg-blue-500 h-full rounded"
                     style={{ width: `${Math.min(100, (s.count / (kpi.total || 1)) * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Topics + Keywords ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div className="text-sm font-semibold text-gray-800 mb-3">Topics</div>
          <div className="flex flex-wrap gap-2">
            {data.top_topics.map(t => (
              <span key={t} className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full border border-blue-100">
                {t.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div className="text-sm font-semibold text-gray-800 mb-3">Keywords</div>
          <div className="flex flex-wrap gap-2">
            {data.top_keywords.map(k => (
              <span key={k} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
                {k}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Mentions table ─────────────────────────────────────────────────── */}
      <div ref={mentionsRef}>
        <MentionsList
          brandId={brandId}
          brandName={brandName}
          portals={data.top_sources.map(s => s.portal_id)}
          topics={data.top_topics}
          states={data.state_breakdown.map(s => s.state)}
          initialSentiment={mentionsSentimentFilter}
          selectable
          syncUrl
        />
      </div>

    </div>
  );
}
