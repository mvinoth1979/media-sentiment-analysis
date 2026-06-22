import { useEffect, useState } from "react";
import { fetchYTSentimentSplit } from "../lib/api";
import type { YTSentimentBucket, YTSentimentSplitData } from "../lib/types";

interface Props {
  brandId: string;
  compact?: boolean;
}

const LABEL_COLOR: Record<string, string> = {
  positive: "bg-green-500/20 text-green-400",
  neutral:  "bg-white/10 text-white/50",
  negative: "bg-red-500/20 text-red-400",
};

function SentimentBar({ bucket }: { bucket: YTSentimentBucket }) {
  const t = bucket.total || 1;
  const posPct = Math.round((bucket.positive / t) * 100);
  const neuPct = Math.round((bucket.neutral  / t) * 100);
  const negPct = 100 - posPct - neuPct;
  return (
    <div className="flex h-2 rounded-full overflow-hidden w-full mt-2 mb-3">
      <div className="bg-green-400 transition-all" style={{ width: `${posPct}%` }} />
      <div className="bg-white/20 transition-all" style={{ width: `${neuPct}%` }} />
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
        <span className="text-[11px] font-semibold text-white/80">{label}</span>
        <span className="ml-auto text-[10px] text-white/40">{bucket.total.toLocaleString()} items</span>
      </div>
      <SentimentBar bucket={bucket} />
      <div className="space-y-1">
        {(["positive", "neutral", "negative"] as const).map(k => (
          <div key={k} className="flex items-center justify-between text-[11px]">
            <span className="capitalize text-white/50">{k}</span>
            <span className="font-medium text-white/80">
              {bucket[k].toLocaleString()} <span className="text-white/40">({pct(bucket[k])}%)</span>
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
    <div className="bg-[#1a2744] border border-white/10 rounded-xl p-4 animate-pulse h-28" />
  );

  const noData = !data || (data.creator.total === 0 && data.audience.total === 0);
  if (noData) return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl p-4">
      <p className="text-xs text-white/40 text-center py-4">
        No YouTube data yet — enable YouTube monitoring in <strong className="text-white/60">Channel Settings</strong>.
      </p>
    </div>
  );

  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white mb-4">
        YouTube Sentiment — Creator vs Audience
      </h3>

      {/* Two-column sentiment breakdown */}
      <div className="flex gap-6">
        <BucketPanel label="Creator (Videos)"   icon="🎥" bucket={data.creator}  />
        <div className="w-px bg-white/10 shrink-0" />
        <BucketPanel label="Audience (Comments)" icon="💬" bucket={data.audience} />
      </div>

      {/* Divergent videos — only in expanded mode when present */}
      {!compact && data.divergent_videos.length > 0 && (
        <div className="mt-4 border-t border-white/10 pt-3">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-amber-400 text-sm">⚠</span>
            <span className="text-[11px] font-semibold text-amber-400">
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
                  className="flex-1 text-white/70 hover:text-indigo-400 truncate leading-tight"
                  title={v.title}
                >
                  {v.title.length > 65 ? v.title.slice(0, 62) + "…" : v.title}
                </a>
                <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium ${LABEL_COLOR[v.creator_label] ?? "bg-white/10 text-white/50"}`}>
                  {v.creator_label}
                </span>
                <span className="shrink-0 text-white/20">→</span>
                <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium ${LABEL_COLOR[v.audience_label] ?? "bg-white/10 text-white/50"}`}>
                  {v.audience_label}
                </span>
                <span className="shrink-0 text-white/40 whitespace-nowrap">{v.comment_count} comments</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
