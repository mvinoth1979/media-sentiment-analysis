import { useQuery } from "@tanstack/react-query";
import { fetchTopAdvocates } from "../lib/api";
import type { BrandAdvocate } from "../lib/types";

interface Props {
  brandId: string;
  days?: number;
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(Math.round(n));
}

const SOURCE_STYLE: Record<string, { bg: string; text: string }> = {
  YouTube: { bg: "bg-red-500/15",     text: "text-red-400" },
  Blog:    { bg: "bg-emerald-500/15", text: "text-emerald-400" },
  Reddit:  { bg: "bg-orange-500/15",  text: "text-orange-400" },
  Media:   { bg: "bg-blue-500/15",    text: "text-blue-400" },
};

function AdvocateRow({ advocate }: { advocate: BrandAdvocate }) {
  const initial = advocate.name.charAt(0).toUpperCase();
  const style = SOURCE_STYLE[advocate.source_type] ?? SOURCE_STYLE.Media;

  return (
    <div className="flex items-center gap-2.5 py-1.5">
      <div className="w-7 h-7 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
        <span className="text-[11px] font-bold text-emerald-300">{initial}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-medium text-white/80 truncate">{advocate.name}</div>
        <div className="text-[9px] text-white/35">{fmt(advocate.total_reach)} reach · {advocate.article_count} posts</div>
      </div>
      <div className="flex flex-col items-end gap-0.5 shrink-0">
        <span className={`text-[8px] font-semibold px-1.5 py-0.5 rounded-full ${style.bg} ${style.text}`}>
          {advocate.source_type}
        </span>
        <span className="text-[8px] text-emerald-400/70 font-medium">✓ Positive</span>
      </div>
    </div>
  );
}

export function TopBrandAdvocates({ brandId, days = 30 }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["top-advocates", brandId, days],
    queryFn: () => fetchTopAdvocates(brandId, days),
    staleTime: 5 * 60_000,
  });

  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl p-3 min-h-0">
      <div className="flex items-center justify-between mb-2 flex-none">
        <span className="text-[10px] font-semibold text-white/40 uppercase tracking-wider">
          Brand Advocates
        </span>
        <span className="text-[9px] text-emerald-400/60 font-medium">↑ Positive</span>
      </div>

      <div className="flex-1 min-h-0 overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 pt-1">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-8 bg-white/5 rounded-md animate-pulse" />
            ))}
          </div>
        ) : !data?.advocates.length ? (
          <div className="flex items-center justify-center h-full text-[11px] text-white/25">
            No advocates found
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {data.advocates.map(a => (
              <AdvocateRow key={a.name} advocate={a} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
