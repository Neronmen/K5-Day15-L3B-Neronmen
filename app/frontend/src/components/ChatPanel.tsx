"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Sparkles } from "lucide-react";

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
    <div className={cn("flex min-h-0 flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-card", className)}>
      <div className="flex flex-wrap items-center gap-2.5 border-b border-line px-4 py-3">
        <span className="grid size-7 place-items-center rounded-lg bg-accent-soft text-accent">
          <Sparkles size={15} />
        </span>
        <h2 className="mr-auto text-[0.95rem] font-semibold">{title}</h2>
        {badge}
      </div>
      <div ref={boxRef} className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4" aria-live="polite">
        {msgs.length === 0 && (
          <div className="max-w-[92%] self-start rounded-2xl rounded-tl-md border border-line bg-sunken px-4 py-3 text-sm leading-relaxed text-muted">
            {intro}
          </div>
        )}
        {msgs.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="max-w-[85%] animate-rise self-end whitespace-pre-wrap break-words rounded-2xl rounded-br-md border border-accent/25 bg-accent-soft px-4 py-2.5 text-sm text-ink">
              {m.content}
            </div>
          ) : (
            <div
              key={m.id}
              className={cn(
                "max-w-[94%] animate-rise self-start rounded-2xl rounded-tl-md border border-line bg-sunken px-4 py-3",
                m.error && "border-bad/30 bg-bad-soft text-bad",
              )}
            >
              <div className="mb-1 text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-faint">Gia sư</div>
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
        <div className="flex flex-wrap gap-1.5 px-4 pb-3">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => send(s)}
              className="rounded-full border border-line-strong px-3 py-1.5 text-xs text-muted transition hover:border-accent hover:bg-accent-soft hover:text-ink"
            >
              {s}
            </button>
          ))}
        </div>
      )}
      {notice && <p className="px-4 pb-2 text-xs text-warn">{notice}</p>}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="border-t border-line p-3"
      >
        <div className="flex items-end gap-2 rounded-xl border border-line-strong bg-field p-1.5 pl-3 transition focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/20">
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
          className="max-h-32 min-w-0 flex-1 resize-none bg-transparent py-1.5 text-sm placeholder:text-faint focus:outline-none"
        />
        <button
          disabled={busy || !input.trim()}
          aria-label="Gửi"
          className="grid size-9 flex-none place-items-center rounded-lg bg-accent text-accent-ink transition hover:brightness-105 disabled:bg-sunken disabled:text-faint"
        >
          <ArrowUp size={17} />
        </button>
        </div>
      </form>
    </div>
  );
}
