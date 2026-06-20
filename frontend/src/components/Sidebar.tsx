import type { ReactNode } from "react";

export type Tab = "overview" | "sources" | "topics" | "users";

interface NavItem {
  id: string;
  label: string;
  tab?: Tab;
  icon: ReactNode;
  section?: boolean;
  adminOnly?: boolean;
}

interface Props {
  brand: { id: string; name: string } | null;
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  onBrandChange: () => void;
  isAdmin: boolean;
  lastUpdated?: string | null;
}

function NavIcon({ d }: { d: string }) {
  return (
    <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d={d} />
    </svg>
  );
}

const NAV_ITEMS: NavItem[] = [
  {
    id: "overview", tab: "overview", label: "Executive Overview",
    icon: <NavIcon d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />,
  },
  {
    id: "sources-rss", tab: "sources", label: "News & RSS",
    icon: <NavIcon d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />,
  },
  {
    id: "youtube", tab: "overview", label: "YouTube",
    icon: <NavIcon d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />,
  },
  {
    id: "blogs", tab: "sources", label: "Blogs & Portals",
    icon: <NavIcon d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />,
  },
  {
    id: "review-sites", tab: "overview", label: "Review Sites",
    icon: <NavIcon d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />,
  },
  {
    id: "social", tab: "sources", label: "Social & Forums",
    icon: <NavIcon d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />,
  },
  {
    id: "competitors", tab: "overview", label: "Competitors",
    icon: <NavIcon d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />,
  },
  {
    id: "topics", tab: "topics", label: "Reports",
    icon: <NavIcon d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />,
  },
  {
    id: "alerts", tab: "overview", label: "Alerts & Risks",
    icon: <NavIcon d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />,
  },
  {
    id: "users", tab: "users", label: "Settings", adminOnly: true,
    icon: <NavIcon d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />,
  },
];

function formatLastUpdated(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function Sidebar({ brand, activeTab, onTabChange, onBrandChange, isAdmin, lastUpdated }: Props) {
  return (
    <aside className="w-56 shrink-0 flex flex-col bg-[#1a2744] min-h-screen">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-tight">BrandPulse</div>
            <div className="text-[10px] text-blue-300/70 leading-tight">Media Sentiment Dashboard</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.filter(item => !item.adminOnly || isAdmin).map(item => {
          const isActive = item.tab === activeTab &&
            (item.id === "overview" ? activeTab === "overview" :
             item.id === "sources-rss" || item.id === "blogs" || item.id === "social" ? activeTab === "sources" :
             item.id === "topics" ? activeTab === "topics" :
             item.id === "users" ? activeTab === "users" :
             false);

          const handleClick = () => {
            if (item.tab) onTabChange(item.tab);
          };

          return (
            <button
              key={item.id}
              onClick={handleClick}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-colors text-sm ${
                isActive
                  ? "bg-blue-600/25 text-blue-300 border border-blue-500/30"
                  : "text-white/60 hover:text-white/90 hover:bg-white/5"
              }`}
            >
              <span className={isActive ? "text-blue-400" : "text-white/40"}>
                {item.icon}
              </span>
              <span className="text-[13px] font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Brand selector */}
      <div className="px-3 py-3 border-t border-white/10 space-y-2">
        <div className="text-[10px] text-white/40 uppercase tracking-wider font-medium px-1">
          Monitoring For
        </div>
        {brand ? (
          <button
            onClick={onBrandChange}
            className="w-full flex items-center justify-between bg-white/8 hover:bg-white/12 border border-white/10 rounded-lg px-3 py-2 transition-colors"
          >
            <span className="text-xs font-semibold text-white truncate">{brand.name}</span>
            <svg className="w-3.5 h-3.5 text-white/40 shrink-0 ml-1" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        ) : (
          <div className="text-xs text-white/30 px-1">No brand selected</div>
        )}

        {lastUpdated && (
          <div className="px-1 pt-1">
            <div className="text-[10px] text-white/30">Last Updated</div>
            <div className="text-[10px] text-white/50 mt-0.5">{formatLastUpdated(lastUpdated)}</div>
          </div>
        )}
      </div>
    </aside>
  );
}
