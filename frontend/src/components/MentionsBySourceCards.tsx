import type { SourceTypeStat } from "../lib/types";

interface Props {
  data: Record<string, SourceTypeStat>;
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function DeltaBadge({ pct }: { pct: number | null }) {
  if (pct === null) return null;
  const up = pct >= 0;
  return (
    <span className={`text-[10px] font-semibold ${up ? "text-emerald-400" : "text-red-400"}`}>
      {up ? "↑" : "↓"}{Math.abs(pct)}%
    </span>
  );
}

interface CardDef {
  key: string;
  label: string;
  icon: React.ReactNode;
  accent: string;
}

function NewsIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
    </svg>
  );
}

function YoutubeIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function BlogIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  );
}

function StarIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
    </svg>
  );
}

function ForumIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
    </svg>
  );
}

const CARDS: CardDef[] = [
  { key: "news",         label: "News & RSS",     icon: <NewsIcon />,    accent: "text-red-400 bg-red-500/10" },
  { key: "youtube",      label: "YouTube",         icon: <YoutubeIcon />, accent: "text-red-500 bg-red-600/10" },
  { key: "blog",         label: "Blogs & Portals", icon: <BlogIcon />,    accent: "text-emerald-400 bg-emerald-500/10" },
  { key: "google_review",label: "Review Sites",    icon: <StarIcon />,    accent: "text-amber-400 bg-amber-500/10" },
  { key: "reddit_post",  label: "Forums",          icon: <ForumIcon />,   accent: "text-indigo-400 bg-indigo-500/10" },
];

export function MentionsBySourceCards({ data }: Props) {
  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl p-3 min-h-0">
      <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-2.5">By Source</div>
      <div className="grid grid-cols-5 gap-2 flex-1 min-h-0">
        {CARDS.map(card => {
          const stat: SourceTypeStat = data[card.key] ?? { count: 0, delta_pct: null, negative_pct: 0, avg_rating: null, sparkline: [] };
          const isReview = card.key === "google_review";
          return (
            <div
              key={card.key}
              className="flex flex-col justify-between bg-[#0d1626] border border-white/8 rounded-lg px-2.5 py-2"
            >
              {/* icon + label */}
              <div>
                <div className={`w-7 h-7 rounded-md flex items-center justify-center mb-1.5 ${card.accent}`}>
                  {card.icon}
                </div>
                <div className="text-[10px] font-medium text-white/50 leading-tight">{card.label}</div>
              </div>

              {/* count + delta */}
              <div>
                <div className="flex items-baseline gap-1 mt-1.5">
                  <span className="text-[18px] font-bold text-white leading-none">{fmt(stat.count)}</span>
                  <DeltaBadge pct={stat.delta_pct} />
                </div>

                {/* sub-stat */}
                {isReview ? (
                  stat.avg_rating !== null ? (
                    <div className="text-[9px] text-amber-400/80 mt-0.5">
                      ★ {stat.avg_rating.toFixed(1)} / 5
                    </div>
                  ) : null
                ) : (
                  stat.negative_pct !== null && stat.negative_pct > 0 ? (
                    <div className="text-[9px] text-red-400/70 mt-0.5">
                      Neg {stat.negative_pct}%
                    </div>
                  ) : null
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
