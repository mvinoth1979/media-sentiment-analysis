import { useQuery } from "@tanstack/react-query";
import { fetchAiSummary } from "../lib/api";

interface Props {
  brandId: string;
  queryParams: { days?: number; date_from?: string; date_to?: string };
}

const CARDS = [
  { key: "what_changed" as const, label: "Situation", icon: "📊", border: "border-l-blue-500/50" },
  { key: "why"          as const, label: "Root Cause", icon: "🔍", border: "border-l-amber-500/50" },
];

function Skeleton() {
  return (
    <div className="flex gap-2 overflow-x-auto scrollbar-none">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="flex-shrink-0 w-44 h-20 bg-white/5 rounded-xl animate-pulse" />
      ))}
    </div>
  );
}

export function WhatChangedCards({ brandId, queryParams }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["ai-summary", brandId, queryParams],
    queryFn: () => fetchAiSummary(brandId, queryParams),
    staleTime: 30 * 60_000,
    retry: 1,
  });

  if (isLoading) return <Skeleton />;
  if (!data) return null;

  const actionCards = (data.actions || []).slice(0, 1).map((action, i) => ({
    key: `action_${i}`,
    label: "Action Required",
    icon: "⚡",
    border: "border-l-emerald-500/50",
    text: action,
  }));

  const cards = [
    ...CARDS.map(c => ({ ...c, text: data[c.key] })),
    ...actionCards,
  ];

  return (
    <div className="flex gap-2 overflow-x-auto scrollbar-none pb-0.5">
      {cards.map(card => (
        <div
          key={card.key}
          className={`flex-shrink-0 w-48 bg-[#1a2744] border border-white/8 border-l-2 ${card.border} rounded-xl px-3 py-2.5 space-y-1`}
        >
          <div className="flex items-center gap-1.5">
            <span className="text-[11px]">{card.icon}</span>
            <span className="text-[9px] font-semibold text-white/40 uppercase tracking-wider">{card.label}</span>
          </div>
          <p className="text-[11px] text-white/75 leading-relaxed line-clamp-3">{card.text}</p>
        </div>
      ))}
    </div>
  );
}
