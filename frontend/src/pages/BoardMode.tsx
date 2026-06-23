import { useQuery } from "@tanstack/react-query";
import { fetchMorningBrief, fetchRiskForecast, fetchIssueRadar, fetchStoryFeed, type IssueRadarPoint } from "../lib/api";

interface Props {
  brandId: string;
  brandName: string;
  days: number;
  onBack: () => void;
}

function dateLine() {
  return new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
}

function RiskBadge({ score }: { score: number }) {
  const [cls, label] = score >= 65
    ? ["text-red-400", "HIGH RISK"]
    : score >= 40
    ? ["text-amber-400", "MEDIUM"]
    : ["text-emerald-400", "LOW RISK"];
  return <span className={`text-[10px] font-bold tracking-wider ${cls}`}>{label}</span>;
}

function Skeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2 animate-pulse">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-3 bg-white/10 rounded" style={{ width: `${70 + (i % 3) * 10}%` }} />
      ))}
    </div>
  );
}

function IssueRow({ issue }: { issue: IssueRadarPoint }) {
  const label = issue.velocity >= 3 ? "Escalating" : issue.velocity >= 1.5 ? "Elevated" : "Stable";
  const icon = issue.velocity >= 3 ? "▲" : issue.velocity >= 1.5 ? "◆" : "•";
  const color = issue.velocity >= 3 ? "text-red-400" : issue.velocity >= 1.5 ? "text-amber-400" : "text-white/30";
  return (
    <div className="flex items-start gap-3">
      <span className={`text-[11px] pt-0.5 ${color}`}>{icon}</span>
      <div>
        <div className="text-[13px] text-white/70 capitalize">{issue.issue.replace(/_/g, " ")}</div>
        <div className="text-[10px] text-white/30">{label} · {issue.count} articles · {issue.velocity.toFixed(1)}× velocity</div>
      </div>
    </div>
  );
}

export function BoardMode({ brandId, brandName, days, onBack }: Props) {
  const { data: brief, isLoading: loadBrief } = useQuery({
    queryKey: ["morning-brief", brandId, days],
    queryFn: () => fetchMorningBrief(brandId, days),
    staleTime: 15 * 60_000,
  });

  const { data: risk, isLoading: loadRisk } = useQuery({
    queryKey: ["risk-forecast", brandId, days],
    queryFn: () => fetchRiskForecast(brandId, days),
    staleTime: 15 * 60_000,
  });

  const { data: radar } = useQuery({
    queryKey: ["issue-radar", brandId, days],
    queryFn: () => fetchIssueRadar(brandId, days),
    staleTime: 15 * 60_000,
  });

  const { data: stories } = useQuery({
    queryKey: ["story-feed", brandId, days, 5],
    queryFn: () => fetchStoryFeed(brandId, days, 5),
    staleTime: 15 * 60_000,
  });

  // Build 5 board highlights from morning brief data
  const highlights = brief?.highlights ?? [];
  const displayPoints = highlights.length > 0
    ? highlights.slice(0, 5)
    : [`Monitoring ${brandName} across all media channels.`, "Sentiment data is being processed."];

  const topIssues = (radar?.points ?? []).slice(0, 3);
  const currentRisk = risk?.historical?.at(-1)?.risk_score ?? 0;
  const forecast7d = risk?.forecasts?.at(-1)?.predicted_risk ?? currentRisk;
  const direction = forecast7d > currentRisk + 2 ? "Rising" : forecast7d < currentRisk - 2 ? "Declining" : "Stable";
  const dirIcon = forecast7d > currentRisk + 2 ? "▲" : forecast7d < currentRisk - 2 ? "▼" : "→";
  const dirColor = forecast7d > currentRisk + 2 ? "text-red-400" : forecast7d < currentRisk - 2 ? "text-emerald-400" : "text-white/40";

  return (
    <div className="min-h-full bg-[#09111f] text-white flex flex-col print:bg-white print:text-black">
      {/* Header */}
      <div className="flex items-center justify-between px-10 py-5 border-b border-white/10 flex-none">
        <div className="flex items-center gap-6">
          <button
            onClick={onBack}
            className="text-[11px] text-white/40 hover:text-white/80 transition-colors flex items-center gap-1.5 print:hidden"
          >
            ← Dashboard
          </button>
          <div>
            <span className="text-[13px] font-semibold text-white/90 tracking-wide">BrandPulse</span>
            <span className="text-[11px] text-white/30 ml-2">· Board Intelligence · {brandName}</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] text-white/30">{dateLine()}</span>
          <button
            onClick={() => window.print()}
            className="text-[10px] border border-white/20 text-white/50 hover:text-white/80 hover:border-white/40 px-3 py-1 rounded transition-colors print:hidden"
          >
            Export PDF
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-10 py-8 max-w-4xl mx-auto w-full space-y-10">

        {/* Opening */}
        <div>
          <p className="text-[22px] font-light text-white/90 leading-relaxed mb-6">
            {brief?.greeting
              ? <>{brief.greeting.replace(/^Good \w+[,.]?\s*/i, "")}</>
              : <>Good morning. Here are the key developments for <span className="font-semibold text-white">{brandName}</span>.</>
            }
          </p>

          {loadBrief ? (
            <Skeleton lines={5} />
          ) : (
            <ol className="space-y-5">
              {displayPoints.map((point, i) => (
                <li key={i} className="flex gap-5">
                  <span className="text-[15px] font-semibold text-white/20 tabular-nums w-6 shrink-0 pt-0.5">{i + 1}.</span>
                  <p className="text-[15px] text-white/75 leading-relaxed">{point}</p>
                </li>
              ))}
            </ol>
          )}

          {/* Score summary pill */}
          {brief && (
            <div className="mt-6 inline-flex items-center gap-3 bg-[#111e36] border border-white/10 rounded-lg px-4 py-2">
              <span className="text-[11px] text-white/40">Score change</span>
              <span className={`text-[14px] font-semibold ${brief.score_direction === "up" ? "text-emerald-400" : brief.score_direction === "down" ? "text-red-400" : "text-white/60"}`}>
                {brief.score_direction === "up" ? "+" : brief.score_direction === "down" ? "-" : ""}{Math.abs(brief.score_change).toFixed(1)} pts
              </span>
              <span className="text-[10px] text-white/30">· {days}d window · {brief.confidence_pct}% confidence</span>
            </div>
          )}
        </div>

        {/* Two-column: Risk Status + Top Concerns */}
        <div className="grid grid-cols-2 gap-8 border-t border-white/8 pt-8">
          <div>
            <div className="text-[9px] uppercase tracking-widest text-white/30 mb-4">Risk Status</div>
            {loadRisk ? <Skeleton lines={4} /> : (
              <div className="space-y-3">
                <div className="flex items-baseline gap-3">
                  <span className="text-[32px] font-light text-white">{Math.round(currentRisk)}</span>
                  <div>
                    <RiskBadge score={currentRisk} />
                    <div className="text-[10px] text-white/30 mt-0.5">Risk Score / 100</div>
                  </div>
                </div>
                <div className={`text-[12px] flex items-center gap-2 ${dirColor}`}>
                  {dirIcon}{" "}
                  <span className="text-white/50">7-day outlook:</span>{" "}
                  <span className="text-white/70">{direction}</span>
                  <span className="text-white/30">({Math.round(forecast7d)} projected)</span>
                </div>
                {risk?.narrative && (
                  <p className="text-[12px] text-white/50 leading-relaxed border-l-2 border-blue-500/30 pl-3 mt-2">
                    {risk.narrative}
                  </p>
                )}
              </div>
            )}
          </div>

          <div>
            <div className="text-[9px] uppercase tracking-widest text-white/30 mb-4">Top Concerns</div>
            {topIssues.length === 0 ? (
              <p className="text-[12px] text-white/30 italic">No elevated issues detected.</p>
            ) : (
              <div className="space-y-3">
                {topIssues.map((issue, i) => <IssueRow key={i} issue={issue} />)}
              </div>
            )}
          </div>
        </div>

        {/* Top Headlines */}
        {stories && stories.stories.length > 0 && (
          <div className="border-t border-white/8 pt-8">
            <div className="text-[9px] uppercase tracking-widest text-white/30 mb-4">Top Stories This Period</div>
            <div className="space-y-3">
              {stories.stories.slice(0, 4).map((s, i) => {
                const impColor = s.impact_score >= 70 ? "text-red-400" : s.impact_score >= 40 ? "text-amber-400" : "text-white/30";
                const sentColor = s.sentiment_label === "negative" ? "bg-red-500/15 text-red-400" : s.sentiment_label === "positive" ? "bg-emerald-500/15 text-emerald-400" : "bg-white/8 text-white/35";
                return (
                  <div key={s.article_id} className="flex items-start gap-3">
                    <span className="text-[12px] text-white/20 tabular-nums w-4 shrink-0 pt-0.5">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-[13px] text-white/70 hover:text-white leading-snug line-clamp-2 transition-colors">
                        {s.title}
                      </a>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[9px] text-white/25">{s.portal_name}</span>
                        <span className={`text-[8px] font-semibold px-1 py-0.5 rounded ${sentColor}`}>{s.sentiment_label}</span>
                        <span className={`text-[9px] font-semibold ml-auto ${impColor}`}>Impact {s.impact_score}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* AI Recommendation */}
        {risk?.narrative && (
          <div className="border-t border-white/8 pt-8">
            <div className="text-[9px] uppercase tracking-widest text-white/30 mb-4">
              AI Recommendation{risk.confidence_pct > 0 ? ` · ${risk.confidence_pct}% confidence` : ""}
            </div>
            <div className="bg-[#111e36] border border-blue-500/15 rounded-xl p-5">
              <p className="text-[14px] text-white/75 leading-relaxed italic">
                "{brief?.highlights?.[0] ?? risk.narrative}"
              </p>
              <div className="flex gap-3 mt-4">
                {["Accept", "Modify", "Delegate"].map(action => (
                  <button
                    key={action}
                    className="text-[10px] border border-white/15 text-white/40 hover:text-white/70 hover:border-white/30 px-4 py-1.5 rounded transition-colors"
                  >
                    {action}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-10 py-4 border-t border-white/8 text-[9px] text-white/20 flex items-center justify-between flex-none print:hidden">
        <span>BrandPulse · Confidential · {days}d window</span>
        <span>Powered by AI analysis across all monitored media sources</span>
      </div>
    </div>
  );
}
