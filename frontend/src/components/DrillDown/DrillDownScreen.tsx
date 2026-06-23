import React, { useState, useEffect } from "react";
import { MentionsList } from "../mentions/MentionsList";
import { ArticleDetail } from "./ArticleDetail";
import type { DrillEntry, DrillFilters, ArticleItem } from "../../lib/types";

interface StackFrame {
  label: string;
  filters: DrillFilters;
}

interface Props {
  brandId: string;
  brandName?: string;
  entry: DrillEntry | null;
}

export function DrillDownScreen({ brandId, brandName, entry }: Props) {
  const [stack, setStack] = useState<StackFrame[]>([]);
  const [article, setArticle] = useState<ArticleItem | null>(null);

  // Reset stack whenever a new drill entry is triggered
  useEffect(() => {
    if (entry) {
      setStack([{ label: entry.widgetTitle, filters: entry.filters }]);
      setArticle(null);
    }
  }, [entry]);

  if (!entry || stack.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-white/25 select-none">
          <div className="text-5xl mb-3 opacity-40">↗</div>
          <div className="text-sm font-medium text-white/40">Click any widget to drill down</div>
          <div className="text-xs mt-1 text-white/20">Cascading data explorer — entities, states, keywords are all clickable</div>
        </div>
      </div>
    );
  }

  const current = stack[stack.length - 1];

  function drillInto(label: string, filters: DrillFilters) {
    setStack(prev => [...prev, { label, filters }]);
    setArticle(null);
  }

  function goToFrame(index: number) {
    setStack(prev => prev.slice(0, index + 1));
    setArticle(null);
  }

  const crumbTitle = article
    ? article.title.slice(0, 48) + (article.title.length > 48 ? "…" : "")
    : null;

  return (
    <div className="flex flex-col h-full overflow-hidden bg-[#0d1626]">

      {/* ── Breadcrumb bar ───────────────────────────────────────────────── */}
      <div className="flex items-center gap-1 px-4 py-2.5 bg-[#111e36] border-b border-white/10 flex-none overflow-x-auto" style={{ scrollbarWidth: "none" }}>
        <span className="text-[10px] text-white/25 shrink-0 mr-1">Drill down</span>

        {stack.map((frame, i) => (
          <React.Fragment key={i}>
            <span className="text-white/20 text-xs shrink-0">›</span>
            {i < stack.length - 1 && !article ? (
              <button
                onClick={() => goToFrame(i)}
                className="text-[10px] text-blue-400 hover:text-blue-300 underline-offset-2 hover:underline transition-colors shrink-0"
              >
                {frame.label}
              </button>
            ) : (
              <span className={`text-[10px] font-medium shrink-0 ${article ? "text-white/50" : "text-white"}`}>
                {frame.label}
              </span>
            )}
          </React.Fragment>
        ))}

        {/* Article title as final breadcrumb when in detail view */}
        {article && (
          <>
            <span className="text-white/20 text-xs shrink-0">›</span>
            <span className="text-[10px] font-medium text-white shrink-0">{crumbTitle}</span>
          </>
        )}

        {/* Back button shortcut */}
        {(stack.length > 1 || article) && (
          <button
            onClick={() => {
              if (article) { setArticle(null); return; }
              goToFrame(stack.length - 2);
            }}
            className="ml-auto shrink-0 text-[10px] text-white/30 hover:text-white/60 border border-white/10 hover:border-white/25 rounded px-1.5 py-0.5 transition-colors"
          >
            ← back
          </button>
        )}
      </div>

      {/* ── Content area ─────────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-auto p-4">
        {article ? (
          <ArticleDetail
            article={article}
            onBack={() => setArticle(null)}
            onDrillInto={drillInto}
          />
        ) : (
          <MentionsList
            brandId={brandId}
            brandName={brandName}
            initialTopic={current.filters.topic ?? ""}
            initialSentiment={current.filters.sentiment ?? ""}
            initialSourceCategory={current.filters.sourceCategory ?? ""}
            initialSourceType={current.filters.sourceType ?? ""}
            initialIssueCategory={current.filters.issueCategory ?? ""}
            initialEntity={current.filters.entity ?? ""}
            initialState={current.filters.state ?? ""}
            initialQ={current.filters.q ?? ""}
            onArticleClick={setArticle}
          />
        )}
      </div>
    </div>
  );
}
