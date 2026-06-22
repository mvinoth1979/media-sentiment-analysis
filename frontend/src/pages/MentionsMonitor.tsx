import { useState } from "react";
import { MentionsList } from "../components/mentions/MentionsList";
import { JournalistCoverage } from "./JournalistCoverage";

interface Props {
  brandId: string;
  brandName: string;
}

type MonitorTab = "all" | "news" | "youtube" | "reviews" | "reddit" | "journalists";

const TABS: { id: MonitorTab; label: string; sourceCategory?: string; icon: string }[] = [
  { id: "all",         label: "All Mentions",  icon: "M4 6h16M4 10h16M4 14h16M4 18h7" },
  { id: "news",        label: "News & RSS",    sourceCategory: "news",         icon: "M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" },
  { id: "youtube",     label: "YouTube",       sourceCategory: "youtube",      icon: "M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
  { id: "reviews",     label: "Reviews",       sourceCategory: "google_review", icon: "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" },
  { id: "reddit",      label: "Reddit",        sourceCategory: "reddit_post",  icon: "M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" },
  { id: "journalists", label: "Journalists",   icon: "M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" },
];

const TAB_ACCENT: Record<MonitorTab, string> = {
  all:         "border-blue-400 text-blue-300",
  news:        "border-emerald-400 text-emerald-300",
  youtube:     "border-red-400 text-red-300",
  reviews:     "border-amber-400 text-amber-300",
  reddit:      "border-orange-400 text-orange-300",
  journalists: "border-purple-400 text-purple-300",
};

function TabIcon({ d }: { d: string }) {
  return (
    <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d={d} />
    </svg>
  );
}

export function MentionsMonitor({ brandId, brandName }: Props) {
  const [activeTab, setActiveTab] = useState<MonitorTab>("all");
  const tab = TABS.find(t => t.id === activeTab)!;

  return (
    <div className="h-full flex flex-col bg-[#0d1626] overflow-hidden">

      {/* Header */}
      <div className="flex-none px-5 pt-4 pb-0 border-b border-white/10">
        <div className="flex items-end justify-between mb-3">
          <div>
            <h1 className="text-sm font-bold text-white leading-tight">Mentions Monitor</h1>
            <p className="text-[10px] text-white/40 mt-0.5">
              Browse and filter all media mentions across every source channel
            </p>
          </div>
          <span className="text-[9px] text-white/25 pb-1">{brandName}</span>
        </div>

        {/* Source tab bar */}
        <div className="flex gap-0 overflow-x-auto" style={{ scrollbarWidth: "none" }}>
          {TABS.map(t => {
            const isActive = t.id === activeTab;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex items-center gap-1.5 px-3.5 py-2.5 text-[11px] font-medium border-b-2 transition-colors shrink-0 ${
                  isActive
                    ? TAB_ACCENT[t.id]
                    : "border-transparent text-white/40 hover:text-white/65 hover:border-white/20"
                }`}
              >
                <span className={isActive ? "" : "text-white/30"}>
                  <TabIcon d={t.icon} />
                </span>
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content — key forces re-mount on tab change so each tab has independent state */}
      <div className="flex-1 min-h-0 overflow-auto">
        {activeTab === "journalists" ? (
          <JournalistCoverage
            key="journalists"
            brandId={brandId}
            brandName={brandName}
          />
        ) : (
          <MentionsList
            key={activeTab}
            brandId={brandId}
            brandName={brandName}
            initialSourceCategory={tab.sourceCategory}
            selectable
            syncUrl
          />
        )}
      </div>
    </div>
  );
}
