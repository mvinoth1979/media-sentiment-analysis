import { SentimentBadge } from "../ui/SentimentBadge";
import { formatCount } from "../../lib/utils";
import type { ArticleItem, DrillFilters } from "../../lib/types";

interface Props {
  article: ArticleItem;
  onBack: () => void;
  onDrillInto: (label: string, filters: DrillFilters) => void;
}

const SENTIMENT_COLOR: Record<string, string> = {
  positive: "emerald",
  negative: "red",
  neutral:  "amber",
};

function MetaChip({ label, color, onClick }: { label: string; color: string; onClick?: () => void }) {
  const base = `text-[10px] px-1.5 py-0.5 rounded inline-block mb-1 mr-1 transition-colors`;
  const colors = `bg-${color}-500/15 text-${color}-400 ${onClick ? "cursor-pointer hover:bg-" + color + "-500/30" : ""}`;
  return onClick
    ? <button className={`${base} ${colors}`} onClick={onClick}>{label}</button>
    : <span className={`${base} ${colors}`}>{label}</span>;
}

export function ArticleDetail({ article, onBack, onDrillInto }: Props) {
  const sentColor = SENTIMENT_COLOR[article.sentiment_label] ?? "amber";
  const scoreSign = article.sentiment_score >= 0 ? "+" : "";
  const reach = article.metrics?.estimated_reach ?? article.reach_metadata?.view_count ?? null;
  const pubDate = article.published_at
    ? new Date(article.published_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })
    : "—";

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white transition-colors group"
      >
        <svg className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to article list
      </button>

      <div className="bg-[#1a2744] border border-white/10 rounded-xl p-5 space-y-4">
        {/* Title */}
        <div>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-semibold text-white hover:text-blue-400 transition-colors leading-snug block"
          >
            {article.title}
          </a>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-2 text-[10px] text-white/40">
            <span>{article.portal_id.replace(/_/g, " ")}</span>
            {article.author && <span>· By {article.author}</span>}
            <span>· {pubDate}</span>
            <span className="uppercase">{article.language}</span>
          </div>
        </div>

        {/* Sentiment + signals row */}
        <div className="flex flex-wrap items-center gap-2">
          <SentimentBadge label={article.sentiment_label} />
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full bg-${sentColor}-500/15 text-${sentColor}-400`}>
            {scoreSign}{article.sentiment_score.toFixed(2)}
          </span>
          {article.issue_category && (
            <button
              onClick={() => onDrillInto(`Issue: ${article.issue_category!.replace(/_/g, " ")}`, { issueCategory: article.issue_category! })}
              className="text-xs px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-400 hover:bg-purple-500/25 transition-colors"
            >
              {article.issue_category.replace(/_/g, " ")}
            </button>
          )}
          {article.editorial_tone && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400">
              {article.editorial_tone.replace(/_/g, " ")}
            </span>
          )}
        </div>

        {/* Metric cards */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-white/5 rounded-lg p-3 space-y-1">
            <div className="text-[10px] text-white/40 font-medium uppercase tracking-wide">Source signals</div>
            <div className="text-white/70">Credibility: <span className="font-semibold text-white">{(article.source_credibility * 100).toFixed(0)}%</span></div>
            <div className="text-white/70">Platform: <span className="font-semibold text-white">{(article.source_type ?? "news").replace(/_/g, " ")}</span></div>
            {article.is_regulatory_source && (
              <div className="text-[10px] text-blue-400 pt-0.5">🛡 Government / Regulatory source</div>
            )}
          </div>
          <div className="bg-white/5 rounded-lg p-3 space-y-1">
            <div className="text-[10px] text-white/40 font-medium uppercase tracking-wide">Reach</div>
            {reach ? (
              <div className="text-white/70">
                {article.reach_metadata?.view_count ? "Views" : "Est. reach"}:{" "}
                <span className="font-semibold text-white">{formatCount(reach)}</span>
              </div>
            ) : (
              <div className="text-white/30 text-[10px]">No reach data</div>
            )}
            {article.reach_metadata?.like_count ? (
              <div className="text-white/70">Likes: <span className="font-semibold text-white">{formatCount(article.reach_metadata.like_count)}</span></div>
            ) : null}
          </div>
        </div>

        {/* Clickable tags — each tag drills further */}
        <div className="space-y-2">
          {article.entities.length > 0 && (
            <div>
              <span className="text-[10px] text-white/40 mr-2">Entities</span>
              {article.entities.slice(0, 10).map(e => (
                <MetaChip
                  key={e} label={e} color="emerald"
                  onClick={() => onDrillInto(`Entity: ${e}`, { entity: e })}
                />
              ))}
            </div>
          )}
          {article.keywords.length > 0 && (
            <div>
              <span className="text-[10px] text-white/40 mr-2">Keywords</span>
              {article.keywords.slice(0, 10).map(k => (
                <MetaChip
                  key={k} label={k} color="slate"
                  onClick={() => onDrillInto(`Keyword: ${k}`, { q: k })}
                />
              ))}
            </div>
          )}
          {article.states_mentioned.length > 0 && (
            <div>
              <span className="text-[10px] text-white/40 mr-2">States</span>
              {article.states_mentioned.map(s => (
                <MetaChip
                  key={s} label={s} color="blue"
                  onClick={() => onDrillInto(`State: ${s}`, { state: s })}
                />
              ))}
            </div>
          )}
          {article.topics.length > 0 && (
            <div>
              <span className="text-[10px] text-white/40 mr-2">Topics</span>
              {article.topics.map(t => (
                <MetaChip
                  key={t} label={t.replace(/_/g, " ")} color="indigo"
                  onClick={() => onDrillInto(`Topic: ${t.replace(/_/g, " ")}`, { topic: t })}
                />
              ))}
            </div>
          )}
        </div>

        {/* Divergence warning */}
        {article.sentiment_divergence && (
          <div className="flex items-start gap-2 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
            <span className="text-amber-400 text-sm">⚠</span>
            <div>
              <div className="text-xs font-medium text-amber-400">Sentiment Divergence Detected</div>
              <div className="text-[10px] text-amber-400/70 mt-0.5">Headline sentiment differs from body — manual review recommended</div>
            </div>
          </div>
        )}

        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors font-medium"
        >
          Read original article
          <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </div>
  );
}
