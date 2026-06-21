import { useEffect, useState } from "react";
import api from "../lib/api";

interface VideoRiskItem {
  article_id: string;
  title: string;
  url: string;
  portal_id: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  sentiment_score: number;
  risk_score: number;
  reach_tier: "Viral" | "High" | "Mid" | "Low";
  published_at: string | null;
}

interface BrandRiskScoresResponse {
  videos: VideoRiskItem[];
  brand_id: string;
  period_days: number;
}

interface Props {
  brandId: string;
  days?: number;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

function ReachTierBadge({ tier }: { tier: string }) {
  const styles: Record<string, string> = {
    Viral: "bg-purple-100 text-purple-700 border-purple-200",
    High:  "bg-blue-100 text-blue-700 border-blue-200",
    Mid:   "bg-teal-100 text-teal-700 border-teal-200",
    Low:   "bg-gray-100 text-gray-500 border-gray-200",
  };
  const cls = styles[tier] ?? styles.Low;
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold border ${cls}`}>
      {tier}
    </span>
  );
}

/** Horizontal risk bar: width proportional to abs(risk_score), colour by sign. */
function RiskBar({ score, maxAbs }: { score: number; maxAbs: number }) {
  const pct = maxAbs > 0 ? Math.abs(score) / maxAbs : 0;
  const widthPct = Math.round(pct * 100);
  const isNeg = score < 0;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            isNeg ? "bg-red-500" : "bg-green-500"
          }`}
          style={{ width: `${Math.max(widthPct, 2)}%` }}
        />
      </div>
      <span
        className={`text-[11px] font-mono w-12 text-right shrink-0 ${
          isNeg ? "text-red-600" : "text-green-600"
        }`}
      >
        {score > 0 ? "+" : ""}
        {score.toFixed(2)}
      </span>
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 px-4 py-3 animate-pulse">
      <div className="flex-1 space-y-1.5">
        <div className="h-3 bg-gray-200 rounded w-2/3" />
        <div className="h-2 bg-gray-100 rounded w-1/2" />
      </div>
      <div className="w-32 h-2 bg-gray-200 rounded-full" />
    </div>
  );
}

export function BrandRiskScores({ brandId, days = 30 }: Props) {
  const [data, setData] = useState<BrandRiskScoresResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get<BrandRiskScoresResponse>(`/dashboard/brand-risk-scores/${brandId}`, {
        params: { days },
      })
      .then(r => setData(r.data))
      .catch(() => setError("Failed to load risk scores."))
      .finally(() => setLoading(false));
  }, [brandId, days]);

  const maxAbs =
    data?.videos.length
      ? Math.max(...data.videos.map(v => Math.abs(v.risk_score)))
      : 1;

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Brand Risk Scores</h3>
          <p className="text-[11px] text-gray-400 mt-0.5">
            Top YouTube videos by risk impact — last {days} days
          </p>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-gray-400">
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-sm bg-green-500" /> Positive risk
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-sm bg-red-500" /> Negative risk
          </span>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="divide-y divide-gray-50">
          {Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)}
        </div>
      ) : error ? (
        <div className="px-4 py-6 text-sm text-red-500 text-center">{error}</div>
      ) : !data || data.videos.length === 0 ? (
        <div className="px-4 py-10 text-center text-gray-400">
          <svg
            className="w-8 h-8 mx-auto mb-2 text-gray-300"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.362a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z"
            />
          </svg>
          <div className="text-sm font-medium text-gray-500">No YouTube data</div>
          <div className="text-[11px] text-gray-400 mt-0.5">
            Risk scores appear after YouTube videos are collected.
          </div>
        </div>
      ) : (
        <div className="divide-y divide-gray-50">
          {data.videos.map((v, i) => (
            <div key={v.article_id} className="px-4 py-3 hover:bg-gray-50/50 transition-colors">
              {/* Rank + title row */}
              <div className="flex items-start gap-2 mb-1.5">
                <span className="text-[11px] text-gray-300 font-mono w-4 shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
                    <ReachTierBadge tier={v.reach_tier} />
                  </div>
                  <a
                    href={v.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs font-medium text-gray-800 hover:text-blue-600 hover:underline line-clamp-1 leading-snug"
                  >
                    {v.title}
                  </a>
                  <div className="flex items-center gap-2 mt-0.5 text-[10px] text-gray-400">
                    <span>{formatNumber(v.view_count)} views</span>
                    {v.like_count > 0 && <span>{formatNumber(v.like_count)} likes</span>}
                    {v.comment_count > 0 && (
                      <span>{formatNumber(v.comment_count)} comments</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Risk bar */}
              <div className="pl-6">
                <RiskBar score={v.risk_score} maxAbs={maxAbs} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
