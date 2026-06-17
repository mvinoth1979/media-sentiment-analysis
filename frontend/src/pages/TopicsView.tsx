import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchTopics } from "../lib/api";
import type { TopicStat } from "../lib/types";
import { TopicSentimentChart } from "../components/charts/TopicSentimentChart";
import { MentionsList } from "../components/mentions/MentionsList";

interface Props {
  brandId: string;
}

type SortKey = keyof Omit<TopicStat, "topic">;

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "count", label: "Mentions" },
  { key: "positive", label: "Positive" },
  { key: "negative", label: "Negative" },
  { key: "neutral", label: "Neutral" },
];

export function TopicsView({ brandId }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("count");
  const [sortDesc, setSortDesc] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);

  const { data: topics = [], isLoading } = useQuery<TopicStat[]>({
    queryKey: ["topics", brandId],
    queryFn: () => fetchTopics(brandId),
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

  const sorted = [...topics].sort((a, b) =>
    sortDesc ? b[sortKey] - a[sortKey] : a[sortKey] - b[sortKey]
  );

  return (
    <div className="p-4 sm:p-6 space-y-4">
      <div>
        <h2 className="text-lg sm:text-xl font-bold text-gray-100">Topics</h2>
        <p className="text-xs text-gray-500 mt-0.5">All topics, sortable by any metric</p>
      </div>

      {!isLoading && topics.length > 0 && (
        <TopicSentimentChart topics={topics} onSelect={setSelectedTopic} />
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        {isLoading ? (
          <div className="text-gray-500 text-sm py-8 text-center">Loading topics…</div>
        ) : topics.length === 0 ? (
          <div className="text-gray-600 text-sm py-8 text-center">No topics found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500 text-left">
                  <th className="pb-2 pr-3 font-medium">Topic</th>
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
                {sorted.map(t => (
                  <tr key={t.topic} className="hover:bg-gray-800/40 transition-colors">
                    <td className="py-2 pr-3">
                      <button
                        onClick={() => setSelectedTopic(t.topic)}
                        className="text-gray-200 hover:text-indigo-400 hover:underline text-left"
                      >
                        {t.topic.replace(/_/g, " ")}
                      </button>
                    </td>
                    <td className="py-2 pr-3 text-right text-gray-300">{t.count}</td>
                    <td className="py-2 pr-3 text-right text-green-400">{t.positive}</td>
                    <td className="py-2 pr-3 text-right text-red-400">{t.negative}</td>
                    <td className="py-2 pr-3 text-right text-gray-400">{t.neutral}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedTopic && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Mentions tagged <span className="text-gray-200 font-medium">{selectedTopic.replace(/_/g, " ")}</span>
            </span>
            <button onClick={() => setSelectedTopic(null)} className="text-xs text-indigo-400 underline">
              Clear
            </button>
          </div>
          <MentionsList key={selectedTopic} brandId={brandId} initialTopic={selectedTopic} />
        </div>
      )}
    </div>
  );
}
