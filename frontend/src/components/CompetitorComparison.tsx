import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCompetitorSentiment } from "../lib/api";
import { CompetitorShareOfVoice } from "./CompetitorShareOfVoice";
import type { BrandSentimentEntry } from "../lib/types";

interface Props {
  brandId: string;
  days?: number;
  topTopics?: string[];
  onTopicDrill?: (topic: string) => void;
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

function TopicsTab({ topics, onTopicDrill }: { topics: string[]; onTopicDrill?: (t: string) => void }) {
  if (!topics.length) {
    return (
      <div className="flex items-center justify-center h-32 text-[11px] text-white/30">
        No topic data available
      </div>
    );
  }
  return (
    <div className="p-3">
      <div className="text-[9px] text-white/30 mb-3 uppercase tracking-wider">Top topics — click to drill down</div>
      <div className="space-y-1.5">
        {topics.slice(0, 10).map((t, i) => (
          <button
            key={t}
            onClick={() => onTopicDrill?.(t)}
            className="w-full flex items-center gap-2.5 hover:opacity-90 transition-opacity text-left"
          >
            <span className="text-[10px] text-white/30 w-4 text-right shrink-0">{i + 1}</span>
            <div className="flex-1 h-6 bg-white/5 rounded-md overflow-hidden">
              <div
                className="h-full bg-blue-500/25 hover:bg-blue-500/40 flex items-center px-2 transition-colors"
                style={{ width: `${Math.max(20, 100 - i * 9)}%` }}
              >
                <span className="text-[10px] font-medium text-white/70 truncate">
                  {t.replace(/_/g, " ")}
                </span>
              </div>
            </div>
            <span className="text-[8px] text-blue-400/40 shrink-0">→</span>
          </button>
        ))}
      </div>
    </div>
  );
}

const TABS: { id: Tab; label: string }[] = [
  { id: "sov",       label: "Share of Voice" },
  { id: "sentiment", label: "Sentiment Comparison" },
  { id: "topics",    label: "Topics Comparison" },
];

export function CompetitorComparison({ brandId, days = 30, topTopics = [], onTopicDrill }: Props) {
  const [tab, setTab] = useState<Tab>("sov");

  return (
    <div className="h-full flex flex-col bg-[#1a2744] border border-white/10 rounded-xl overflow-hidden min-h-0">
      {/* Header */}
      <div className="flex items-center gap-1.5 px-3 pt-2.5 border-b border-white/8 flex-none">
        <div className="flex-1">
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-[9px] text-white/35">Executive Overview</span>
            <span className="text-[9px] text-white/20">›</span>
            <span className="text-[10px] font-semibold text-white/70">Share of Voice</span>
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
      <div className="flex-1 min-h-0 overflow-hidden">
        {tab === "sov" && (
          <div className="p-2 h-full">
            <CompetitorShareOfVoice brandId={brandId} />
          </div>
        )}
        {tab === "sentiment" && (
          <div className="flex gap-2 h-full min-h-0 p-2">
            <div className="flex-[3] overflow-y-auto min-h-0">
              <SentimentTab brandId={brandId} days={days} />
            </div>
            <div className="flex-[2] min-h-0">
              <CompetitorShareOfVoice brandId={brandId} compact />
            </div>
          </div>
        )}
        {tab === "topics" && (
          <TopicsTab topics={topTopics} onTopicDrill={onTopicDrill} />
        )}
      </div>
    </div>
  );
}
