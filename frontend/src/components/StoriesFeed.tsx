import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchStoryFeed } from "../lib/api";
import { StoryFeedCard } from "./StoryFeedCard";

interface Props {
  brandId: string;
  days: number;
}

type Filter = "all" | "high" | "investigate" | "watch";

const FILTERS: { key: Filter; label: string }[] = [
  { key: "all",         label: "All" },
  { key: "high",        label: "High Impact" },
  { key: "investigate", label: "Investigate" },
  { key: "watch",       label: "Watching" },
];

function Skeleton() {
  return (
    <div className="space-y-2">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-[#1a2744] border border-white/8 rounded-xl p-3 space-y-2 animate-pulse">
          <div className="flex gap-2">
            <div className="h-4 w-16 bg-white/10 rounded" />
            <div className="h-4 w-24 bg-white/5 rounded" />
          </div>
          <div className="h-3 w-full bg-white/8 rounded" />
          <div className="h-3 w-4/5 bg-white/5 rounded" />
          <div className="flex gap-1.5">
            {[...Array(3)].map((_, j) => <div key={j} className="h-5 w-20 bg-white/5 rounded" />)}
          </div>
        </div>
      ))}
    </div>
  );
}

export function StoriesFeed({ brandId, days }: Props) {
  const [filter, setFilter] = useState<Filter>("all");
  const queryKey = ["story-feed", brandId, days];

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () => fetchStoryFeed(brandId, days),
    staleTime: 5 * 60_000,
    retry: 1,
  });

  const stories = data?.stories ?? [];

  const filtered = stories.filter(s => {
    if (filter === "high") return s.impact_score >= 60;
    if (filter === "investigate") return s.action === "investigate";
    if (filter === "watch") return s.action === "watch";
    return true;
  });

  return (
    <div className="bg-[#111e36] border border-white/10 rounded-xl flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/8 flex-none">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-semibold text-white">Stories That Matter</span>
          {data && <span className="text-[9px] text-white/30">↑ {data.total} sorted by impact</span>}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 px-3 py-1.5 border-b border-white/5 flex-none">
        {FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`text-[9px] px-2 py-0.5 rounded transition-colors ${
              filter === f.key
                ? "bg-blue-600/30 text-blue-300 border border-blue-500/30"
                : "text-white/30 hover:text-white/60"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Story list */}
      <div className="flex-1 min-h-0 overflow-y-auto px-2 py-2 space-y-1.5" style={{ scrollbarWidth: "none" }}>
        {isLoading ? (
          <Skeleton />
        ) : filtered.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-[11px] text-white/25">
              {filter === "all" ? `No stories in the last ${days} days` : `No ${filter} stories`}
            </span>
          </div>
        ) : (
          filtered.map(story => (
            <StoryFeedCard
              key={story.article_id}
              story={story}
              brandId={brandId}
              queryKey={queryKey}
            />
          ))
        )}
      </div>
    </div>
  );
}
