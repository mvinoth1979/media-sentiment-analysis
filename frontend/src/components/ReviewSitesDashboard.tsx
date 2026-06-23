import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchReviewSitesBreakdown, fetchMentions } from "../lib/api";
import type { ReviewPlatformStat, ArticleItem } from "../lib/types";

const PLATFORM_NAMES: Record<string, string> = {
  google_review:     "Google Reviews",
  trustpilot_review: "Trustpilot",
  mouthshut_review:  "MouthShut",
  justdial_review:   "JustDial",
  ambitionbox_review:"AmbitionBox",
  tripadvisor_review:"TripAdvisor",
  team_bhp_review:   "Team-BHP",
  amazon_review:     "Amazon",
  flipkart_review:   "Flipkart",
  indiamart_review:  "IndiaMART",
  glassdoor_review:  "Glassdoor",
};

const PLATFORM_ICON: Record<string, string> = {
  google_review:     "⭐",
  trustpilot_review: "🟢",
  mouthshut_review:  "💬",
  justdial_review:   "📞",
  ambitionbox_review:"💼",
  tripadvisor_review:"✈️",
  team_bhp_review:   "🚗",
  amazon_review:     "📦",
  flipkart_review:   "🛒",
  indiamart_review:  "🏭",
  glassdoor_review:  "🏢",
};

function Stars({ rating, size = "sm" }: { rating: number; size?: "sm" | "md" }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  const cls = size === "sm" ? "text-[9px]" : "text-[12px]";
  return (
    <span className={`text-amber-400 ${cls} leading-none`}>
      {"★".repeat(full)}{half ? "½" : ""}{"☆".repeat(empty)}
    </span>
  );
}

function PlatformCard({ p, active, onClick }: { p: ReviewPlatformStat; active: boolean; onClick: () => void }) {
  const sentColor = p.negative_pct > 40
    ? "text-red-400"
    : p.positive_pct > 60
    ? "text-emerald-400"
    : "text-amber-400";

  return (
    <button
      onClick={onClick}
      className={`flex flex-col gap-1 p-2.5 rounded-xl border transition-all text-left w-full ${
        active
          ? "bg-blue-600/20 border-blue-500/50"
          : "bg-[#0f1c35] border-white/8 hover:border-white/20 hover:bg-white/5"
      }`}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-base leading-none">{PLATFORM_ICON[p.source_type] ?? "📋"}</span>
        <span className="text-[10px] font-semibold text-white/80 truncate flex-1">{p.platform_name}</span>
        <span className="text-[9px] font-bold text-white/50 shrink-0">{p.count}</span>
      </div>

      {p.avg_rating !== null && (
        <div className="flex items-center gap-1">
          <Stars rating={p.avg_rating} />
          <span className="text-[9px] text-white/50">{p.avg_rating.toFixed(1)}</span>
        </div>
      )}

      {/* Sentiment bar */}
      <div className="h-1 rounded-full bg-white/8 overflow-hidden flex">
        <div className="h-full bg-emerald-500" style={{ width: `${p.positive_pct}%` }} />
        <div className="h-full bg-slate-500" style={{ width: `${100 - p.positive_pct - p.negative_pct}%` }} />
        <div className="h-full bg-red-500" style={{ width: `${p.negative_pct}%` }} />
      </div>

      <span className={`text-[9px] font-semibold ${sentColor}`}>
        {p.positive_pct > p.negative_pct
          ? `${p.positive_pct}% positive`
          : `${p.negative_pct}% negative`}
      </span>
    </button>
  );
}

function ReviewFeed({
  brandId,
  sourceType,
  onReviewClick,
}: {
  brandId: string;
  sourceType: string | null;
  onReviewClick: (item: ArticleItem) => void;
}) {
  const params: Record<string, string> = { limit: "20", source_category: "review_site" };
  if (sourceType) params.source_type = sourceType;

  const { data: items = [], isLoading } = useQuery<ArticleItem[]>({
    queryKey: ["review-feed", brandId, sourceType],
    queryFn: () => fetchMentions(brandId, params),
    staleTime: 5 * 60_000,
  });

  if (isLoading) return (
    <div className="flex items-center justify-center h-16 text-white/30 text-xs">Loading…</div>
  );
  if (items.length === 0) return (
    <div className="flex items-center justify-center h-16 text-white/30 text-xs">
      No reviews collected yet — pipeline runs hourly.
    </div>
  );

  return (
    <div className="space-y-0.5 overflow-y-auto flex-1 min-h-0 pr-0.5" style={{ scrollbarWidth: "none" }}>
      {items.map(item => {
        const label = item.sentiment_label;
        const dotColor = label === "positive" ? "bg-emerald-500" : label === "negative" ? "bg-red-500" : "bg-slate-400";
        const date = item.published_at ? new Date(item.published_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "";
        const icon = PLATFORM_ICON[item.source_type ?? ""] ?? "📋";
        const rating = item.reach_metadata?.rating;
        const platformName = PLATFORM_NAMES[item.source_type ?? ""] ?? (item.source_type ?? "Review");

        return (
          <div
            key={item.id}
            onClick={() => onReviewClick(item)}
            className="flex items-start gap-2 p-1.5 rounded-lg hover:bg-white/5 transition-colors group cursor-pointer"
          >
            <span className={`w-1.5 h-1.5 rounded-full mt-1 shrink-0 ${dotColor}`} />
            <div className="flex-1 min-w-0">
              <p className="text-[11px] text-white/70 leading-snug line-clamp-2 group-hover:text-white/90 transition-colors">
                {item.title}
              </p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="text-[9px]">{icon}</span>
                <span className="text-[9px] text-white/35">{platformName}</span>
                {rating && <span className="text-[9px] text-amber-400">{"★".repeat(Math.round(Number(rating)))}</span>}
                {date && <span className="text-[9px] text-white/25">{date}</span>}
              </div>
            </div>
            <span className="text-[9px] text-white/20 group-hover:text-white/40 shrink-0 self-center">›</span>
          </div>
        );
      })}
    </div>
  );
}

function ReviewDetail({ item, onBack }: { item: ArticleItem; onBack: () => void }) {
  const label = item.sentiment_label ?? "neutral";
  const sentBg = label === "positive" ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
    : label === "negative" ? "bg-red-500/15 text-red-400 border-red-500/30"
    : "bg-slate-500/15 text-slate-400 border-slate-500/30";
  const rating = item.reach_metadata?.rating ? Math.round(Number(item.reach_metadata.rating)) : null;
  const platformName = PLATFORM_NAMES[item.source_type ?? ""] ?? (item.source_type ?? "Review");
  const icon = PLATFORM_ICON[item.source_type ?? ""] ?? "📋";
  const date = item.published_at
    ? new Date(item.published_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })
    : "";

  return (
    <div className="flex flex-col gap-3 flex-1 min-h-0 overflow-y-auto pr-0.5" style={{ scrollbarWidth: "none" }}>
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-[10px] text-white/40 hover:text-white/70 transition-colors self-start"
      >
        ← back to feed
      </button>

      {/* Platform + rating */}
      <div className="flex items-center gap-2">
        <span className="text-xl">{icon}</span>
        <div>
          <div className="text-[10px] font-semibold text-white/70">{platformName}</div>
          {rating !== null && (
            <div className="flex items-center gap-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <span key={i} className={`text-[14px] ${i < rating ? "text-amber-400" : "text-white/15"}`}>★</span>
              ))}
              <span className="text-[9px] text-white/40 ml-0.5">{rating}/5</span>
            </div>
          )}
        </div>
        <div className="ml-auto flex flex-col items-end gap-1">
          <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${sentBg}`}>
            {label}
          </span>
          {item.sentiment_score !== null && item.sentiment_score !== undefined && (
            <span className="text-[9px] text-white/30">score {item.sentiment_score.toFixed(2)}</span>
          )}
        </div>
      </div>

      {/* Review text */}
      <div className="bg-[#0f1c35] border border-white/8 rounded-xl p-3">
        <p className="text-[12px] text-white/80 leading-relaxed whitespace-pre-line">{item.title}</p>
      </div>

      {/* Metadata row */}
      <div className="flex flex-wrap gap-2 text-[10px] text-white/40">
        {item.author && <span>by <span className="text-white/60">{item.author}</span></span>}
        {date && <span>{date}</span>}
        {item.issue_category && item.issue_category !== "other" && (
          <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/8 text-white/50">
            {item.issue_category.replace(/_/g, " ")}
          </span>
        )}
        {item.editorial_tone && (
          <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/8 text-white/50">
            {item.editorial_tone}
          </span>
        )}
      </div>

      {/* Original link */}
      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="self-start text-[10px] text-blue-400/70 hover:text-blue-300 border border-blue-400/20 hover:border-blue-400/40 rounded px-2 py-1 transition-colors"
        >
          View original review ↗
        </a>
      )}
    </div>
  );
}

interface Props {
  brandId: string;
  days: number;
}

export function ReviewSitesDashboard({ brandId, days }: Props) {
  const [activePlatform, setActivePlatform] = useState<string | null>(null);
  const [activeReview, setActiveReview] = useState<ArticleItem | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["review-sites-breakdown", brandId, days],
    queryFn: () => fetchReviewSitesBreakdown(brandId, { days }),
    staleTime: 5 * 60_000,
  });

  const platforms = data?.platforms ?? [];
  const total = data?.total_reviews ?? 0;
  const overallRating = data?.overall_avg_rating ?? null;

  const best = platforms.reduce<ReviewPlatformStat | null>(
    (b, p) => (p.avg_rating !== null && (b === null || (p.avg_rating ?? 0) > (b.avg_rating ?? 0)) ? p : b), null
  );
  const worst = platforms.reduce<ReviewPlatformStat | null>(
    (w, p) => (p.negative_pct > (w?.negative_pct ?? 0) ? p : w), null
  );

  const activeSource = activePlatform;

  // clear active review when platform filter changes
  const handlePlatformChange = (platform: string | null) => {
    setActivePlatform(p => p === platform ? null : platform);
    setActiveReview(null);
  };

  return (
    <div className="h-full flex flex-col bg-[#0d1626] overflow-hidden">

      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[#1a2744] border-b border-white/10 flex-none">
        <span className="text-sm font-semibold text-white">Review Sites Intelligence</span>
        <span className="text-[10px] text-white/30 ml-1">— last {days} days</span>
        <div className="ml-auto flex items-center gap-3 text-[10px] text-white/40">
          <span>{total.toLocaleString()} reviews</span>
          {overallRating !== null && (
            <span className="flex items-center gap-1">
              <Stars rating={overallRating} size="sm" />
              <span className="text-white/60 font-semibold">{overallRating.toFixed(1)}</span>
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-1 min-h-0 gap-0">

        {/* ── Left: KPI + Platform cards ────────────────────── */}
        <div className="flex flex-col gap-2 p-3 w-[52%] min-w-0 border-r border-white/8">

          {/* Summary KPI strip */}
          <div className="grid grid-cols-3 gap-2 flex-none">
            <div className="bg-[#0f1c35] border border-white/8 rounded-xl px-3 py-2 flex flex-col gap-0.5">
              <span className="text-[8px] uppercase tracking-wider text-white/35 font-medium">Total Reviews</span>
              <span className="text-lg font-bold text-white leading-none">
                {total >= 1000 ? `${(total / 1000).toFixed(1)}K` : total}
              </span>
              <span className="text-[9px] text-white/40">{platforms.length} platforms</span>
            </div>
            <div className="bg-[#0f1c35] border border-white/8 rounded-xl px-3 py-2 flex flex-col gap-0.5">
              <span className="text-[8px] uppercase tracking-wider text-white/35 font-medium">Overall Rating</span>
              {overallRating !== null ? (
                <>
                  <span className="text-lg font-bold text-amber-400 leading-none">{overallRating.toFixed(1)}</span>
                  <Stars rating={overallRating} size="sm" />
                </>
              ) : (
                <span className="text-[10px] text-white/25 mt-1">No data</span>
              )}
            </div>
            <div className="bg-[#0f1c35] border border-white/8 rounded-xl px-3 py-2 flex flex-col gap-0.5">
              <span className="text-[8px] uppercase tracking-wider text-white/35 font-medium">Needs Attention</span>
              {worst && worst.negative_pct > 20 ? (
                <>
                  <span className="text-[11px] font-semibold text-red-400 leading-snug truncate">{worst.platform_name}</span>
                  <span className="text-[9px] text-red-400/70">{worst.negative_pct}% negative</span>
                </>
              ) : (
                <span className="text-[10px] text-emerald-400 mt-1">All healthy</span>
              )}
            </div>
          </div>

          {/* Platform grid */}
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center text-white/30 text-xs">Loading platforms…</div>
          ) : platforms.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 p-4">
              <span className="text-2xl">⭐</span>
              <p className="text-[11px] text-white/40">No reviews collected yet</p>
              <p className="text-[10px] text-white/25">Enable review site channels in Brand Settings and wait for the next pipeline run.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-1.5 flex-1 content-start overflow-y-auto" style={{ scrollbarWidth: "none" }}>
              {/* "All platforms" filter chip */}
              <button
                onClick={() => handlePlatformChange(null)}
                className={`col-span-2 text-[9px] font-medium px-2 py-1 rounded-lg border transition-all ${
                  activePlatform === null
                    ? "bg-blue-600/20 border-blue-500/50 text-blue-300"
                    : "border-white/10 text-white/40 hover:border-white/20"
                }`}
              >
                All Platforms ({total.toLocaleString()} reviews)
              </button>
              {platforms.map(p => (
                <PlatformCard
                  key={p.source_type}
                  p={p}
                  active={activePlatform === p.source_type}
                  onClick={() => handlePlatformChange(p.source_type)}
                />
              ))}
            </div>
          )}
        </div>

        {/* ── Right: Review feed / Detail ──────────────────── */}
        <div className="flex flex-col flex-1 min-w-0 p-3 gap-2 min-h-0">
          {activeReview ? (
            <ReviewDetail item={activeReview} onBack={() => setActiveReview(null)} />
          ) : (
            <>
              <div className="flex items-center gap-2 flex-none">
                <span className="text-[10px] font-semibold text-white/60">
                  {activePlatform
                    ? (platforms.find(p => p.source_type === activePlatform)?.platform_name ?? activePlatform)
                    : "All Reviews"}
                </span>
                {activePlatform && (
                  <button
                    onClick={() => handlePlatformChange(null)}
                    className="text-[9px] text-white/30 hover:text-white/60 ml-auto"
                  >
                    ✕ clear filter
                  </button>
                )}
              </div>

              {/* Best platform spotlight — only when viewing all */}
              {!activePlatform && best && (
                <div className="flex-none bg-emerald-900/20 border border-emerald-500/20 rounded-xl px-3 py-2 flex items-center gap-3">
                  <span className="text-xl">{PLATFORM_ICON[best.source_type] ?? "⭐"}</span>
                  <div>
                    <div className="text-[9px] text-emerald-400 font-semibold uppercase tracking-wider">Best Rated</div>
                    <div className="text-[11px] text-white/80 font-medium">{best.platform_name}</div>
                    {best.avg_rating !== null && (
                      <div className="flex items-center gap-1 mt-0.5">
                        <Stars rating={best.avg_rating} size="sm" />
                        <span className="text-[9px] text-amber-400">{best.avg_rating.toFixed(1)}</span>
                        <span className="text-[9px] text-white/35">· {best.count} reviews</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <ReviewFeed brandId={brandId} sourceType={activeSource} onReviewClick={setActiveReview} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
