import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchMentions } from "../../lib/api";
import { SentimentBadge } from "../ui/SentimentBadge";
import type { ArticleItem } from "../../lib/types";

interface Props {
  brandId: string;
}

const PAGE_SIZE = 50;

const SENTIMENT_FILTERS = [
  { label: "All", value: "" },
  { label: "Positive", value: "positive" },
  { label: "Negative", value: "negative" },
  { label: "Neutral", value: "neutral" },
];

const LANG_FILTERS = [
  { label: "All", value: "" },
  { label: "English", value: "en" },
  { label: "Tamil", value: "ta" },
];

export function MentionsList({ brandId }: Props) {
  const [page, setPage] = useState(0);
  const [sentiment, setSentiment] = useState("");
  const [language, setLanguage] = useState("");

  const params: Record<string, string> = { limit: String(PAGE_SIZE), offset: String(page * PAGE_SIZE) };
  if (sentiment) params.sentiment = sentiment;
  if (language) params.language = language;

  const { data: articles = [], isLoading } = useQuery<ArticleItem[]>({
    queryKey: ["mentions", brandId, page, sentiment, language],
    queryFn: () => fetchMentions(brandId, params),
    staleTime: 60_000,
  });

  function resetFilters() {
    setSentiment("");
    setLanguage("");
    setPage(0);
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-4">
      {/* Header + filters */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-semibold text-gray-200 mr-auto">All Mentions</span>

        <div className="flex gap-1">
          {SENTIMENT_FILTERS.map(f => (
            <button key={f.value}
              onClick={() => { setSentiment(f.value); setPage(0); }}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                sentiment === f.value
                  ? "bg-indigo-600 border-indigo-500 text-white"
                  : "border-gray-700 text-gray-400 hover:border-gray-500"
              }`}
            >{f.label}</button>
          ))}
        </div>

        <div className="flex gap-1">
          {LANG_FILTERS.map(f => (
            <button key={f.value}
              onClick={() => { setLanguage(f.value); setPage(0); }}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                language === f.value
                  ? "bg-teal-700 border-teal-600 text-white"
                  : "border-gray-700 text-gray-400 hover:border-gray-500"
              }`}
            >{f.label}</button>
          ))}
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-gray-500 text-sm py-8 text-center">Loading mentions…</div>
      ) : articles.length === 0 ? (
        <div className="text-gray-600 text-sm py-8 text-center">
          No mentions found.{" "}
          {(sentiment || language) && (
            <button onClick={resetFilters} className="text-indigo-400 underline">Clear filters</button>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-left">
                <th className="pb-2 pr-3 font-medium hidden sm:table-cell w-12">#</th>
                <th className="pb-2 pr-3 font-medium">Title</th>
                <th className="pb-2 pr-3 font-medium w-24">Source</th>
                <th className="pb-2 pr-3 font-medium w-8 hidden md:table-cell">Lang</th>
                <th className="pb-2 pr-3 font-medium w-24">Sentiment</th>
                <th className="pb-2 pr-3 font-medium w-12 text-right hidden lg:table-cell">Score</th>
                <th className="pb-2 pr-3 font-medium w-12 text-right hidden lg:table-cell">Cred</th>
                <th className="pb-2 font-medium w-24 hidden sm:table-cell">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {articles.map((a, i) => (
                <tr key={a.id} className="hover:bg-gray-800/40 transition-colors">
                  <td className="py-2 pr-3 text-gray-600 hidden sm:table-cell">{page * PAGE_SIZE + i + 1}</td>
                  <td className="py-2 pr-3 max-w-[180px] sm:max-w-xs">
                    <a href={a.url} target="_blank" rel="noreferrer"
                       className="text-gray-200 hover:text-indigo-400 line-clamp-2 leading-snug">
                      {a.title}
                    </a>
                  </td>
                  <td className="py-2 pr-3 text-gray-500 truncate max-w-[80px] sm:max-w-[96px]">
                    {a.portal_id.replace(/_/g, " ")}
                  </td>
                  <td className="py-2 pr-3 hidden md:table-cell">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      a.language === "ta"
                        ? "bg-teal-900/40 text-teal-400"
                        : "bg-gray-800 text-gray-400"
                    }`}>{a.language.toUpperCase()}</span>
                  </td>
                  <td className="py-2 pr-3">
                    <SentimentBadge label={a.sentiment_label} />
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-gray-400 hidden lg:table-cell">
                    {a.sentiment_score.toFixed(2)}
                  </td>
                  <td className="py-2 pr-3 text-right hidden lg:table-cell">
                    <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${
                      a.source_credibility >= 0.85
                        ? "bg-green-900/40 text-green-400"
                        : a.source_credibility >= 0.75
                        ? "bg-yellow-900/40 text-yellow-400"
                        : "bg-gray-800 text-gray-500"
                    }`}>
                      {a.source_credibility.toFixed(2)}
                    </span>
                  </td>
                  <td className="py-2 text-gray-600 hidden sm:table-cell">
                    {a.published_at ? new Date(a.published_at).toLocaleDateString("en-IN") : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between pt-1">
        <span className="text-xs text-gray-600">
          Showing {page * PAGE_SIZE + 1}–{page * PAGE_SIZE + articles.length}
        </span>
        <div className="flex gap-2">
          <button onClick={() => setPage(p => p - 1)} disabled={page === 0}
            className="text-xs px-3 py-1 border border-gray-700 rounded-lg text-gray-400 hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
            ← Prev
          </button>
          <button onClick={() => setPage(p => p + 1)} disabled={articles.length < PAGE_SIZE}
            className="text-xs px-3 py-1 border border-gray-700 rounded-lg text-gray-400 hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
