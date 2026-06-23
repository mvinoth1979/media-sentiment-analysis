import { useState, useRef, useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { supabase } from "../lib/supabase";
import { fetchRiskForecast, fetchIssueRadar } from "../lib/api";
import { ChatThread, type ChatMessage } from "./ChatThread";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const FOLLOW_UPS = [
  "What's the top risk right now?",
  "Which region needs attention?",
  "How is sentiment trending?",
  "What should I do next?",
  "Compare with last week",
  "Who are the key journalists?",
];

interface Props {
  brandId: string;
  brandName: string;
  days?: number;
  open: boolean;
  onClose: () => void;
}

function PinIcon({ pinned }: { pinned: boolean }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill={pinned ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
      <path d="M12 2l2 7h6l-5 4 2 7-5-4-5 4 2-7-5-4h6z" />
    </svg>
  );
}

function ContextCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="bg-[#0d1626] border border-white/8 rounded-lg px-3 py-2">
      <div className="text-[8px] uppercase tracking-widest text-white/30 mb-0.5">{label}</div>
      <div className={`text-[13px] font-semibold ${color ?? "text-white"}`}>{value}</div>
      {sub && <div className="text-[9px] text-white/30 mt-0.5">{sub}</div>}
    </div>
  );
}

export function CoPilotPanel({ brandId, brandName, days = 7, open, onClose }: Props) {
  const [pinned, setPinned] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [tab, setTab] = useState<"context" | "chat">("context");
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const visible = open || pinned;

  const { data: risk } = useQuery({
    queryKey: ["risk-forecast", brandId, days],
    queryFn: () => fetchRiskForecast(brandId, days),
    staleTime: 15 * 60_000,
    enabled: visible,
  });

  const { data: radar } = useQuery({
    queryKey: ["issue-radar", brandId, days],
    queryFn: () => fetchIssueRadar(brandId, days),
    staleTime: 15 * 60_000,
    enabled: visible,
  });

  const currentRisk = risk?.historical?.at(-1)?.risk_score ?? 0;
  const topIssue = radar?.points?.[0];

  useEffect(() => {
    if (visible && tab === "chat") {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [visible, tab]);

  const send = useCallback(async (text: string) => {
    if (!text.trim() || streaming) return;
    const userMsg: ChatMessage = { role: "user", content: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setTab("chat");
    setStreaming(true);
    setMessages(prev => [...prev, { role: "assistant", content: "" }]);

    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    abortRef.current = new AbortController();

    try {
      const resp = await fetch(`${API_BASE}/dashboard/chat?days=${days}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: userMsg.content, brand_id: brandId, context_messages: messages }),
        signal: abortRef.current.signal,
      });

      if (!resp.ok || !resp.body) throw new Error("Stream error");
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.replace(/^data:\s*/, "").trim();
          if (!line) continue;
          try {
            const { token: tok, done: isDone } = JSON.parse(line);
            if (isDone) break;
            setMessages(prev => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last?.role === "assistant") {
                updated[updated.length - 1] = { ...last, content: last.content + tok };
              }
              return updated;
            });
          } catch { /* ignore */ }
        }
      }
    } catch (e: unknown) {
      if ((e as Error).name !== "AbortError") {
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant" && !last.content) {
            updated[updated.length - 1] = { ...last, content: "Error. Please try again." };
          }
          return updated;
        });
      }
    } finally {
      setStreaming(false);
    }
  }, [brandId, days, messages, streaming]);

  if (!visible) return null;

  return (
    <>
      {/* Backdrop — only shown when not pinned */}
      {!pinned && open && (
        <div
          className="fixed inset-0 z-40"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-[340px] bg-[#0d1626] border-l border-white/10 flex flex-col z-50 transition-transform duration-200 ${visible ? "translate-x-0" : "translate-x-full"}`}
        role="complementary"
        aria-label="AI Co-Pilot"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-none bg-[#111e36]">
          <div className="flex items-center gap-2">
            <span className="text-blue-400 text-sm">✦</span>
            <span className="text-[12px] font-semibold text-white">AI Co-Pilot</span>
            {pinned && <span className="text-[8px] bg-blue-500/20 text-blue-300 rounded px-1.5 py-0.5">Pinned</span>}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] text-white/30 truncate max-w-[100px]">{brandName}</span>
            <button
              onClick={() => setPinned(p => !p)}
              className={`p-1 rounded transition-colors ${pinned ? "text-blue-400 bg-blue-500/15" : "text-white/30 hover:text-white/70"}`}
              title={pinned ? "Unpin panel" : "Pin panel"}
            >
              <PinIcon pinned={pinned} />
            </button>
            <button
              onClick={() => { setPinned(false); onClose(); }}
              className="text-white/30 hover:text-white/70 transition-colors text-base leading-none"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex border-b border-white/8 flex-none">
          {(["context", "chat"] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-2 text-[10px] font-medium capitalize transition-colors ${tab === t ? "text-white border-b border-blue-500" : "text-white/35 hover:text-white/60"}`}
            >
              {t === "context" ? "Context" : `Chat${messages.length > 0 ? ` (${messages.length})` : ""}`}
            </button>
          ))}
        </div>

        {/* Context Tab */}
        {tab === "context" && (
          <div className="flex-1 overflow-y-auto p-3 space-y-3" style={{ scrollbarWidth: "none" }}>
            <div className="text-[9px] uppercase tracking-widest text-white/25 mb-1">Live Snapshot</div>

            <div className="grid grid-cols-2 gap-2">
              <ContextCard
                label="Risk Score"
                value={`${Math.round(currentRisk)}/100`}
                sub={currentRisk >= 65 ? "High risk" : currentRisk >= 40 ? "Medium" : "Low"}
                color={currentRisk >= 65 ? "text-red-400" : currentRisk >= 40 ? "text-amber-400" : "text-emerald-400"}
              />
              {topIssue && (
                <ContextCard
                  label="Top Issue"
                  value={topIssue.issue.replace(/_/g, " ")}
                  sub={`${topIssue.velocity.toFixed(1)}× velocity`}
                  color="text-amber-300"
                />
              )}
            </div>

            {risk?.narrative && (
              <div className="bg-[#0d1626] border border-white/8 rounded-lg px-3 py-2.5">
                <div className="text-[8px] uppercase tracking-widest text-white/25 mb-1">Risk Narrative</div>
                <p className="text-[11px] text-white/60 leading-relaxed">{risk.narrative}</p>
              </div>
            )}

            <div>
              <div className="text-[9px] uppercase tracking-widest text-white/25 mb-2">Ask Me About</div>
              <div className="flex flex-wrap gap-1.5">
                {FOLLOW_UPS.map(q => (
                  <button
                    key={q}
                    onClick={() => send(q)}
                    className="text-[10px] text-white/50 border border-white/10 rounded-full px-2.5 py-0.5 hover:text-white/80 hover:border-white/25 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Chat Tab */}
        {tab === "chat" && (
          <div className="flex-1 flex flex-col min-h-0">
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center p-4 text-center gap-3">
                <span className="text-3xl text-blue-400/40">✦</span>
                <p className="text-[11px] text-white/30 leading-relaxed">
                  Ask anything about {brandName}. I have full context of the last {days} days.
                </p>
              </div>
            ) : (
              <div className="flex-1 min-h-0 overflow-hidden">
                <ChatThread messages={messages} isStreaming={streaming} />
              </div>
            )}

            <div className="border-t border-white/8 p-3 flex items-center gap-2 flex-none">
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }}
                onFocus={() => setTab("chat")}
                placeholder="Ask Co-Pilot…"
                disabled={streaming}
                className="flex-1 bg-[#0d1626] border border-white/10 rounded-lg text-[11px] text-white placeholder-white/25 px-3 py-1.5 outline-none focus:border-blue-500/50 disabled:opacity-50 min-w-0"
              />
              {messages.length > 0 && (
                <button
                  onClick={() => setMessages([])}
                  className="text-[9px] text-white/25 hover:text-white/50 shrink-0"
                  title="Clear"
                >✕</button>
              )}
              {input.trim() && (
                <button
                  onClick={() => send(input)}
                  disabled={streaming}
                  className="text-[10px] text-blue-400 hover:text-blue-300 disabled:opacity-40 font-medium shrink-0"
                >
                  Send
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
