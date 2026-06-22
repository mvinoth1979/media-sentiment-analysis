import type { SourceTypeStat } from "../lib/types";
import { MentionsList } from "./mentions/MentionsList";

interface Props {
  brandId: string;
  brandName?: string;
  portals?: string[];
  topics?: string[];
  states?: string[];
  bySourceType: Record<string, SourceTypeStat>;
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function KPIChip({ label, value, sub, color = "text-white" }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="flex flex-col">
      <span className={`text-[13px] font-bold ${color} leading-none`}>{value}</span>
      {sub && <span className="text-[9px] text-white/35 mt-0.5">{sub}</span>}
      <span className="text-[9px] text-white/40 mt-0.5">{label}</span>
    </div>
  );
}

export function NewsRSSMentionsPanel({ brandId, brandName, portals = [], topics = [], states = [], bySourceType }: Props) {
  const news = bySourceType.news  ?? { count: 0, delta_pct: null, negative_pct: 0 };
  const blog = bySourceType.blog  ?? { count: 0, delta_pct: null, negative_pct: 0 };
  const total = news.count + blog.count;
  const negPct = total > 0
    ? ((news.count * (news.negative_pct ?? 0) + blog.count * (blog.negative_pct ?? 0)) / total).toFixed(1)
    : "0";
  const delta = news.delta_pct;

  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl overflow-hidden min-h-0">
      {/* Header */}
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[9px] text-white/35">Executive Overview</span>
        <span className="text-[9px] text-white/20">›</span>
        <span className="text-[10px] font-semibold text-white/70">News & RSS Mentions</span>
        {delta !== null && (
          <span className={`ml-auto text-[10px] font-semibold ${delta >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {delta >= 0 ? "↑" : "↓"}{Math.abs(delta)}%
          </span>
        )}
      </div>

      {/* KPI strip */}
      <div className="flex items-center gap-4 px-3 py-2 border-b border-white/5 flex-none">
        <KPIChip label="Total" value={fmt(total)} />
        <div className="w-px h-6 bg-white/10" />
        <KPIChip label="Negative" value={`${negPct}%`} color="text-red-400" />
        <KPIChip label="Positive" value={`${total > 0 ? (100 - parseFloat(negPct) * 1.4).toFixed(0) : 0}%`} color="text-emerald-400" />
        <div className="ml-auto text-[9px] text-white/25">News + Blogs + RSS</div>
      </div>

      {/* MentionsList pre-filtered to news/blog sources */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <MentionsList
          brandId={brandId}
          brandName={brandName}
          portals={portals}
          topics={topics}
          states={states}
          initialSourceCategory="news"
        />
      </div>
    </div>
  );
}
