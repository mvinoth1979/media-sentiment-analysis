import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchMentions, deleteMentions } from "../../lib/api";
import { SentimentBadge } from "../ui/SentimentBadge";
import type { ArticleItem } from "../../lib/types";

interface Props {
  brandId: string;
  portals?: string[];
  topics?: string[];
  initialPortalId?: string;
  initialTopic?: string;
  selectable?: boolean;
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

export function MentionsList({ brandId, portals = [], topics = [], initialPortalId = "", initialTopic = "", selectable = false }: Props) {
  const [page, setPage] = useState(0);
  const [sentiment, setSentiment] = useState("");
  const [language, setLanguage] = useState("");
  const [portalId, setPortalId] = useState(initialPortalId);
  const [topic, setTopic] = useState(initialTopic);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [qDraft, setQDraft] = useState("");
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmDelete, setConfirmDelete] = useState(false);

  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: (ids: string[]) => deleteMentions(brandId, ids),
    onSuccess: () => {
      setSelected(new Set());
      setConfirmDelete(false);
      queryClient.invalidateQueries({ queryKey: ["mentions", brandId] });
      queryClient.invalidateQueries({ queryKey: ["sources", brandId] });
      queryClient.invalidateQueries({ queryKey: ["topics", brandId] });
    },
  });

  useEffect(() => {
    const id = setTimeout(() => setQ(qDraft), 400);
    return () => clearTimeout(id);
  }, [qDraft]);

  const params: Record<string, string> = { limit: String(PAGE_SIZE), offset: String(page * PAGE_SIZE) };
  if (sentiment) params.sentiment = sentiment;
  if (language) params.language = language;
  if (portalId) params.portal_id = portalId;
  if (topic) params.topic = topic;
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  if (q) params.q = q;

  const { data: articles = [], isLoading } = useQuery<ArticleItem[]>({
    queryKey: ["mentions", brandId, page, sentiment, language, portalId, topic, dateFrom, dateTo, q],
    queryFn: () => fetchMentions(brandId, params),
    staleTime: 60_000,
  });

  const hasFilters = !!(sentiment || language || portalId || topic || dateFrom || dateTo || q);

  function toggleSelect(id: string) {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selected.size === articles.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(articles.map(a => a.id)));
    }
  }

  function resetFilters() {
    setSentiment("");
    setLanguage("");
    setPortalId("");
    setTopic("");
    setDateFrom("");
    setDateTo("");
    setQDraft("");
    setQ("");
    setPage(0);
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-4">
      {/* Delete confirmation bar */}
      {selectable && selected.size > 0 && (
        <div className="flex items-center gap-3 bg-red-950/40 border border-red-800/50 rounded-lg px-3 py-2">
          <span className="text-sm text-red-300">
            {selected.size} mention{selected.size > 1 ? "s" : ""} selected
          </span>
          {confirmDelete ? (
            <>
              <span className="text-xs text-red-400 ml-auto">
                Permanently delete and block similar articles?
              </span>
              <button
                onClick={() => deleteMutation.mutate(Array.from(selected))}
                disabled={deleteMutation.isPending}
                className="text-xs px-3 py-1 bg-red-700 hover:bg-red-600 text-white rounded-lg disabled:opacity-50"
              >
                {deleteMutation.isPending ? "Deleting…" : "Confirm delete"}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="text-xs text-gray-400 hover:text-gray-200"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setConfirmDelete(true)}
                className="ml-auto text-xs px-3 py-1 bg-red-900/60 hover:bg-red-800/80 border border-red-700 text-red-300 rounded-lg"
              >
                Delete selected
              </button>
              <button
                onClick={() => setSelected(new Set())}
                className="text-xs text-gray-500 hover:text-gray-300"
              >
                Clear
              </button>
            </>
          )}
        </div>
      )}

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

      {/* Second filter row: search, portal, topic, date range */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={qDraft}
          onChange={e => { setQDraft(e.target.value); setPage(0); }}
          placeholder="Search title…"
          className="bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-200 px-2.5 py-1.5 placeholder:text-gray-500 focus:outline-none focus:border-indigo-500 w-40"
        />

        {portals.length > 0 && (
          <select
            value={portalId}
            onChange={e => { setPortalId(e.target.value); setPage(0); }}
            className="bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-200 px-2 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All sources</option>
            {portals.map(p => (
              <option key={p} value={p}>{p.replace(/_/g, " ")}</option>
            ))}
          </select>
        )}

        {topics.length > 0 && (
          <select
            value={topic}
            onChange={e => { setTopic(e.target.value); setPage(0); }}
            className="bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-200 px-2 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All topics</option>
            {topics.map(t => (
              <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
            ))}
          </select>
        )}

        <input
          type="date"
          value={dateFrom}
          onChange={e => { setDateFrom(e.target.value); setPage(0); }}
          className="bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-300 px-2 py-1.5 focus:outline-none focus:border-indigo-500"
        />
        <span className="text-gray-600 text-xs">to</span>
        <input
          type="date"
          value={dateTo}
          onChange={e => { setDateTo(e.target.value); setPage(0); }}
          className="bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-300 px-2 py-1.5 focus:outline-none focus:border-indigo-500"
        />

        {hasFilters && (
          <button onClick={resetFilters} className="text-xs text-indigo-400 underline ml-auto">
            Clear all filters
          </button>
        )}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-gray-500 text-sm py-8 text-center">Loading mentions…</div>
      ) : articles.length === 0 ? (
        <div className="text-gray-600 text-sm py-8 text-center">
          No mentions found.{" "}
          {hasFilters && (
            <button onClick={resetFilters} className="text-indigo-400 underline">Clear filters</button>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-left">
                {selectable && (
                  <th className="pb-2 pr-3 w-8">
                    <input
                      type="checkbox"
                      checked={articles.length > 0 && selected.size === articles.length}
                      onChange={toggleSelectAll}
                      className="accent-indigo-500 cursor-pointer"
                    />
                  </th>
                )}
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
                <tr key={a.id} className={`hover:bg-gray-800/40 transition-colors ${selected.has(a.id) ? "bg-red-950/20" : ""}`}>
                  {selectable && (
                    <td className="py-2 pr-3">
                      <input
                        type="checkbox"
                        checked={selected.has(a.id)}
                        onChange={() => toggleSelect(a.id)}
                        className="accent-indigo-500 cursor-pointer"
                      />
                    </td>
                  )}
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
