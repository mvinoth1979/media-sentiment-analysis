import { useEffect, useState } from "react";
import { fetchYTSentimentSplit } from "../lib/api";
import type { YTSentimentBucket, YTSentimentSplitData } from "../lib/types";

interface Props {
  brandId: string;
  compact?: boolean;
}

const LABEL_COLOR: Record<string, string> = {
  positive: "bg-green-100 text-green-700",
  neutral:  "bg-gray-100 text-gray-600",
  negative: "bg-red-100 text-red-600",
};

function SentimentBar({ bucket }: { bucket: YTSentimentBucket }) {
  const t = bucket.total || 1;
  const posPct = Math.round((bucket.positive / t) * 100);
  const neuPct = Math.round((bucket.neutral  / t) * 100);
  const negPct = 100 - posPct - neuPct;
  return (
    <div className="flex h-2 rounded-full overflow-hidden w-full mt-2 mb-3">
      <div className="bg-green-400 transition-all" style={{ width: `${posPct}%` }} />
      <div className="bg-gray-300 transition-all" style={{ width: `${neuPct}%` }} />
      <div className="bg-red-400 transition-all"   style={{ width: `${negPct}%` }} />
    </div>
  );
}

function BucketPanel({ label, icon, bucket }: { label: string; icon: string; bucket: YTSentimentBucket }) {
  const t = bucket.total || 1;
  const pct = (n: number) => Math.round((n / t) * 100);
  return (
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-base">{icon}</span>
        <span className="text-[11px] font-semibold text-gray-700">{label}</span>
        <span className="ml-auto text-[10px] text-gray-400">{bucket.total.toLocaleString()} items</span>
      </div>
      <SentimentBar bucket={bucket} />
      <div className="space-y-1">
        {(["positive", "neutral", "negative"] as const).map(k => (
          <div key={k} className="flex items-center justify-between text-[11px]">
            <span className="capitalize text-gray-500">{k}</span>
            <span className="font-medium text-gray-700">
              {bucket[k].toLocaleString()} <span className="text-gray-400">({pct(bucket[k])}%)</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function YouTubeSentimentSplit({ brandId, compact }: Props) {
  const [data, setData] = useState<YTSentimentSplitData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchYTSentimentSplit(brandId, 30)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [brandId]);

  if (loading) return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm animate-pulse h-28" />
  );

  const noData = !data || (data.creator.total === 0 && data.audience.total === 0);
  if (noData) return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <p className="text-xs text-gray-400 text-center py-4">
        No YouTube data yet — enable YouTube monitoring in <strong>Channel Settings</strong>.
      </p>
    </div>
  );

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-800 mb-4">
        YouTube Sentiment — Creator vs Audience
      </h3>

      {/* Two-column sentiment breakdown */}
      <div className="flex gap-6">
        <BucketPanel label="Creator (Videos)"   icon="🎥" bucket={data.creator}  />
        <div className="w-px bg-gray-100 shrink-0" />
        <BucketPanel label="Audience (Comments)" icon="💬" bucket={data.audience} />
      </div>

      {/* Divergent videos — only in expanded mode when present */}
      {!compact && data.divergent_videos.length > 0 && (
        <div className="mt-4 border-t border-gray-100 pt-3">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-amber-500 text-sm">⚠</span>
            <span className="text-[11px] font-semibold text-amber-700">
              Divergent Videos — creator and audience sentiment disagree
            </span>
          </div>
          <div className="space-y-2">
            {data.divergent_videos.map((v, i) => (
              <div key={i} className="flex items-start gap-2 text-[11px]">
                <a
                  href={v.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 text-gray-700 hover:text-indigo-600 truncate leading-tight"
                  title={v.title}
                >
                  {v.title.length > 65 ? v.title.slice(0, 62) + "…" : v.title}
                </a>
                <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium ${LABEL_COLOR[v.creator_label] ?? "bg-gray-100 text-gray-600"}`}>
                  {v.creator_label}
                </span>
                <span className="shrink-0 text-gray-300">→</span>
                <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium ${LABEL_COLOR[v.audience_label] ?? "bg-gray-100 text-gray-600"}`}>
                  {v.audience_label}
                </span>
                <span className="shrink-0 text-gray-400 whitespace-nowrap">{v.comment_count} comments</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
