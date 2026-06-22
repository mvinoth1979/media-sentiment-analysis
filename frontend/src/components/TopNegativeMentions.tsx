import { useQuery } from "@tanstack/react-query";
import { fetchMentions } from "../lib/api";
import type { ArticleItem } from "../lib/types";

interface Props {
  brandId: string;
  days?: number;
}

function timeSince(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const h = Math.floor(diff / 3_600_000);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function ImpactDot({ score }: { score: number }) {
  const abs = Math.abs(score);
  const color = abs > 0.6 ? "bg-red-500" : abs > 0.3 ? "bg-amber-500" : "bg-red-400/50";
  const label = abs > 0.6 ? "High" : abs > 0.3 ? "Med" : "Low";
  return (
    <span className={`flex items-center gap-1 text-[9px] font-semibold text-white/50`}>
      <span className={`w-1.5 h-1.5 rounded-full ${color}`} />
      {label}
    </span>
  );
}

function MentionCard({ article }: { article: ArticleItem }) {
  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-[#0d1626] border border-white/8 rounded-lg px-2.5 py-2 hover:border-red-500/30 transition-colors"
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <span className="text-[9px] font-semibold bg-red-500/15 text-red-400 px-1.5 py-0.5 rounded-full shrink-0">
          Negative
        </span>
        <ImpactDot score={article.sentiment_score} />
      </div>
      <p className="text-[11px] font-medium text-white/80 leading-snug line-clamp-2 mb-1.5">
        {article.title}
      </p>
      <div className="flex items-center gap-1.5 text-[9px] text-white/35">
        <span className="truncate">{article.portal_id}</span>
        <span>·</span>
        <span className="shrink-0">{timeSince(article.published_at)}</span>
      </div>
    </a>
  );
}

export function TopNegativeMentions({ brandId }: Props) {
  const { data: raw, isLoading } = useQuery({
    queryKey: ["top-negative-mentions", brandId],
    queryFn: () => fetchMentions(brandId, { sentiment: "negative", limit: "15" }) as Promise<ArticleItem[]>,
    staleTime: 5 * 60_000,
  });

  const mentions = raw
    ? [...raw].sort((a, b) => a.sentiment_score - b.sentiment_score).slice(0, 3)
    : [];

  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl p-3 min-h-0">
      <div className="flex items-center justify-between mb-2 flex-none">
        <span className="text-[10px] font-semibold text-white/40 uppercase tracking-wider">
          Top Negative Mentions
        </span>
        <span className="text-[9px] text-white/25">by impact</span>
      </div>

      <div className="flex-1 min-h-0 flex flex-col gap-1.5 overflow-hidden">
        {isLoading ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-white/5 rounded-lg animate-pulse" />
          ))
        ) : !mentions.length ? (
          <div className="flex items-center justify-center flex-1 text-[11px] text-white/25">
            No negative mentions
          </div>
        ) : (
          mentions.map(m => <MentionCard key={m.id} article={m} />)
        )}
      </div>
    </div>
  );
}
