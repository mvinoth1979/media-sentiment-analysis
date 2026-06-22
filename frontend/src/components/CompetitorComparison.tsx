import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCompetitorSentiment } from "../lib/api";
import { CompetitorShareOfVoice } from "./CompetitorShareOfVoice";
import type { BrandSentimentEntry } from "../lib/types";

interface Props {
  brandId: string;
  days?: number;
  topTopics?: string[];
}

type Tab = "sov" | "sentiment" | "topics";

function SentimentBar({ entry }: { entry: BrandSentimentEntry }) {
  return (
    <div className="py-1.5">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] font-medium text-white/80 truncate max-w-[60%]">
          {entry.is_brand ? <span className="text-blue-300">{entry.name}</span> : entry.name}
        </span>
        <span className="text-[9px] text-white/30">{entry.count} articles</span>
      </div>
      <div className="flex h-4 rounded-full overflow-hidden gap-px">
        <div
          className="bg-emerald-500/70 flex items-center justify-center transition-all"
          style={{ width: `${entry.positive_pct}%` }}
          title={`Positive ${entry.positive_pct}%`}
        >
          {entry.positive_pct > 12 && (
            <span className="text-[8px] font-bold text-white/90">{entry.positive_pct}%</span>
          )}
        </div>
        <div
          className="bg-white/20 flex items-center justify-center transition-all"
          style={{ width: `${entry.neutral_pct}%` }}
          title={`Neutral ${entry.neutral_pct}%`}
        >
          {entry.neutral_pct > 12 && (
            <span className="text-[8px] font-bold text-white/60">{entry.neutral_pct}%</span>
          )}
        </div>
        <div
          className="bg-red-500/70 flex items-center justify-center transition-all"
          style={{ width: `${entry.negative_pct}%` }}
          title={`Negative ${entry.negative_pct}%`}
        >
          {entry.negative_pct > 12 && (
            <span className="text-[8px] font-bold text-white/90">{entry.negative_pct}%</span>
          )}
        </div>
      </div>
    </div>
  );
}

function SentimentTab({ brandId, days }: { brandId: string; days: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["competitor-sentiment", brandId, days],
    queryFn: () => fetchCompetitorSentiment(brandId, days),
    staleTime: 5 * 60_000,
  });

  if (isLoading) {
    return (
      <div className="space-y-3 p-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-10 bg-white/5 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data?.brands.length) {
    return (
      <div className="flex items-center justify-center h-32 text-[11px] text-white/30">
        No competitor data — configure competitors in Brand Settings
      </div>
    );
  }

  return (
    <div className="p-3 space-y-0.5">
      <div className="flex items-center gap-3 mb-3 text-[9px] text-white/40">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500/70" />Positive</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-white/20" />Neutral</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500/70" />Negative</span>
      </div>
      <div className="divide-y divide-white/5">
        {data.brands.map(b => <SentimentBar key={b.name} entry={b} />)}
      </div>
    </div>
  );
}

function TopicsTab({ topics }: { topics: string[] }) {
  if (!topics.length) {
    return (
      <div className="flex items-center justify-center h-32 text-[11px] text-white/30">
        No topic data available
      </div>
    );
  }
  return (
    <div className="p-3">
      <div className="text-[9px] text-white/30 mb-3 uppercase tracking-wider">Top topics for your brand this period</div>
      <div className="space-y-1.5">
        {topics.slice(0, 10).map((t, i) => (
          <div key={t} className="flex items-center gap-2.5">
            <span className="text-[10px] text-white/30 w-4 text-right shrink-0">{i + 1}</span>
            <div className="flex-1 h-6 bg-white/5 rounded-md overflow-hidden">
              <div
                className="h-full bg-blue-500/25 flex items-center px-2"
                style={{ width: `${Math.max(20, 100 - i * 9)}%` }}
              >
                <span className="text-[10px] font-medium text-white/70 truncate">
                  {t.replace(/_/g, " ")}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 pt-3 border-t border-white/5 text-[9px] text-white/25 text-center">
        Competitor topic comparison — coming soon
      </div>
    </div>
  );
}

const TABS: { id: Tab; label: string }[] = [
  { id: "sov",       label: "Share of Voice" },
  { id: "sentiment", label: "Sentiment" },
  { id: "topics",    label: "Topics" },
];

export function CompetitorComparison({ brandId, days = 30, topTopics = [] }: Props) {
  const [tab, setTab] = useState<Tab>("sov");

  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl overflow-hidden min-h-0">
      {/* Header */}
      <div className="flex items-center gap-1.5 px-3 pt-2.5 border-b border-white/8 flex-none">
        <div className="flex-1">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-[9px] text-white/35">Executive Overview</span>
            <span className="text-[9px] text-white/20">›</span>
            <span className="text-[10px] font-semibold text-white/70">Competitor Comparison</span>
          </div>
          {/* Tab bar */}
          <div className="flex gap-1">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`text-[10px] font-medium px-3 py-1.5 border-b-2 transition-colors ${
                  tab === t.id
                    ? "border-blue-400 text-blue-300"
                    : "border-transparent text-white/40 hover:text-white/60"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 min-h-0 overflow-auto">
        {tab === "sov" && (
          <div className="p-2 h-full">
            <CompetitorShareOfVoice brandId={brandId} />
          </div>
        )}
        {tab === "sentiment" && (
          <SentimentTab brandId={brandId} days={days} />
        )}
        {tab === "topics" && (
          <TopicsTab topics={topTopics} />
        )}
      </div>

      {/* Drill-down journey strip */}
      <div className="flex items-center border-t border-white/5 flex-none px-3 py-2 gap-0 overflow-x-auto">
        {["Exec Overview", "Source Level", "Mention Level", "Insights & Action"].map((step, i, arr) => (
          <div key={step} className="flex items-center shrink-0">
            <span className={`text-[9px] ${i === 0 ? "text-blue-400 font-semibold" : "text-white/25"}`}>{step}</span>
            {i < arr.length - 1 && <span className="text-white/15 mx-1.5 text-[9px]">→</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
