import { useQuery } from "@tanstack/react-query";
import { fetchEmergingTopics } from "../lib/api";

interface Props {
  brandId: string;
  days?: number;
}

export function EmergingNarrativeBanner({ brandId, days = 7 }: Props) {
  const { data } = useQuery({
    queryKey: ["emerging-topics", brandId, days],
    queryFn: () => fetchEmergingTopics(brandId, days),
    staleTime: 15 * 60_000,
    retry: 1,
  });

  const emerging = data?.emerging ?? [];
  if (emerging.length === 0) return null;

  const topTopic = emerging[0];
  const extra = emerging.length - 1;

  return (
    <div className="flex items-start gap-2 bg-amber-500/10 border border-amber-500/25 rounded-lg px-3 py-2">
      <span className="text-amber-400 text-[13px] mt-0.5 flex-none">🧠</span>
      <div className="flex-1 min-w-0">
        <span className="text-[11px] font-semibold text-amber-300">AI discovered new narrative: </span>
        <span className="text-[11px] text-amber-200 font-medium">{topTopic.topic}</span>
        {extra > 0 && (
          <span className="text-[10px] text-amber-400/70"> +{extra} more emerging topic{extra > 1 ? "s" : ""}</span>
        )}
        <div className="text-[9px] text-amber-400/60 mt-0.5">
          {topTopic.novelty_score.toFixed(1)}× above baseline · {topTopic.current_count} mentions in {days}d
        </div>
      </div>
      <div className="text-[9px] text-amber-500/50 flex-none">
        {emerging.map(e => e.topic).slice(0, 3).join(" · ")}
      </div>
    </div>
  );
}
