import { useEffect, useState } from "react";
import { fetchReviewSummary } from "../lib/api";
import type { ReviewSummaryData } from "../lib/types";

interface Props {
  brandId: string;
  compact?: boolean;
  onClick?: () => void;
}

function StarRating({ rating, max = 5 }: { rating: number; max?: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: max }).map((_, i) => (
        <svg
          key={i}
          className={`w-4 h-4 ${i < Math.floor(rating) ? "text-amber-400" : i < rating ? "text-amber-300" : "text-gray-200"}`}
          fill="currentColor" viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
  );
}

const FALLBACK: ReviewSummaryData = {
  total: 0,
  avg_rating: 0,
  distribution: [5, 4, 3, 2, 1].map(s => ({ stars: s, count: 0, pct: 0 })),
  top_positive_topics: [],
  top_negative_topics: [],
};

export function ReviewSitesSummary({ brandId, compact, onClick }: Props) {
  const [data, setData] = useState<ReviewSummaryData>(FALLBACK);
  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  useEffect(() => {
    fetchReviewSummary(brandId)
      .then(setData)
      .catch(() => {/* keep fallback */});
  }, [brandId]);

  const { avg_rating, total, distribution, top_positive_topics, top_negative_topics } = data;
  const ratingLabel = avg_rating.toFixed(1);

  if (compact) {
    return (
      <div onClick={onClick} className={`bg-white border border-gray-200 rounded-lg p-2 shadow-sm h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="flex items-center justify-between mb-1 flex-none">
          <span className="text-[11px] font-semibold text-gray-800">Review Sites</span>
          <div className="flex items-center gap-1">
            <span className="text-base font-bold text-gray-900">{ratingLabel}</span>
            <span className="text-[10px] text-gray-400">/5</span>
            <StarRating rating={avg_rating} />
          </div>
        </div>
        <div className="space-y-0.5 flex-none">
          {distribution.map(d => (
            <div key={d.stars} className="flex items-center gap-1">
              <span className="text-[8px] text-gray-400 w-2 shrink-0">{d.stars}</span>
              <div className="flex-1 h-1 bg-gray-100 rounded-full">
                <div className="h-full bg-amber-400 rounded-full" style={{ width: `${d.pct}%` }} />
              </div>
              <span className="text-[8px] text-gray-400 w-5 text-right">{d.pct}%</span>
            </div>
          ))}
        </div>
        {(top_positive_topics.length > 0 || top_negative_topics.length > 0) && (
          <div className="mt-1.5 flex-1 min-h-0 overflow-hidden space-y-1">
            {top_positive_topics.slice(0, 2).map(t => (
              <div key={t.label} className="flex items-center gap-1 text-[9px]">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 shrink-0" />
                <span className="text-gray-600 truncate flex-1">{t.label}</span>
                <span className="text-green-600 font-semibold shrink-0">{t.pct}%</span>
              </div>
            ))}
            {top_negative_topics.slice(0, 2).map(t => (
              <div key={t.label} className="flex items-center gap-1 text-[9px]">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                <span className="text-gray-600 truncate flex-1">{t.label}</span>
                <span className="text-red-500 font-semibold shrink-0">{t.pct}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div onClick={onClick} className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${clickable}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-800">Review Sites Summary</div>
        <button className="text-[11px] text-blue-600 hover:text-blue-700 font-medium">View All</button>
      </div>

      <div className="flex gap-4 mb-4">
        <div className="shrink-0 text-center">
          <div className="text-3xl font-bold text-gray-900">{ratingLabel}</div>
          <div className="text-xs text-gray-400">/ 5</div>
          <StarRating rating={avg_rating} />
          <div className="text-[10px] text-gray-400 mt-1">
            Based on {total.toLocaleString()} mentions
          </div>
        </div>
        <div className="flex-1 space-y-1">
          <div className="text-[10px] text-gray-400 mb-1.5 font-medium">Rating Distribution</div>
          {distribution.map(d => (
            <div key={d.stars} className="flex items-center gap-1.5">
              <span className="text-[10px] text-gray-500 w-3">{d.stars}</span>
              <div className="flex-1 h-1.5 bg-gray-100 rounded-full">
                <div className="h-full bg-amber-400 rounded-full" style={{ width: `${d.pct}%` }} />
              </div>
              <span className="text-[10px] text-gray-500 w-6 text-right">{d.pct}%</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-[10px] text-green-600 font-semibold uppercase tracking-wide mb-1.5">
            Top Positive Themes
          </div>
          <div className="space-y-1">
            {top_positive_topics.length > 0
              ? top_positive_topics.map(t => (
                  <div key={t.label} className="flex items-center justify-between gap-2">
                    <span className="text-[11px] text-gray-600 truncate">{t.label}</span>
                    <span className="text-[11px] font-semibold text-green-600 shrink-0">{t.pct}%</span>
                  </div>
                ))
              : <span className="text-[10px] text-gray-400">No data yet</span>
            }
          </div>
        </div>
        <div>
          <div className="text-[10px] text-red-500 font-semibold uppercase tracking-wide mb-1.5">
            Top Negative Themes
          </div>
          <div className="space-y-1">
            {top_negative_topics.length > 0
              ? top_negative_topics.map(t => (
                  <div key={t.label} className="flex items-center justify-between gap-2">
                    <span className="text-[11px] text-gray-600 truncate">{t.label}</span>
                    <span className="text-[11px] font-semibold text-red-500 shrink-0">{t.pct}%</span>
                  </div>
                ))
              : <span className="text-[10px] text-gray-400">No data yet</span>
            }
          </div>
        </div>
      </div>
    </div>
  );
}
