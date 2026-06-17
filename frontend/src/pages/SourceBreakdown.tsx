import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchSources } from "../lib/api";
import { SourceSentimentChart } from "../components/charts/SourceSentimentChart";
import { MentionsList } from "../components/mentions/MentionsList";
import type { SourceStat } from "../lib/types";

interface Props {
  brandId: string;
}

type SortKey = keyof Omit<SourceStat, "portal_id">;

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "count", label: "Mentions" },
  { key: "positive", label: "Positive" },
  { key: "negative", label: "Negative" },
  { key: "neutral", label: "Neutral" },
  { key: "avg_credibility", label: "Avg. Credibility" },
];

export function SourceBreakdown({ brandId }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("count");
  const [sortDesc, setSortDesc] = useState(true);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);

  const { data: sources = [], isLoading } = useQuery<SourceStat[]>({
    queryKey: ["sources", brandId],
    queryFn: () => fetchSources(brandId),
    staleTime: 60_000,
  });

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDesc(d => !d);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  }

  const sorted = [...sources].sort((a, b) =>
    sortDesc ? b[sortKey] - a[sortKey] : a[sortKey] - b[sortKey]
  );

  return (
    <div className="p-4 sm:p-6 space-y-4">
      <div>
        <h2 className="text-lg sm:text-xl font-bold text-gray-100">Source Breakdown</h2>
        <p className="text-xs text-gray-500 mt-0.5">All sources, sortable by any metric</p>
      </div>

      {!isLoading && sources.length > 0 && (
        <SourceSentimentChart sources={sources} onSelect={setSelectedSource} />
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        {isLoading ? (
          <div className="text-gray-500 text-sm py-8 text-center">Loading sources…</div>
        ) : sources.length === 0 ? (
          <div className="text-gray-600 text-sm py-8 text-center">No sources found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500 text-left">
                  <th className="pb-2 pr-3 font-medium">Source</th>
                  {COLUMNS.map(col => (
                    <th
                      key={col.key}
                      onClick={() => toggleSort(col.key)}
                      className="pb-2 pr-3 font-medium text-right cursor-pointer hover:text-gray-300 select-none"
                    >
                      {col.label}{sortKey === col.key ? (sortDesc ? " ▼" : " ▲") : ""}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {sorted.map(s => (
                  <tr key={s.portal_id} className="hover:bg-gray-800/40 transition-colors">
                    <td className="py-2 pr-3">
                      <button
                        onClick={() => setSelectedSource(s.portal_id)}
                        className="text-gray-200 hover:text-indigo-400 hover:underline text-left"
                      >
                        {s.portal_id.replace(/_/g, " ")}
                      </button>
                    </td>
                    <td className="py-2 pr-3 text-right text-gray-300">{s.count}</td>
                    <td className="py-2 pr-3 text-right text-green-400">{s.positive}</td>
                    <td className="py-2 pr-3 text-right text-red-400">{s.negative}</td>
                    <td className="py-2 pr-3 text-right text-gray-400">{s.neutral}</td>
                    <td className="py-2 pr-3 text-right">
                      <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${
                        s.avg_credibility >= 0.85
                          ? "bg-green-900/40 text-green-400"
                          : s.avg_credibility >= 0.75
                          ? "bg-yellow-900/40 text-yellow-400"
                          : "bg-gray-800 text-gray-500"
                      }`}>
                        {s.avg_credibility.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedSource && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Mentions from <span className="text-gray-200 font-medium">{selectedSource.replace(/_/g, " ")}</span>
            </span>
            <button onClick={() => setSelectedSource(null)} className="text-xs text-indigo-400 underline">
              Clear
            </button>
          </div>
          <MentionsList key={selectedSource} brandId={brandId} initialPortalId={selectedSource} />
        </div>
      )}
    </div>
  );
}
