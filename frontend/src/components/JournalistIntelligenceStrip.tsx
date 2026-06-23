import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchJournalistCoverage } from "../lib/api";
import type { JournalistProfile } from "../lib/types";

interface Props {
  brandId: string;
  days?: number;
  onJournalistDrill?: (author: string) => void;
}

function stanceLabel(j: JournalistProfile): { label: string; color: string } {
  if (j.negative_pct >= 60) return { label: "Critical", color: "text-red-400" };
  if (j.negative_pct >= 30) return { label: "Mixed",    color: "text-amber-400" };
  if (j.positive_count / j.total_articles > 0.5) return { label: "Positive", color: "text-emerald-400" };
  return { label: "Neutral", color: "text-white/40" };
}

function timeAgo(iso: string): string {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  return d === 0 ? "Today" : d === 1 ? "Yesterday" : `${d}d ago`;
}

function OutreachModal({ author, onClose }: { author: string; onClose: () => void }) {
  const [sent, setSent] = useState(false);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-[#0d1626] border border-white/15 rounded-xl p-5 w-72 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="text-[11px] font-semibold text-white mb-3">Outreach — {author}</div>
        {sent ? (
          <div className="text-center py-4">
            <div className="text-emerald-400 text-2xl mb-2">✓</div>
            <p className="text-[11px] text-white/60">Engagement noted. Team will follow up.</p>
            <button onClick={onClose} className="mt-3 text-[10px] text-white/40 hover:text-white/70">Close</button>
          </div>
        ) : (
          <>
            <div className="space-y-2 mb-4">
              {["Brief for product review", "Request media interview", "Add to press list", "Monitor activity"].map(action => (
                <button
                  key={action}
                  onClick={() => setSent(true)}
                  className="w-full text-left text-[10px] text-white/60 hover:text-white border border-white/10 hover:border-white/25 rounded-lg px-3 py-2 transition-colors"
                >
                  {action}
                </button>
              ))}
            </div>
            <button onClick={onClose} className="text-[9px] text-white/25 hover:text-white/50">Cancel</button>
          </>
        )}
      </div>
    </div>
  );
}

function JournalistRow({ j, onDrill, onEngage }: {
  j: JournalistProfile;
  onDrill?: (a: string) => void;
  onEngage: (a: string) => void;
}) {
  const { label, color } = stanceLabel(j);
  const posPct = j.total_articles ? Math.round((j.positive_count / j.total_articles) * 100) : 0;
  const negPct = j.negative_pct;
  const neuPct = 100 - posPct - negPct;

  return (
    <div className="flex items-center gap-2 py-1.5 border-b border-white/5 last:border-0">
      {/* Avatar */}
      <div className="w-6 h-6 rounded-full bg-blue-500/15 flex items-center justify-center shrink-0 text-[10px] font-bold text-blue-300">
        {j.author.charAt(0).toUpperCase()}
      </div>

      {/* Name + meta */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <button
            onClick={() => onDrill?.(j.author)}
            className="text-[10px] font-medium text-white/75 hover:text-white truncate max-w-[120px] transition-colors text-left"
          >
            {j.author}
          </button>
          <span className={`text-[8px] font-semibold ${color}`}>{label}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-1 w-20 bg-white/8 rounded-full overflow-hidden flex">
            <div className="bg-emerald-500/70" style={{ width: `${posPct}%` }} />
            <div className="bg-white/15"        style={{ width: `${neuPct}%` }} />
            <div className="bg-red-500/70"      style={{ width: `${negPct}%` }} />
          </div>
          <span className="text-[8px] text-white/25">{j.total_articles} · {timeAgo(j.last_article_at)}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-1 shrink-0">
        <button
          onClick={() => onEngage(j.author)}
          className="text-[8px] border border-blue-500/25 text-blue-400/70 hover:text-blue-400 hover:border-blue-400/50 rounded px-1.5 py-0.5 transition-colors"
        >
          Engage
        </button>
        <button
          onClick={() => onDrill?.(j.author)}
          className="text-[8px] border border-white/10 text-white/30 hover:text-white/60 hover:border-white/25 rounded px-1.5 py-0.5 transition-colors"
        >
          View
        </button>
      </div>
    </div>
  );
}

export function JournalistIntelligenceStrip({ brandId, days = 30, onJournalistDrill }: Props) {
  const [engageTarget, setEngageTarget] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["journalist-coverage", brandId, days],
    queryFn: () => fetchJournalistCoverage(brandId, days),
    staleTime: 15 * 60_000,
    retry: 1,
  });

  const journalists = data?.journalists?.slice(0, 6) ?? [];

  return (
    <div className="bg-[#111e36] border border-white/10 rounded-xl flex flex-col overflow-hidden h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[11px] font-semibold text-white">Journalist Intelligence</span>
        <span className="text-[9px] text-white/30 ml-auto">{data?.journalists?.length ?? 0} journalists · {days}d</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-1" style={{ scrollbarWidth: "none" }}>
        {isLoading && (
          <div className="space-y-2 py-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-9 bg-white/5 rounded animate-pulse" />
            ))}
          </div>
        )}
        {!isLoading && journalists.length === 0 && (
          <div className="flex items-center justify-center h-full text-[10px] text-white/25 py-6">
            No journalist data for this period
          </div>
        )}
        {journalists.map(j => (
          <JournalistRow
            key={j.author}
            j={j}
            onDrill={onJournalistDrill}
            onEngage={setEngageTarget}
          />
        ))}
      </div>

      {engageTarget && (
        <OutreachModal author={engageTarget} onClose={() => setEngageTarget(null)} />
      )}
    </div>
  );
}
