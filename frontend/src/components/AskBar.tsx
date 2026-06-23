import { useState, useRef, useEffect, useCallback } from "react";
import { supabase } from "../lib/supabase";
import { ChatThread, type ChatMessage } from "./ChatThread";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const EXAMPLE_QUERIES = [
  "Why did sentiment drop?",
  "What's the top risk?",
  "Which region needs attention?",
  "Compare with competitors",
];

interface Props {
  brandId: string;
  days?: number;
}

export function AskBar({ brandId, days = 7 }: Props) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Keyboard shortcut: Ctrl/Cmd+K to open
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const send = useCallback(async (text: string) => {
    if (!text.trim() || streaming) return;
    const userMsg: ChatMessage = { role: "user", content: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setOpen(true);
    setStreaming(true);

    // Optimistic empty assistant bubble
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
        body: JSON.stringify({
          message: userMsg.content,
          brand_id: brandId,
          context_messages: messages,
        }),
        signal: abortRef.current.signal,
      });

      if (!resp.ok || !resp.body) throw new Error("Stream failed");

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
          } catch { /* ignore malformed SSE */ }
        }
      }
    } catch (e: unknown) {
      if ((e as Error).name !== "AbortError") {
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant" && !last.content) {
            updated[updated.length - 1] = { ...last, content: "Error getting response. Please try again." };
          }
          return updated;
        });
      }
    } finally {
      setStreaming(false);
    }
  }, [brandId, days, messages, streaming]);

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  return (
    <div
      className="fixed bottom-4 z-30 transition-all duration-200"
      style={{ left: "80px", right: "16px" }}
    >
      <div className="bg-[#1a2744] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        {/* Chat thread — only shown when open and there are messages */}
        {open && messages.length > 0 && (
          <ChatThread messages={messages} isStreaming={streaming} />
        )}

        {/* Example query chips — shown when open and no messages yet */}
        {open && messages.length === 0 && (
          <div className="flex flex-wrap gap-1.5 px-3 pt-2.5 pb-1">
            {EXAMPLE_QUERIES.map(q => (
              <button
                key={q}
                onClick={() => send(q)}
                className="text-[11px] text-white/50 border border-white/10 rounded-full px-2.5 py-0.5 hover:text-white/80 hover:border-white/25 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input row */}
        <div className="flex items-center gap-2 px-3 py-2">
          <button
            onClick={() => { setOpen(o => !o); setTimeout(() => inputRef.current?.focus(), 50); }}
            className="text-white/30 hover:text-white/60 transition-colors shrink-0 text-base"
            title={open ? "Collapse" : "Expand"}
          >
            {open ? "▾" : "▸"}
          </button>
          <span className="text-white/15 text-xs shrink-0">⌘K</span>
          {!open && messages.length === 0 && (
            <div className="flex gap-1.5 overflow-hidden">
              {EXAMPLE_QUERIES.slice(0, 2).map(q => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-[10px] text-white/30 border border-white/8 rounded-full px-2 py-0.5 hover:text-white/60 hover:border-white/20 transition-colors whitespace-nowrap"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            onFocus={() => setOpen(true)}
            placeholder="Ask BrandPulse AI anything about your brand…"
            disabled={streaming}
            className="flex-1 bg-transparent text-sm text-white placeholder-white/25 outline-none min-w-0 disabled:opacity-50"
          />
          {input.trim() && (
            <button
              onClick={() => send(input)}
              disabled={streaming}
              className="shrink-0 text-xs text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-40 font-medium"
            >
              Send
            </button>
          )}
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              className="shrink-0 text-[10px] text-white/25 hover:text-white/50 transition-colors"
              title="Clear chat"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
