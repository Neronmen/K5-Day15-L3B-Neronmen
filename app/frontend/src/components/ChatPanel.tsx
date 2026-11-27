"use client";

import { useEffect, useRef, useState } from "react";
import { SendHorizontal } from "lucide-react";

import { api } from "@/lib/api";
import { streamChat } from "@/lib/sse";
import type { ChatMessage, Citation } from "@/lib/types";
import { Answer } from "./Answer";
import { cn } from "./ui";

type Msg = Pick<ChatMessage, "role" | "content" | "citations"> & { id: string; streaming?: boolean; error?: boolean };

export function ChatPanel({
  title,
  badge,
  intro,
  historyPath,
  postPath,
  suggestions,
  placeholder,
  onCite,
  className,
}: {
  title: string;
  badge?: React.ReactNode;
  intro: React.ReactNode;
  historyPath: string;
  postPath: string;
  suggestions: string[];
  placeholder: string;
  onCite: (c: Citation) => void;
  className?: string;
}) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<ChatMessage[]>(historyPath)
      .then((rows) => setMsgs(rows.map((m) => ({ id: m.id, role: m.role, content: m.content, citations: m.citations }))))
      .catch(() => setMsgs([]));
  }, [historyPath]);

  useEffect(() => {
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight });
  }, [msgs]);

  async function send(q: string) {
    const question = q.trim();
    if (!question || busy) return;
    setBusy(true);
    setNotice(null);
    setInput("");
    const aid = `a-${Date.now()}`;
    setMsgs((m) => [
      ...m,
      { id: `u-${Date.now()}`, role: "user", content: question, citations: [] },
      { id: aid, role: "assistant", content: "", citations: [], streaming: true },
    ]);
    const patch = (fn: (m: Msg) => Msg) => setMsgs((all) => all.map((m) => (m.id === aid ? fn(m) : m)));
    try {
      await streamChat(postPath, question, (e) => {
        if (e.type === "start" && typeof e.remaining_today === "number" && e.remaining_today <= 5) {
          setNotice(`Còn ${e.remaining_today} lượt hỏi AI hôm nay.`);
        } else if (e.type === "delta") patch((m) => ({ ...m, content: m.content + e.text }));
        else if (e.type === "done") patch((m) => ({ ...m, citations: e.citations, streaming: false }));
        else if (e.type === "error") patch((m) => ({ ...m, content: m.content || e.message, streaming: false, error: true }));
      });
      patch((m) => ({ ...m, streaming: false }));
    } catch (err) {
      patch((m) => ({ ...m, content: (err as Error).message, streaming: false, error: true }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={cn("flex min-h-0 flex-col rounded-xl border border-line bg-surface p-4", className)}>
      <div className="flex flex-wrap items-center gap-2 border-b border-line pb-3">
        <h2 className="mr-auto text-base font-semibold">{title}</h2>
        {badge}
      </div>
      <div ref={boxRef} className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto py-3" aria-live="polite">
        {msgs.length === 0 && <div className="max-w-[92%] self-start rounded-xl rounded-bl-sm bg-sunken px-3.5 py-2.5 text-sm">{intro}</div>}
        {msgs.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="max-w-[88%] self-end whitespace-pre-wrap break-words rounded-xl rounded-br-sm bg-accent px-3.5 py-2.5 text-sm text-accent-ink">
              {m.content}
            </div>
          ) : (
            <div
              key={m.id}
              className={cn("max-w-[94%] self-start rounded-xl rounded-bl-sm bg-sunken px-3.5 py-2.5", m.error && "bg-bad-soft text-bad")}
            >
              {m.content ? (
                <Answer text={m.content} citations={m.citations} streaming={m.streaming} onCite={onCite} />
              ) : (
                <span className="inline-flex gap-1" aria-label="AI đang trả lời">
                  {[0, 1, 2].map((i) => (
                    <i key={i} className="size-1.5 animate-pulse rounded-full bg-muted" style={{ animationDelay: `${i * 150}ms` }} />
                  ))}
                </span>
              )}
            </div>
          ),
        )}
      </div>
      {msgs.length === 0 && (
        <div className="flex flex-wrap gap-1.5 pb-2.5">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => send(s)}
              className="rounded-full border border-line px-3 py-1 text-xs text-muted hover:border-accent hover:text-accent"
            >
              {s}
            </button>
          ))}
        </div>
      )}
      {notice && <p className="pb-2 text-xs text-warn">{notice}</p>}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2 border-t border-line pt-3"
      >
        <textarea
          aria-label="Câu hỏi"
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          placeholder={placeholder}
          className="max-h-32 min-w-0 flex-1 resize-none rounded-[9px] border border-line bg-surface px-3 py-2 text-sm"
        />
        <button
          disabled={busy || !input.trim()}
          aria-label="Gửi"
          className="grid size-10 flex-none place-items-center rounded-[9px] bg-accent text-accent-ink disabled:opacity-50"
        >
          <SendHorizontal size={17} />
        </button>
      </form>
    </div>
  );
}
