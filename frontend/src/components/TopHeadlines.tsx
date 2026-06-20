import { useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { fetchHeadlines } from "../lib/api";
import type { HeadlineItem } from "../lib/types";
import { sentimentIntensity, tierBadge, reachBadge } from "../lib/utils";
import { YouTubeIcon } from "./ui/YouTubeIcon";

type HeadlineTab = "positive" | "negative" | "trending";

interface Props {
  brandId: string;
  dateFrom?: string;
  dateTo?: string;
  onViewAll?: (tab: HeadlineTab) => void;
}

const TABS: { key: HeadlineTab; label: string }[] = [
  { key: "positive", label: "Top Positive" },
  { key: "negative", label: "Top Negative" },
  { key: "trending", label: "Trending"     },
];

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function HeadlineCard({ item }: { item: HeadlineItem }) {
  const intensity = sentimentIntensity(item.sentiment_label, item.sentiment_score);
  const tb = tierBadge(item.source_tier);
  const isYouTube = item.portal_category === "youtube";

  return (
    <div className="flex gap-2.5 py-2.5 border-b border-gray-800/60 last:border-0">
      {/* Avatar */}
      <div className={`w-7 h-7 rounded shrink-0 flex items-center justify-center text-[10px] font-bold mt-0.5 ${
        isYouTube ? "bg-red-900/40" : "bg-indigo-900/30"
      }`}>
        {isYouTube
          ? <YouTubeIcon className="w-4 h-4" />
          : <span className="text-indigo-300">{item.portal_name.charAt(0).toUpperCase()}</span>
        }
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1">
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-gray-200 hover:text-indigo-300 line-clamp-2 leading-tight transition-colors"
        >
          {item.title}
        </a>

        {/* Badge row */}
        <div className="flex flex-wrap items-center gap-1">
          <span className={`text-[9px] px-1.5 py-0.5 rounded border border-current/20 ${intensity.bg} ${intensity.color}`}>
            {item.sentiment_intensity}
          </span>
          {item.source_tier > 0 && (
            <span className={`text-[9px] px-1 rounded ${tb.bg} ${tb.color}`}>
              {tb.label}
            </span>
          )}
          {item.reach_tier && item.reach_tier !== "Low" && (
            <span className={`text-[9px] font-medium ${reachBadge(item.reach_tier).color}`}>
              {reachBadge(item.reach_tier).label}
            </span>
          )}
          {item.repeat_author && (
            <span
              title={`${item.author_name ?? "This author"} has multiple negative articles about this brand`}
              className="text-[9px] text-orange-400 border border-orange-800/50 px-1 rounded"
            >
              ⚠ Repeat critic
            </span>
          )}
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-1.5 text-[10px] text-gray-500">
          <span className="truncate max-w-[100px]">{item.portal_name}</span>
          {item.language !== "en" && (
            <span className="uppercase font-mono text-gray-600">{item.language}</span>
          )}
          <span>·</span>
          <span>{timeAgo(item.collected_at ?? item.published_at)}</span>
        </div>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="flex gap-2.5 py-2.5 border-b border-gray-800/60 last:border-0 animate-pulse">
      <div className="w-7 h-7 rounded bg-gray-800 shrink-0 mt-0.5" />
      <div className="flex-1 space-y-1.5">
        <div className="h-3 bg-gray-800 rounded w-full" />
        <div className="h-3 bg-gray-800 rounded w-4/5" />
        <div className="flex gap-1">
          <div className="h-3 w-16 bg-gray-800 rounded" />
          <div className="h-3 w-10 bg-gray-800 rounded" />
        </div>
        <div className="h-2.5 bg-gray-800 rounded w-24" />
      </div>
    </div>
  );
}

export function TopHeadlines({ brandId, dateFrom, dateTo, onViewAll }: Props) {
  const [activeTab, setActiveTab] = useState<HeadlineTab>("positive");

  const { data, isLoading } = useQuery({
    queryKey: ["headlines", brandId, activeTab, dateFrom, dateTo],
    queryFn: () => fetchHeadlines(brandId, activeTab, { limit: 5, date_from: dateFrom, date_to: dateTo }),
    staleTime: 5 * 60_000,
    placeholderData: keepPreviousData,
  });

  const items = data?.items ?? [];

  // Split YouTube items for Trending tab (Creator vs Audience grouping)
  const videoItems = items.filter(i => i.source_type === "youtube_video");
  const commentItems = items.filter(i => i.source_type === "youtube_comment");
  const newsItems = items.filter(i => !i.source_type.startsWith("youtube_"));
  const hasYouTubeGroups =
    activeTab === "trending" && (videoItems.length > 0 || commentItems.length > 0);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-200">Top Headlines</div>
        {onViewAll && (
          <button
            onClick={() => onViewAll(activeTab)}
            className="text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            View all →
          </button>
        )}
      </div>

      {/* Tab bar */}
      <div className="flex gap-0 border border-gray-700/60 rounded-lg p-0.5 mb-3">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex-1 text-[10px] py-1 rounded-md transition-colors ${
              activeTab === t.key
                ? "bg-gray-700 text-gray-100"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)
        ) : items.length === 0 ? (
          <div className="py-8 text-center text-gray-600 text-xs">
            No {activeTab} headlines found.
          </div>
        ) : hasYouTubeGroups ? (
          <>
            {newsItems.length > 0 && newsItems.map(item => <HeadlineCard key={item.id} item={item} />)}
            {videoItems.length > 0 && (
              <>
                <div className="text-[10px] text-gray-600 uppercase tracking-wider mt-2 mb-1">
                  Creator (Videos)
                </div>
                {videoItems.map(item => <HeadlineCard key={item.id} item={item} />)}
              </>
            )}
            {commentItems.length > 0 && (
              <>
                <div className="text-[10px] text-gray-600 uppercase tracking-wider mt-2 mb-1">
                  Audience (Comments)
                </div>
                {commentItems.map(item => <HeadlineCard key={item.id} item={item} />)}
              </>
            )}
          </>
        ) : (
          items.map(item => <HeadlineCard key={item.id} item={item} />)
        )}
      </div>
    </div>
  );
}
