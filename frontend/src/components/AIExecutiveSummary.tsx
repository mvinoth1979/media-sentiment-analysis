import { useQuery } from "@tanstack/react-query";
import { fetchAiSummary } from "../lib/api";

interface Props {
  brandId: string;
  queryParams: { days?: number; date_from?: string; date_to?: string };
}

function Skeleton() {
  return (
    <div className="grid grid-cols-3 gap-4 divide-x divide-white/10 animate-pulse">
      {[...Array(3)].map((_, i) => (
        <div key={i} className={`space-y-1.5 ${i > 0 ? "px-4" : "pr-4"}`}>
          <div className="h-2.5 w-20 bg-white/10 rounded" />
          <div className="h-2 w-full bg-white/6 rounded" />
          <div className="h-2 w-5/6 bg-white/6 rounded" />
          <div className="h-2 w-4/6 bg-white/6 rounded" />
        </div>
      ))}
    </div>
  );
}

export function AIExecutiveSummary({ brandId, queryParams }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["ai-summary", brandId, queryParams],
    queryFn: () => fetchAiSummary(brandId, queryParams),
    staleTime: 30 * 60_000,
    retry: 1,
  });

  return (
    <div className="bg-[#1a2744] border border-white/10 rounded-xl px-4 py-3 flex items-start gap-4 flex-none">
      {/* Left: header + content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-2.5">
          <svg className="w-3.5 h-3.5 text-blue-400 shrink-0" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5L12 2z" />
          </svg>
          <span className="text-[11px] font-semibold text-white/85 tracking-wide">AI Executive Summary</span>
          {data && (
            <span className="ml-auto text-[9px] text-white/25 font-normal">
              {new Date(data.generated_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
        </div>

        {isLoading && <Skeleton />}

        {isError && (
          <p className="text-[10px] text-white/30 italic">AI summary unavailable — pipeline data is being processed.</p>
        )}

        {data && !isLoading && (
          <div className="grid grid-cols-3 gap-0 divide-x divide-white/10">
            <div className="pr-4">
              <div className="text-[9px] font-semibold text-white/40 uppercase tracking-wider mb-1">What changed?</div>
              <p className="text-[11px] text-white/75 leading-relaxed">{data.what_changed}</p>
            </div>
            <div className="px-4">
              <div className="text-[9px] font-semibold text-white/40 uppercase tracking-wider mb-1">Why?</div>
              <p className="text-[11px] text-white/75 leading-relaxed">{data.why}</p>
            </div>
            <div className="pl-4">
              <div className="text-[9px] font-semibold text-white/40 uppercase tracking-wider mb-1">What should we do?</div>
              <ul className="space-y-0.5">
                {data.actions.map((action: string, i: number) => (
                  <li key={i} className="flex items-start gap-1.5 text-[11px] text-white/75">
                    <span className="text-blue-400 mt-0.5 shrink-0 text-[8px]">▸</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Right: CTA button */}
      <button className="text-[10px] text-blue-400 hover:text-blue-300 border border-blue-500/30 hover:border-blue-400/50 rounded-lg px-3 py-1.5 h-fit self-center transition-colors whitespace-nowrap shrink-0">
        View Full Insights →
      </button>
    </div>
  );
}
