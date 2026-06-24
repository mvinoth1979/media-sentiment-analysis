import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { postGenerate, type GenerateResponse } from "../lib/api";

type ReviewState = "draft" | "review" | "approved";

interface Props {
  brandId: string;
  defaultTopic?: string;
}

type Format = "press_release" | "faq" | "tweet" | "linkedin" | "ceo_statement";

const FORMATS: { key: Format; label: string; icon: string; limit?: number; desc: string }[] = [
  { key: "press_release", label: "Press Release", icon: "📰", desc: "Formal 400-word release for media distribution" },
  { key: "faq",          label: "FAQ",            icon: "❓", desc: "5 consumer-facing Q&As — empathetic and clear" },
  { key: "tweet",        label: "Tweet",          icon: "🐦", limit: 280, desc: "280-char statement for social media" },
  { key: "linkedin",     label: "LinkedIn",       icon: "💼", desc: "150-word business post with engagement hook" },
  { key: "ceo_statement",label: "CEO Statement",  icon: "🎙", desc: "200-word executive statement — decisive, accountable" },
];

function ConfidenceBadge({ pct }: { pct: number }) {
  const color = pct >= 75 ? "text-emerald-400 bg-emerald-500/10" : pct >= 50 ? "text-amber-400 bg-amber-500/10" : "text-red-400 bg-red-500/10";
  return (
    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded ${color}`}>
      AI {pct}% confident
    </span>
  );
}

const LANGUAGES = ["English", "Tamil", "Hindi", "Telugu", "Kannada", "Malayalam"];

export function ContentGenerator({ brandId, defaultTopic = "" }: Props) {
  const [format, setFormat] = useState<Format>("press_release");
  const [topic, setTopic] = useState(defaultTopic);
  const [language, setLanguage] = useState("English");
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [reviewState, setReviewState] = useState<ReviewState>("draft");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { mutate, isPending } = useMutation({
    mutationFn: () => postGenerate(brandId, format, topic, language),
    onSuccess: (data) => { setResult(data); setReviewState("draft"); },
  });

  const selectedFormat = FORMATS.find(f => f.key === format)!;
  const charCount = result?.char_count ?? 0;
  const isTweet = format === "tweet";

  const handleCopy = () => {
    if (result?.content) {
      navigator.clipboard.writeText(result.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <div className="bg-[#111e36] border border-white/10 rounded-xl flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/8 flex-none">
        <span className="text-[11px] font-semibold text-white">Response Studio</span>
        <span className="text-[9px] text-white/30">AI-generated content drafts</span>
      </div>

      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {/* Format selector */}
        <div className="flex gap-1 px-3 py-2 border-b border-white/5 overflow-x-auto flex-none" style={{ scrollbarWidth: "none" }}>
          {FORMATS.map(f => (
            <button
              key={f.key}
              onClick={() => { setFormat(f.key); setResult(null); }}
              title={f.desc}
              className={`flex items-center gap-1 text-[9px] px-2 py-1 rounded whitespace-nowrap transition-colors flex-none ${
                format === f.key
                  ? "bg-blue-600/30 text-blue-300 border border-blue-500/30"
                  : "text-white/40 hover:text-white/70"
              }`}
            >
              {f.icon} {f.label}
            </button>
          ))}
        </div>

        {/* Language selector */}
        <div className="flex items-center gap-2 px-3 py-1.5 border-b border-white/5 flex-none overflow-x-auto" style={{ scrollbarWidth: "none" }}>
          <span className="text-[9px] text-white/30 uppercase tracking-wider shrink-0">Language:</span>
          {LANGUAGES.map(lang => (
            <button
              key={lang}
              onClick={() => { setLanguage(lang); setResult(null); }}
              className={`text-[9px] px-2 py-0.5 rounded-full border flex-none transition-colors ${
                language === lang
                  ? "bg-blue-600/30 text-blue-300 border-blue-500/40"
                  : "text-white/35 border-white/10 hover:text-white/60 hover:border-white/20"
              }`}
            >
              {lang}
            </button>
          ))}
        </div>

        {/* Topic input + Generate */}
        <div className="flex gap-2 px-3 py-2 border-b border-white/5 flex-none">
          <input
            type="text"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === "Enter" && topic.trim() && mutate()}
            placeholder={`Topic for ${selectedFormat.label.toLowerCase()}…`}
            className="flex-1 bg-white/5 border border-white/10 rounded px-2.5 py-1.5 text-[11px] text-white placeholder-white/25 outline-none focus:border-blue-500/50 transition-colors"
          />
          <button
            onClick={() => mutate()}
            disabled={isPending || !topic.trim()}
            className="shrink-0 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-[10px] font-semibold px-3 py-1.5 rounded transition-colors flex items-center gap-1"
          >
            {isPending ? (
              <><span className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> Generating…</>
            ) : (
              <>✦ Generate</>
            )}
          </button>
        </div>

        {/* Result area */}
        <div className="flex-1 min-h-0 px-3 py-2 overflow-y-auto" style={{ scrollbarWidth: "none" }}>
          {!result ? (
            <div className="flex flex-col items-center justify-center h-full gap-2 text-center">
              <span className="text-[28px] opacity-20">{selectedFormat.icon}</span>
              <span className="text-[11px] text-white/25">{selectedFormat.desc}</span>
              {!topic.trim() && <span className="text-[10px] text-white/15">Enter a topic above to generate</span>}
            </div>
          ) : result.confidence_pct === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-4">
              <span className="text-[28px]">⚠️</span>
              <p className="text-[11px] text-amber-400/80">AI generation failed — the Gemini API key may have quota limits or network issues.</p>
              <button
                onClick={() => { setResult(null); mutate(); }}
                disabled={isPending}
                className="text-[10px] bg-blue-600/20 border border-blue-500/30 text-blue-400 hover:bg-blue-600/30 px-3 py-1.5 rounded transition-colors"
              >
                ↺ Retry
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Meta row */}
              <div className="flex items-center gap-2 flex-wrap">
                <ConfidenceBadge pct={result.confidence_pct} />
                <span className="text-[9px] text-white/25">
                  {isTweet
                    ? `${charCount}/280 chars`
                    : `${result.word_count} words`}
                </span>
                <span className="text-[9px] text-white/15 ml-auto">
                  {new Date(result.generated_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>

              {/* Content textarea */}
              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={result.content}
                  onChange={e => setResult(prev => prev ? { ...prev, content: e.target.value, word_count: e.target.value.split(/\s+/).filter(Boolean).length, char_count: e.target.value.length } : null)}
                  rows={isTweet ? 4 : 10}
                  className="w-full bg-[#1a2744] border border-white/8 rounded-lg p-2.5 text-[11px] text-white/80 leading-relaxed outline-none focus:border-white/20 resize-none transition-colors"
                  style={{ minHeight: isTweet ? 80 : 180 }}
                />
                {isTweet && (
                  <div className={`absolute bottom-2 right-2 text-[9px] font-semibold ${charCount > 280 ? "text-red-400" : charCount > 240 ? "text-amber-400" : "text-white/25"}`}>
                    {charCount}/280
                  </div>
                )}
              </div>

              {/* Approval workflow */}
              {reviewState !== "draft" && (
                <div className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-[10px] ${reviewState === "approved" ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" : "bg-amber-500/10 border border-amber-500/20 text-amber-400"}`}>
                  {reviewState === "approved" ? "✓ Approved — ready to publish" : "⏳ Submitted for review"}
                  {reviewState === "review" && (
                    <button onClick={() => setReviewState("approved")} className="ml-auto text-[9px] bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 px-2 py-0.5 rounded transition-colors">
                      Approve
                    </button>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={handleCopy}
                  className="text-[10px] border border-white/15 hover:border-white/30 text-white/60 hover:text-white px-2.5 py-1 rounded transition-colors"
                >
                  {copied ? "✓ Copied" : "Copy"}
                </button>
                <button
                  onClick={() => { setResult(null); setReviewState("draft"); mutate(); }}
                  disabled={isPending}
                  className="text-[10px] border border-white/10 hover:border-white/20 text-white/40 hover:text-white/70 px-2.5 py-1 rounded transition-colors disabled:opacity-40"
                >
                  Regenerate
                </button>
                {reviewState === "draft" && (
                  <button
                    onClick={() => setReviewState("review")}
                    className="text-[10px] border border-blue-500/25 text-blue-400/70 hover:text-blue-400 hover:border-blue-400/50 px-2.5 py-1 rounded transition-colors ml-auto"
                  >
                    Submit for Review →
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
