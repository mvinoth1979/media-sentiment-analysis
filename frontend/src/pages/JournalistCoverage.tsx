import { useEffect, useState } from "react";
import { fetchJournalistCoverage } from "../lib/api";
import type { JournalistProfile, JournalistArticleItem } from "../lib/types";

interface Props {
  brandId: string;
  brandName: string;
}

function timeAgo(iso: string): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return months === 1 ? "1 month ago" : `${months} months ago`;
}

function SentimentBadge({ label }: { label: string }) {
  const cls =
    label === "positive" ? "bg-green-100 text-green-700" :
    label === "negative" ? "bg-red-100 text-red-700" :
    "bg-gray-100 text-gray-500";
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${cls}`}>
      {label}
    </span>
  );
}

function SentimentBar({ pos, neu, neg }: { pos: number; neu: number; neg: number }) {
  const total = pos + neu + neg || 1;
  const posPct = (pos / total) * 100;
  const neuPct = (neu / total) * 100;
  const negPct = (neg / total) * 100;
  return (
    <div className="flex h-2 w-full rounded-full overflow-hidden bg-gray-100">
      {posPct > 0 && <div className="bg-green-500 h-full" style={{ width: `${posPct}%` }} />}
      {neuPct > 0 && <div className="bg-gray-300 h-full" style={{ width: `${neuPct}%` }} />}
      {negPct > 0 && <div className="bg-red-400 h-full" style={{ width: `${negPct}%` }} />}
    </div>
  );
}

function NegPct({ pct }: { pct: number }) {
  const cls = pct > 50 ? "text-red-600 font-semibold" : pct > 30 ? "text-amber-600" : "text-gray-500";
  return <span className={`text-xs ${cls}`}>{pct.toFixed(0)}% neg</span>;
}

function JournalistRow({ j }: { j: JournalistProfile }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="border border-gray-100 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-4 px-4 py-3 hover:bg-gray-50 transition-colors text-left"
      >
        {/* Avatar initial */}
        <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-sm font-bold shrink-0">
          {j.author.charAt(0).toUpperCase()}
        </div>

        {/* Name */}
        <div className="w-40 shrink-0">
          <div className="text-sm font-semibold text-gray-800 truncate">{j.author}</div>
          <div className="text-[11px] text-gray-400">Last seen {timeAgo(j.last_article_at)}</div>
        </div>

        {/* Sentiment bar */}
        <div className="flex-1 min-w-0">
          <SentimentBar pos={j.positive_count} neu={j.neutral_count} neg={j.negative_count} />
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 shrink-0">
          <NegPct pct={j.negative_pct} />
          <span className="text-xs text-gray-500 w-16 text-right">{j.total_articles} articles</span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-100 px-4 py-3 bg-gray-50/50 space-y-2">
          <div className="text-[11px] text-gray-500 font-medium uppercase tracking-wide mb-2">Recent articles</div>
          {j.recent_articles.length === 0 ? (
            <div className="text-xs text-gray-400">No articles available.</div>
          ) : (
            j.recent_articles.map((a: JournalistArticleItem, i: number) => (
              <div key={i} className="flex items-start gap-2">
                <SentimentBadge label={a.sentiment_label} />
                <a
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-indigo-600 hover:underline flex-1 leading-snug"
                >
                  {a.title}
                </a>
                <span className="text-[10px] text-gray-400 shrink-0">{timeAgo(a.published_at)}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="border border-gray-100 rounded-lg px-4 py-3 flex items-center gap-4 animate-pulse">
      <div className="w-8 h-8 rounded-full bg-gray-200 shrink-0" />
      <div className="w-40 space-y-1.5 shrink-0">
        <div className="h-3 bg-gray-200 rounded w-28" />
        <div className="h-2 bg-gray-100 rounded w-20" />
      </div>
      <div className="flex-1 h-2 bg-gray-200 rounded-full" />
      <div className="w-20 h-3 bg-gray-100 rounded" />
    </div>
  );
}

export function JournalistCoverage({ brandId, brandName }: Props) {
  const [data, setData] = useState<JournalistProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchJournalistCoverage(brandId, 90)
      .then(d => setData(d.journalists))
      .catch(() => setError("Failed to load journalist data."))
      .finally(() => setLoading(false));
  }, [brandId]);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Journalist Coverage</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Authors writing about <span className="font-medium text-gray-700">{brandName}</span> — last 90 days · sorted by negative article count
        </p>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mb-4 text-[11px] text-gray-500">
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-green-500 inline-block" /> Positive</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-gray-300 inline-block" /> Neutral</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-red-400 inline-block" /> Negative</span>
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)}
        </div>
      ) : error ? (
        <div className="text-sm text-red-500 bg-red-50 border border-red-100 rounded-lg px-4 py-3">{error}</div>
      ) : data.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <svg className="w-10 h-10 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
          <div className="text-sm font-medium text-gray-500">No author data yet</div>
          <div className="text-xs text-gray-400 mt-1">Author extraction will populate after the next pipeline run.</div>
        </div>
      ) : (
        <div className="space-y-2">
          {data.map((j, i) => <JournalistRow key={i} j={j} />)}
        </div>
      )}
    </div>
  );
}
