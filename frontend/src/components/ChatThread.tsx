import { useEffect, useRef } from "react";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  messages: ChatMessage[];
  isStreaming?: boolean;
}

export function ChatThread({ messages, isStreaming = false }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 px-3 py-2 overflow-y-auto max-h-80">
      {messages.map((msg, i) => {
        const isLast = i === messages.length - 1;
        const showCursor = isStreaming && isLast && msg.role === "assistant";
        return (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] text-sm rounded-2xl px-3 py-2 leading-relaxed ${
                msg.role === "user"
                  ? "bg-blue-600/30 text-white"
                  : "bg-white/5 text-white/85"
              }`}
            >
              {msg.content}
              {showCursor && (
                <span className="inline-block w-0.5 h-3.5 bg-white/60 ml-0.5 align-middle animate-pulse" />
              )}
            </div>
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
