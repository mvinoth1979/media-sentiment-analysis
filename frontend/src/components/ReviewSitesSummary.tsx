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

const DISTRIBUTION = [
  { stars: 5, pct: 55 },
  { stars: 4, pct: 24 },
  { stars: 3, pct: 12 },
  { stars: 2, pct: 5 },
  { stars: 1, pct: 4 },
];

const POS_THEMES = [
  { label: "Quality of Training", pct: 32 },
  { label: "Faculty Support", pct: 28 },
  { label: "Infrastructure", pct: 18 },
  { label: "Placement Support", pct: 15 },
  { label: "Overall Experience", pct: 11 },
];

const NEG_THEMES = [
  { label: "Placement Opportunities", pct: 35 },
  { label: "Communication", pct: 22 },
  { label: "Course Fees", pct: 18 },
  { label: "Infrastructure Issues", pct: 15 },
  { label: "Administrative Issues", pct: 10 },
];

export function ReviewSitesSummary({ brandId: _, compact, onClick }: Props) {
  const clickable = onClick ? "cursor-pointer hover:border-blue-300 transition-colors" : "";

  if (compact) {
    return (
      <div onClick={onClick} className={`bg-white border border-gray-200 rounded-lg p-2 shadow-sm h-full flex flex-col overflow-hidden ${clickable}`}>
        <div className="flex items-center justify-between mb-1 flex-none">
          <span className="text-[11px] font-semibold text-gray-800">Review Sites</span>
          <div className="flex items-center gap-1">
            <span className="text-base font-bold text-gray-900">4.1</span>
            <span className="text-[10px] text-gray-400">/5</span>
          </div>
        </div>
        <div className="flex-1 min-h-0 space-y-0.5 overflow-hidden">
          {DISTRIBUTION.map(d => (
            <div key={d.stars} className="flex items-center gap-1">
              <span className="text-[8px] text-gray-400 w-2 shrink-0">{d.stars}</span>
              <div className="flex-1 h-1 bg-gray-100 rounded-full">
                <div className="h-full bg-amber-400 rounded-full" style={{ width: `${d.pct}%` }} />
              </div>
              <span className="text-[8px] text-gray-400 w-5 text-right">{d.pct}%</span>
            </div>
          ))}
        </div>
        <div className="mt-1 flex-none">
          <StarRating rating={4.1} />
        </div>
      </div>
    );
  }

  return (
    <div onClick={onClick} className={`bg-white border border-gray-200 rounded-xl p-4 shadow-sm ${clickable}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-800">Review Sites Summary</div>
        <button className="text-[11px] text-blue-600 hover:text-blue-700 font-medium">View All</button>
      </div>

      {/* Rating + distribution */}
      <div className="flex gap-4 mb-4">
        <div className="shrink-0 text-center">
          <div className="text-3xl font-bold text-gray-900">4.1</div>
          <div className="text-xs text-gray-400">/ 5</div>
          <StarRating rating={4.1} />
          <div className="text-[10px] text-gray-400 mt-1">Based on 3,842 reviews</div>
        </div>
        <div className="flex-1 space-y-1">
          <div className="text-[10px] text-gray-400 mb-1.5 font-medium">Rating Distribution</div>
          {DISTRIBUTION.map(d => (
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

      {/* Themes */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-[10px] text-green-600 font-semibold uppercase tracking-wide mb-1.5">
            Top Positive Themes
          </div>
          <div className="space-y-1">
            {POS_THEMES.map(t => (
              <div key={t.label} className="flex items-center justify-between gap-2">
                <span className="text-[11px] text-gray-600 truncate">{t.label}</span>
                <span className="text-[11px] font-semibold text-green-600 shrink-0">{t.pct}%</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[10px] text-red-500 font-semibold uppercase tracking-wide mb-1.5">
            Top Negative Themes
          </div>
          <div className="space-y-1">
            {NEG_THEMES.map(t => (
              <div key={t.label} className="flex items-center justify-between gap-2">
                <span className="text-[11px] text-gray-600 truncate">{t.label}</span>
                <span className="text-[11px] font-semibold text-red-500 shrink-0">{t.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
