import type { SourceTypeStat } from "../lib/types";
import { ReviewSitesSummary } from "./ReviewSitesSummary";

interface Props {
  brandId: string;
  bySourceType: Record<string, SourceTypeStat>;
}

function StarRating({ value }: { value: number }) {
  const stars = Math.round(value * 2) / 2;
  return (
    <span className="text-amber-400 text-[11px]">
      {"★".repeat(Math.floor(stars))}{"☆".repeat(5 - Math.floor(stars))}
      <span className="text-white/60 text-[10px] ml-1">{value.toFixed(1)}</span>
    </span>
  );
}

export function ReviewSiteAnalysisPanel({ brandId, bySourceType }: Props) {
  const reviews = bySourceType.google_review ?? { count: 0, delta_pct: null, negative_pct: 0, avg_rating: null };

  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl overflow-hidden min-h-0">
      {/* Header */}
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[9px] text-white/35">Executive Overview</span>
        <span className="text-[9px] text-white/20">›</span>
        <span className="text-[10px] font-semibold text-white/70">Review Site Analysis</span>
        {reviews.delta_pct !== null && (
          <span className={`ml-auto text-[10px] font-semibold ${reviews.delta_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {reviews.delta_pct >= 0 ? "↑" : "↓"}{Math.abs(reviews.delta_pct)}%
          </span>
        )}
      </div>

      {/* KPI strip */}
      <div className="flex items-center gap-4 px-3 py-2 border-b border-white/5 flex-none">
        <div className="flex flex-col">
          <span className="text-[13px] font-bold text-white leading-none">
            {reviews.count >= 1000 ? `${(reviews.count / 1000).toFixed(1)}K` : reviews.count}
          </span>
          <span className="text-[9px] text-white/40 mt-0.5">Total Reviews</span>
        </div>
        <div className="w-px h-6 bg-white/10" />
        {reviews.avg_rating !== null && (
          <>
            <div className="flex flex-col">
              <StarRating value={reviews.avg_rating} />
              <span className="text-[9px] text-white/40 mt-0.5">Avg Rating</span>
            </div>
            <div className="w-px h-6 bg-white/10" />
          </>
        )}
        {reviews.negative_pct !== null && (
          <div className="flex flex-col">
            <span className="text-[13px] font-bold text-red-400 leading-none">{reviews.negative_pct}%</span>
            <span className="text-[9px] text-white/40 mt-0.5">Negative</span>
          </div>
        )}
        <div className="ml-auto text-[9px] text-white/25">Google Reviews</div>
      </div>

      {/* ReviewSitesSummary embedded */}
      <div className="flex-1 min-h-0 overflow-auto p-2">
        <ReviewSitesSummary brandId={brandId} />
      </div>
    </div>
  );
}
