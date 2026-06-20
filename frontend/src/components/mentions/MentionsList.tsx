import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { fetchMentions, deleteMentions, exportMentionsCsv } from "../../lib/api";
import { formatCount } from "../../lib/utils";
import { SentimentBadge } from "../ui/SentimentBadge";
import { YouTubeIcon } from "../ui/YouTubeIcon";
import type { ArticleItem } from "../../lib/types";

interface Props {
  brandId: string;
  brandName?: string;
  portals?: string[];
  topics?: string[];
  states?: string[];
  initialPortalId?: string;
  initialTopic?: string;
  initialState?: string;
  initialSentiment?: string;
  selectable?: boolean;
  syncUrl?: boolean;
}

const PAGE_SIZE = 10;

const SENTIMENT_FILTERS = [
  { label: "All", value: "" },
  { label: "Positive", value: "positive" },
  { label: "Negative", value: "negative" },
  { label: "Neutral", value: "neutral" },
];

const LANG_FILTERS = [
  { label: "All languages", value: "" },
  { label: "English", value: "en" },
  { label: "Tamil", value: "ta" },
  { label: "Hindi", value: "hi" },
  { label: "Gujarati", value: "gu" },
  { label: "Bengali", value: "bn" },
  { label: "Kannada", value: "kn" },
];

const SOURCE_TYPE_FILTERS = [
  { label: "All types", value: "" },
  { label: "News", value: "news" },
  { label: "YT Videos", value: "youtube_video" },
  { label: "YT Comments", value: "youtube_comment" },
];

function readParam(key: string, fallback = "") {
  return new URLSearchParams(window.location.search).get(key) ?? fallback;
}

export function MentionsList({
  brandId,
  brandName = "",
  portals = [],
  topics = [],
  states = [],
  initialPortalId = "",
  initialTopic = "",
  initialState = "",
  initialSentiment,
  selectable = false,
  syncUrl = false,
}: Props) {
  const [page, setPage]           = useState(0);
  const [maxKnownPage, setMaxKnownPage] = useState(0);
  const [sentiment, setSentiment]  = useState(() => syncUrl ? readParam("sentiment") : (initialSentiment ?? ""));
  const [language, setLanguage]   = useState(() => syncUrl ? readParam("language") : "");
  const [sourceType, setSourceType] = useState(() => syncUrl ? readParam("source_type") : "");
  const [portalId, setPortalId]   = useState(initialPortalId);
  const [topic, setTopic]         = useState(initialTopic);
  const [state, setState]         = useState(() => syncUrl ? readParam("state") : initialState);
  const [dateFrom, setDateFrom]   = useState(() => syncUrl ? readParam("date_from") : "");
  const [dateTo, setDateTo]       = useState(() => syncUrl ? readParam("date_to") : "");
  const [qDraft, setQDraft]       = useState(() => syncUrl ? readParam("q") : "");
  const [q, setQ]                 = useState(() => syncUrl ? readParam("q") : "");
  const [selected, setSelected]   = useState<Set<string>>(new Set());
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [exporting, setExporting] = useState(false);

  const queryClient = useQueryClient();

  const syncRef = useRef(syncUrl);
  useEffect(() => {
    if (!syncRef.current) return;
    const sp = new URLSearchParams();
    if (sentiment)   sp.set("sentiment", sentiment);
    if (language)    sp.set("language", language);
    if (sourceType)  sp.set("source_type", sourceType);
    if (state)       sp.set("state", state);
    if (dateFrom)    sp.set("date_from", dateFrom);
    if (dateTo)      sp.set("date_to", dateTo);
    if (q)           sp.set("q", q);
    const qs = sp.toString();
    history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
  }, [sentiment, language, sourceType, state, dateFrom, dateTo, q]);

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

  // Track how many pages we know exist (grows as user navigates forward)
  useEffect(() => {
    if (isLoading) return;
    if (articles.length === PAGE_SIZE) {
      setMaxKnownPage(p => Math.max(p, page + 1));
    } else {
      setMaxKnownPage(p => Math.max(p, page));
    }
  }, [articles, isLoading, page]);

  // Reset discovered page range when filters change
  useEffect(() => {
    setMaxKnownPage(0);
  }, [sentiment, language, sourceType, portalId, topic, state, dateFrom, dateTo, q]);

  // React to "View All" clicks from TopHeadlines — apply sentiment filter externally
  useEffect(() => {
    if (initialSentiment !== undefined) {
      setSentiment(initialSentiment);
      setPage(0);
    }
  }, [initialSentiment]);

  const params: Record<string, string> = { limit: String(PAGE_SIZE), offset: String(page * PAGE_SIZE) };
  if (sentiment)  params.sentiment    = sentiment;
  if (language)   params.language     = language;
  if (sourceType) params.source_type  = sourceType;
  if (portalId)   params.portal_id    = portalId;
  if (topic)      params.topic        = topic;
  if (state)      params.state        = state;
  if (dateFrom)   params.date_from    = dateFrom;
  if (dateTo)     params.date_to      = dateTo;
  if (q)          params.q            = q;

  const { data: articles = [], isLoading, isFetching } = useQuery<ArticleItem[]>({
    queryKey: ["mentions", brandId, page, sentiment, language, sourceType, portalId, topic, state, dateFrom, dateTo, q],
    queryFn: () => fetchMentions(brandId, params),
    staleTime: 60_000,
    placeholderData: keepPreviousData,
  });

  const hasFilters = !!(sentiment || language || sourceType || portalId || topic || state || dateFrom || dateTo || q);

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
    setSentiment(""); setLanguage(""); setSourceType(""); setPortalId("");
    setTopic(""); setState(""); setDateFrom(""); setDateTo("");
    setQDraft(""); setQ(""); setPage(0);
  }

  function set<T>(setter: (v: T) => void) {
    return (v: T) => { setter(v); setPage(0); };
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-4 shadow-sm">
      {/* Delete confirmation bar */}
      {selectable && selected.size > 0 && (
        <div className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          <span className="text-sm text-red-600">
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
                className="text-xs px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded-lg disabled:opacity-50"
              >
                {deleteMutation.isPending ? "Deleting…" : "Confirm delete"}
              </button>
              <button onClick={() => setConfirmDelete(false)} className="text-xs text-gray-400 hover:text-gray-200">
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setConfirmDelete(true)}
                className="ml-auto text-xs px-3 py-1 bg-red-50 hover:bg-red-100 border border-red-300 text-red-600 rounded-lg"
              >
                Delete selected
              </button>
              <button onClick={() => setSelected(new Set())} className="text-xs text-gray-500 hover:text-gray-300">
                Clear
              </button>
            </>
          )}
        </div>
      )}

      {/* Row 1: header + sentiment + language + source type + export */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-semibold text-gray-800 mr-auto">All Mentions</span>

        <div className="flex gap-1">
          {SENTIMENT_FILTERS.map(f => (
            <button key={f.value} onClick={() => set(setSentiment)(f.value)}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                sentiment === f.value
                  ? "bg-blue-600 border-blue-500 text-white"
                  : "border-gray-300 text-gray-500 hover:border-gray-400"
              }`}>{f.label}</button>
          ))}
        </div>

        <select
          value={language}
          onChange={e => set(setLanguage)(e.target.value)}
          className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2.5 py-1 focus:outline-none focus:border-blue-500"
        >
          {LANG_FILTERS.map(f => (
            <option key={f.value} value={f.value}>{f.label}</option>
          ))}
        </select>

        <select
          value={sourceType}
          onChange={e => set(setSourceType)(e.target.value)}
          className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2.5 py-1 focus:outline-none focus:border-blue-500"
        >
          {SOURCE_TYPE_FILTERS.map(f => (
            <option key={f.value} value={f.value}>{f.label}</option>
          ))}
        </select>

        <button
          onClick={async () => {
            setExporting(true);
            try {
              const exportParams: Record<string, string> = {};
              if (sentiment)  exportParams.sentiment    = sentiment;
              if (language)   exportParams.language     = language;
              if (sourceType) exportParams.source_type  = sourceType;
              if (portalId)   exportParams.portal_id    = portalId;
              if (topic)      exportParams.topic        = topic;
              if (state)      exportParams.state        = state;
              if (dateFrom)   exportParams.date_from    = dateFrom;
              if (dateTo)     exportParams.date_to      = dateTo;
              if (q)          exportParams.q            = q;
              await exportMentionsCsv(brandId, brandName ?? brandId, exportParams);
            } catch (err) {
              alert("Export failed. Please try again.");
              console.error("CSV export error:", err);
            } finally {
              setExporting(false);
            }
          }}
          disabled={exporting}
          className="text-xs px-3 py-1 border border-gray-300 rounded-lg text-gray-500 hover:border-blue-500 hover:text-blue-600 disabled:opacity-40 transition-colors"
        >
          {exporting ? "Exporting…" : "Export CSV"}
        </button>
      </div>

      {/* Row 2: search, portal, topic, state, date */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text" value={qDraft}
          onChange={e => { setQDraft(e.target.value); setPage(0); }}
          placeholder="Search title…"
          className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2.5 py-1.5 placeholder:text-gray-400 focus:outline-none focus:border-blue-500 w-40"
        />

        {portals.length > 0 && (
          <select value={portalId} onChange={e => set(setPortalId)(e.target.value)}
            className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-1.5 focus:outline-none focus:border-blue-500">
            <option value="">All sources</option>
            {portals.map(p => <option key={p} value={p}>{p.replace(/_/g, " ")}</option>)}
          </select>
        )}

        {topics.length > 0 && (
          <select value={topic} onChange={e => set(setTopic)(e.target.value)}
            className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-1.5 focus:outline-none focus:border-blue-500">
            <option value="">All topics</option>
            {topics.map(t => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
          </select>
        )}

        {states.length > 0 && (
          <select value={state} onChange={e => set(setState)(e.target.value)}
            className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-1.5 focus:outline-none focus:border-blue-500">
            <option value="">All states</option>
            {states.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        )}

        <input type="date" value={dateFrom} onChange={e => set(setDateFrom)(e.target.value)}
          className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-1.5 focus:outline-none focus:border-blue-500" />
        <span className="text-gray-600 text-xs">to</span>
        <input type="date" value={dateTo} onChange={e => set(setDateTo)(e.target.value)}
          className="bg-white border border-gray-300 rounded-lg text-xs text-gray-700 px-2 py-1.5 focus:outline-none focus:border-blue-500" />

        {hasFilters && (
          <button onClick={resetFilters} className="text-xs text-blue-600 underline ml-auto">
            Clear all filters
          </button>
        )}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-gray-400 text-sm py-8 text-center">Loading mentions…</div>
      ) : articles.length === 0 ? (
        <div className="text-gray-600 text-sm py-8 text-center">
          No mentions found.{" "}
          {hasFilters && (
            <button onClick={resetFilters} className="text-blue-600 underline">Clear filters</button>
          )}
        </div>
      ) : (
        <div className="relative overflow-x-auto">
          {isFetching && (
            <div className="absolute inset-0 bg-white/60 z-10 flex items-center justify-center rounded-lg pointer-events-none">
              <span className="text-xs text-gray-500 bg-white px-3 py-1 rounded-full border border-gray-300 shadow-sm">
                Updating…
              </span>
            </div>
          )}
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500 text-left">
                {selectable && (
                  <th className="pb-2 pr-3 w-8">
                    <input type="checkbox"
                      checked={articles.length > 0 && selected.size === articles.length}
                      onChange={toggleSelectAll}
                      className="accent-indigo-500 cursor-pointer" />
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
            <tbody className="divide-y divide-gray-100">
              {articles.map((a, i) => (
                <tr key={a.id}
                  className={`hover:bg-gray-50 transition-colors ${selected.has(a.id) ? "bg-red-50" : ""}`}>
                  {selectable && (
                    <td className="py-2 pr-3">
                      <input type="checkbox" checked={selected.has(a.id)}
                        onChange={() => toggleSelect(a.id)}
                        className="accent-indigo-500 cursor-pointer" />
                    </td>
                  )}
                  <td className="py-2 pr-3 text-gray-400 hidden sm:table-cell">{page * PAGE_SIZE + i + 1}</td>

                  {/* Title + reach metadata + state tags */}
                  <td className="py-2 pr-3 max-w-[180px] sm:max-w-xs">
                    <a href={a.url} target="_blank" rel="noreferrer"
                       className="text-gray-700 hover:text-blue-600 line-clamp-2 leading-snug">
                      {a.title}
                    </a>
                    {a.source_type === "youtube_video" && (a.reach_metadata?.view_count ?? 0) > 0 && (
                      <div className="flex items-center gap-1 mt-0.5">
                        <YouTubeIcon className="inline w-2.5 h-2.5" />
                        <span className="text-[9px] text-gray-500">
                          {formatCount(a.reach_metadata!.view_count)} views
                        </span>
                      </div>
                    )}
                    {a.source_type === "youtube_comment" && (a.reach_metadata?.like_count ?? 0) > 0 && (
                      <div className="mt-0.5">
                        <span className="text-[9px] text-gray-500">
                          ♥ {a.reach_metadata!.like_count} likes
                        </span>
                      </div>
                    )}
                    {a.states_mentioned?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {a.states_mentioned.map(s => (
                          <span key={s} className="text-[9px] px-1 py-0.5 bg-violet-50 text-violet-600 rounded">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>

                  {/* Source — YouTube icon prefix for youtube_ portal_ids */}
                  <td className="py-2 pr-3 text-gray-400 truncate max-w-[80px] sm:max-w-[96px]">
                    {a.source_type?.startsWith("youtube_") && (
                      <YouTubeIcon className="inline w-3 h-3 mr-0.5 mb-0.5" />
                    )}
                    {a.portal_id.replace(/_/g, " ")}
                  </td>

                  <td className="py-2 pr-3 hidden md:table-cell">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      a.language === "ta" ? "bg-teal-50 text-teal-700" : "bg-gray-100 text-gray-500"
                    }`}>{a.language.toUpperCase()}</span>
                  </td>
                  <td className="py-2 pr-3"><SentimentBadge label={a.sentiment_label} /></td>
                  <td className="py-2 pr-3 text-right font-mono text-gray-500 hidden lg:table-cell">
                    {a.sentiment_score.toFixed(2)}
                  </td>
                  <td className="py-2 pr-3 text-right hidden lg:table-cell">
                    <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${
                      a.source_credibility >= 0.85 ? "bg-green-50 text-green-700"
                        : a.source_credibility >= 0.75 ? "bg-yellow-50 text-yellow-700"
                        : "bg-gray-100 text-gray-500"
                    }`}>{a.source_credibility.toFixed(2)}</span>
                  </td>
                  <td className="py-2 text-gray-400 hidden sm:table-cell">
                    {a.published_at ? new Date(a.published_at).toLocaleDateString("en-IN") : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {articles.length > 0 && (
        <div className="flex items-center justify-between pt-1 flex-wrap gap-2">
          <span className="text-xs text-gray-500">
            {page * PAGE_SIZE + 1}–{page * PAGE_SIZE + articles.length} of {
              articles.length === PAGE_SIZE ? `${page * PAGE_SIZE + articles.length}+` : String(page * PAGE_SIZE + articles.length)
            }
          </span>

          <div className="flex items-center gap-1">
            {/* Prev arrow */}
            <button
              onClick={() => setPage(p => p - 1)}
              disabled={page === 0}
              className="text-xs px-2 py-1 border border-gray-700 rounded-lg text-gray-400 hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >←</button>

            {/* Numbered page buttons (1-indexed) */}
            {(() => {
              const totalKnown = maxKnownPage + 1; // total pages we know exist
              const pages: (number | "…")[] = [];

              if (totalKnown <= 7) {
                for (let i = 0; i < totalKnown; i++) pages.push(i);
              } else {
                // Always show first, last, and a window around current
                const show = new Set<number>([0, totalKnown - 1, page - 1, page, page + 1].filter(n => n >= 0 && n < totalKnown));
                let prev = -1;
                [...show].sort((a, b) => a - b).forEach(n => {
                  if (prev !== -1 && n > prev + 1) pages.push("…");
                  pages.push(n);
                  prev = n;
                });
              }

              return pages.map((p_, idx) =>
                p_ === "…" ? (
                  <span key={`ellipsis-${idx}`} className="text-xs text-gray-600 px-1">…</span>
                ) : (
                  <button
                    key={p_}
                    onClick={() => setPage(p_ as number)}
                    className={`text-xs w-7 h-7 rounded-lg border transition-colors ${
                      p_ === page
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200"
                    }`}
                  >
                    {(p_ as number) + 1}
                  </button>
                )
              );
            })()}

            {/* Next arrow */}
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={articles.length < PAGE_SIZE}
              className="text-xs px-2 py-1 border border-gray-700 rounded-lg text-gray-400 hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >→</button>
          </div>
        </div>
      )}
    </div>
  );
}
