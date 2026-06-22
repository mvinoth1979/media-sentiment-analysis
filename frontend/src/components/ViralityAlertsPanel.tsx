import { useQuery } from "@tanstack/react-query";
import { fetchViralityAlerts } from "../lib/api";
import type { ViralityFlag } from "../lib/types";

interface Props {
  brandId: string;
  days?: number;
}

const FLAG_CONFIG = {
  1: { label: "Emerging",   bg: "bg-amber-500/20",  border: "border-amber-500/40",  text: "text-amber-400",  dot: "bg-amber-400"  },
  2: { label: "Risk",       bg: "bg-orange-500/20", border: "border-orange-500/40", text: "text-orange-400", dot: "bg-orange-400" },
  3: { label: "Crisis",     bg: "bg-red-500/20",    border: "border-red-500/40",    text: "text-red-400",    dot: "bg-red-400"    },
} as const;

const METRIC_LABELS: Record<string, string> = {
  view_count:    "Views ↑",
  comment_count: "Comments ↑",
  negative_count: "Negatives ↑",
};

function FlagCard({ flag }: { flag: ViralityFlag }) {
  const cfg = FLAG_CONFIG[flag.flag_level];
  const isAbsolute = flag.history_days === 0;

  return (
    <a
      href={flag.url || undefined}
      target="_blank"
      rel="noopener noreferrer"
      className={`block rounded-md border ${cfg.bg} ${cfg.border} px-2.5 py-2 hover:brightness-110 transition-all cursor-pointer`}
    >
      <div className="flex items-start gap-2">
        <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${cfg.dot}`} />
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium text-white/90 leading-tight line-clamp-2">
            {flag.title || "Untitled video"}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-1">
            <span className={`rounded px-1.5 py-0.5 text-[9px] font-semibold ${cfg.text} ${cfg.bg} border ${cfg.border}`}>
              {cfg.label}
            </span>
            {flag.triggered_metrics.map(m => (
              <span key={m} className="rounded px-1.5 py-0.5 text-[9px] text-white/50 bg-white/5 border border-white/10">
                {METRIC_LABELS[m] ?? m}
              </span>
            ))}
            {isAbsolute && (
              <span className="rounded px-1.5 py-0.5 text-[9px] text-white/30 bg-white/5 border border-white/10">
                Day 0
              </span>
            )}
          </div>
        </div>
      </div>
    </a>
  );
}

export default function ViralityAlertsPanel({ brandId, days = 7 }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["virality-alerts", brandId, days],
    queryFn: () => fetchViralityAlerts(brandId, days),
    refetchInterval: 5 * 60 * 1000,
    staleTime: 4 * 60 * 1000,
  });

  const flags = data?.flags ?? [];
  const crisisCount = flags.filter(f => f.flag_level === 3).length;

  return (
    <div className="h-full flex flex-col bg-[#111827] rounded-xl border border-white/8 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[10px] text-white/40">⚡</span>
        <span className="text-[11px] font-semibold text-white/80">Virality Alerts</span>
        {flags.length > 0 && (
          <span className={`ml-auto rounded-full px-1.5 py-0.5 text-[9px] font-bold ${
            crisisCount > 0 ? "bg-red-500/30 text-red-400" : "bg-amber-500/20 text-amber-400"
          }`}>
            {flags.length}
          </span>
        )}
        <span className="text-[9px] text-white/20 ml-auto">
          {days}d
        </span>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1.5 scrollbar-thin scrollbar-thumb-white/10">
        {isLoading && (
          <div className="flex items-center justify-center h-full">
            <span className="text-[10px] text-white/30 animate-pulse">Loading…</span>
          </div>
        )}
        {isError && (
          <div className="flex items-center justify-center h-full">
            <span className="text-[10px] text-red-400/60">Failed to load alerts</span>
          </div>
        )}
        {!isLoading && !isError && flags.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-1.5 text-center py-4">
            <span className="text-2xl opacity-20">📈</span>
            <span className="text-[10px] text-white/25">No viral activity detected</span>
            <span className="text-[9px] text-white/15">in the last {days} days</span>
          </div>
        )}
        {flags.map(flag => (
          <FlagCard key={flag.article_id} flag={flag} />
        ))}
      </div>
    </div>
  );
}
