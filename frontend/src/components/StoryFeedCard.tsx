import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postStoryAction, type StoryCard } from "../lib/api";

interface Props {
  story: StoryCard;
  brandId: string;
  queryKey: unknown[];
}

const SENTIMENT_COLOR: Record<string, string> = {
  positive: "text-emerald-400 bg-emerald-500/10",
  negative: "text-red-400 bg-red-500/10",
  neutral:  "text-white/40 bg-white/5",
};

const SOURCE_ICON: Record<string, string> = {
  youtube_video:   "▶",
  youtube_comment: "💬",
  google_review:   "⭐",
  reddit:          "🔴",
  news:            "📰",
  rss:             "📰",
  blog:            "✍️",
};

function ImpactBadge({ score }: { score: number }) {
  const color = score >= 70 ? "bg-red-500/20 text-red-300" : score >= 40 ? "bg-amber-500/20 text-amber-300" : "bg-emerald-500/20 text-emerald-300";
  return (
    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${color}`}>
      {score} Impact
    </span>
  );
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const h = Math.floor(diff / 3_600_000);
  if (h < 1) return "just now";
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

const ACTIONS = [
  { key: "investigate", label: "🔍 Investigate", active: "bg-blue-600 text-white", inactive: "text-white/50 border-white/15 hover:border-white/30" },
  { key: "watch",       label: "👁 Watch",        active: "bg-amber-600 text-white", inactive: "text-white/50 border-white/15 hover:border-white/30" },
  { key: "ignore",      label: "✕ Ignore",        active: "bg-white/20 text-white/60", inactive: "text-white/30 border-white/10 hover:border-white/20" },
] as const;

export function StoryFeedCard({ story, brandId, queryKey }: Props) {
  const [localAction, setLocalAction] = useState<string | null>(story.action ?? null);
  const queryClient = useQueryClient();

  const { mutate } = useMutation({
    mutationFn: (action: string) => postStoryAction(brandId, story.article_id, action),
    onMutate: (action) => setLocalAction(prev => prev === action ? null : action),
    onSettled: () => queryClient.invalidateQueries({ queryKey }),
  });

  const handleAction = (action: string) => {
    mutate(localAction === action ? "ignore" : action);
  };

  return (
    <div className="bg-[#1a2744] border border-white/8 rounded-xl p-3 space-y-2 hover:border-white/15 transition-colors">
      {/* Row 1: impact + portal + time + sentiment */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <ImpactBadge score={story.impact_score} />
        <span className="text-[9px] text-white/30 shrink-0">
          {SOURCE_ICON[story.source_type] ?? "📄"} {story.portal_name}
        </span>
        {story.published_at && (
          <span className="text-[9px] text-white/20">{timeAgo(story.published_at)}</span>
        )}
        <span className={`ml-auto text-[9px] px-1.5 py-0.5 rounded-full font-medium ${SENTIMENT_COLOR[story.sentiment_label] ?? SENTIMENT_COLOR.neutral}`}>
          {story.sentiment_label}
        </span>
      </div>

      {/* Row 2: title */}
      <a
        href={story.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block text-[12px] font-medium text-white/90 leading-snug line-clamp-2 hover:text-white transition-colors"
      >
        {story.title}
      </a>

      {/* Row 3: action buttons */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {ACTIONS.map(({ key, label, active, inactive }) => (
          <button
            key={key}
            onClick={() => handleAction(key)}
            className={`text-[10px] border rounded px-2 py-0.5 transition-colors ${localAction === key ? active : `border ${inactive}`}`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
