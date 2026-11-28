"use client";

import { useMemo, useState } from "react";
import { ChevronDown, Flag, Sparkles } from "lucide-react";

import { Answer } from "@/components/Answer";
import { Avatar, Button, Card, CardHeader, Empty, ErrorText, Loading, Pill, cn } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate, initials } from "@/lib/format";
import type { ChatLog } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

/** Lịch sử hỏi AI cho giáo viên: mỗi học sinh một thẻ (cờ đỏ đếm bằng code + một dòng AI tóm tắt),
 *  bấm vào để xem hội thoại dạng khung chat, tách theo từng bài. */

type Level = "ok" | "watch" | "alert";
interface Insight { student_id: string; focus: string; stuck: string; red_flag: string | null; level: Level }

const FLAG_LABEL: Record<string, string> = { jailbreak: "Cố bẻ khoá AI", impersonation: "Tự nhận là giáo viên", ask_answer: "Xin đáp án khi còn hạn" };
const LEVEL: Record<Level, { tone: "ok" | "warn" | "bad"; label: string }> = {
  ok: { tone: "ok", label: "Đang tự học" },
  watch: { tone: "warn", label: "Cần để ý" },
  alert: { tone: "bad", label: "Cần kiểm tra" },
};
const RANK: Record<Level, number> = { ok: 0, watch: 1, alert: 2 };

interface StudentGroup {
  id: string;
  name: string;
  messages: ChatLog[]; // cũ → mới
  questions: number;
  flags: Record<string, number>;
  contexts: string[];
  last: string;
}

function codeLevel(flags: Record<string, number>): Level {
  const n = Object.values(flags).reduce((a, b) => a + b, 0);
  if (n >= 2 || flags.jailbreak || flags.impersonation) return "alert";
  return n ? "watch" : "ok";
}

function group(logs: ChatLog[]): StudentGroup[] {
  const map = new Map<string, StudentGroup>();
  for (const m of [...logs].reverse()) {
    const g: StudentGroup = map.get(m.student_id) ?? {
      id: m.student_id, name: m.student_name, messages: [], questions: 0, flags: {}, contexts: [], last: m.created_at ?? "",
    };
    g.messages.push(m);
    g.last = m.created_at ?? g.last;
    if (m.role === "user") g.questions++;
    if (m.flagged) g.flags[m.flagged] = (g.flags[m.flagged] ?? 0) + 1;
    if (!g.contexts.includes(m.context)) g.contexts.push(m.context);
    map.set(m.student_id, g);
  }
  return [...map.values()];
}

export function ChatInsights({ classId }: { classId: string }) {
  const { data, error } = useLoad<ChatLog[]>(`/teacher/classes/${classId}/chats`);
  const [insights, setInsights] = useState<Record<string, Insight> | null>(null);
  const [busy, setBusy] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [onlyFlags, setOnlyFlags] = useState(false);
  const [open, setOpen] = useState<string | null>(null);

  const groups = useMemo(() => {
    const gs = group(data ?? []);
    const lvl = (g: StudentGroup) => {
      const c = codeLevel(g.flags);
      const a = insights?.[g.id]?.level ?? "ok";
      return RANK[a] > RANK[c] ? a : c;
    };
    return gs
      .map((g) => ({ ...g, level: lvl(g) }))
      .filter((g) => !onlyFlags || g.level !== "ok")
      .sort((a, b) => RANK[b.level] - RANK[a.level] || b.last.localeCompare(a.last));
  }, [data, insights, onlyFlags]);

  async function summarize() {
    setBusy(true);
    setAiError(null);
    try {
      const out = await api<{ students: Insight[] }>(`/teacher/classes/${classId}/chats/insights`, { method: "POST" });
      setInsights(Object.fromEntries(out.students.map((s) => [s.student_id, s])));
    } catch (e) {
      setAiError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const alerts = groups.filter((g) => g.level === "alert").length;

  return (
    <Card>
      <CardHeader title="Học sinh đã hỏi AI những gì">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="accent-accent" checked={onlyFlags} onChange={(e) => setOnlyFlags(e.target.checked)} />
            Chỉ em cần để ý
          </label>
          <Button size="sm" variant="primary" onClick={summarize} disabled={busy || !data?.length}>
            <Sparkles size={15} /> {busy ? "AI đang đọc…" : insights ? "Tóm tắt lại" : "AI tóm tắt lớp"}
          </Button>
        </div>
      </CardHeader>
      <ErrorText error={error ?? aiError} />
      {!data ? (
        <Loading />
      ) : groups.length === 0 ? (
        <Empty>{onlyFlags ? "Không có em nào cần để ý." : "Học sinh chưa hỏi AI."}</Empty>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-muted">
            {groups.length} học sinh{alerts ? <> · <b className="text-bad">{alerts} em cần kiểm tra</b></> : null}
            {!insights && " · bấm “AI tóm tắt lớp” để xem mỗi em đang tìm gì"}
          </p>
          {groups.map((g) => (
            <StudentCard key={g.id} g={g} level={g.level} insight={insights?.[g.id]} open={open === g.id}
              onToggle={() => setOpen(open === g.id ? null : g.id)} />
          ))}
        </div>
      )}
    </Card>
  );
}

function StudentCard({ g, level, insight, open, onToggle }: {
  g: StudentGroup; level: Level; insight?: Insight; open: boolean; onToggle: () => void;
}) {
  const [ctx, setCtx] = useState(g.contexts[g.contexts.length - 1]);
  const lv = LEVEL[level];
  return (
    <div className={cn("rounded-2xl border bg-surface transition", level === "alert" ? "border-bad/50" : level === "watch" ? "border-warn/40" : "border-line")}>
      <button onClick={onToggle} className="flex w-full items-start gap-3 p-4 text-left" aria-expanded={open}>
        <Avatar text={initials(g.name)} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <b className="text-[0.95rem]">{g.name}</b>
            <Pill tone={lv.tone}>{lv.label}</Pill>
            {Object.entries(g.flags).map(([k, n]) => (
              <span key={k} className="inline-flex items-center gap-1 rounded-full bg-bad-soft px-2 py-0.5 text-[0.72rem] font-semibold text-bad">
                <Flag size={11} /> {FLAG_LABEL[k] ?? k}{n > 1 ? ` ×${n}` : ""}
              </span>
            ))}
          </div>
          <p className="mt-0.5 text-xs text-faint">
            {g.questions} câu hỏi · {g.contexts.length} bài / tài liệu · lần cuối {fmtDate(g.last)}
          </p>
          {insight && (
            <div className="mt-2 grid gap-1 text-sm">
              <p><span className="text-faint">Đang tìm:</span> {insight.focus}</p>
              {insight.stuck && <p><span className="text-faint">Kẹt ở:</span> {insight.stuck}</p>}
              {insight.red_flag && <p className="text-bad"><span className="font-semibold">Cờ đỏ:</span> {insight.red_flag}</p>}
            </div>
          )}
        </div>
        <ChevronDown size={18} className={cn("mt-1 shrink-0 text-faint transition", open && "rotate-180")} />
      </button>
      {open && (
        <div className="border-t border-line p-4">
          {g.contexts.length > 1 && (
            <div className="no-scrollbar mb-3 flex gap-1.5 overflow-x-auto">
              {g.contexts.map((c) => (
                <button key={c} onClick={() => setCtx(c)}
                  className={cn("whitespace-nowrap rounded-full border px-3 py-1 text-xs", c === ctx ? "border-accent bg-accent-soft text-accent" : "border-line text-muted hover:text-ink")}>
                  {c}
                </button>
              ))}
            </div>
          )}
          <div className="flex max-h-[460px] flex-col gap-3 overflow-y-auto rounded-xl bg-sunken p-3">
            {g.messages.filter((m) => m.context === ctx).map((m) =>
              m.role === "user" ? (
                <div key={m.id} className="flex max-w-[85%] flex-col items-end gap-1 self-end">
                  <div className="whitespace-pre-wrap break-words rounded-2xl rounded-br-md border border-accent/25 bg-accent-soft px-4 py-2.5 text-sm text-ink">
                    {m.content}
                  </div>
                  <div className="flex items-center gap-2 text-[0.7rem] text-faint">
                    {m.flagged && <span className="font-semibold text-bad">⚑ {FLAG_LABEL[m.flagged] ?? m.flagged}</span>}
                    {fmtDate(m.created_at)}
                  </div>
                </div>
              ) : (
                <div key={m.id} className="max-w-[92%] self-start rounded-2xl rounded-tl-md border border-line bg-surface px-4 py-3">
                  <div className="mb-1 flex items-center gap-2 text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-faint">
                    Gia sư {m.mode === "hint" ? "· gợi ý" : m.mode === "answer" ? "· sau hạn" : ""}
                  </div>
                  <Answer text={m.content} citations={m.citations ?? []} />
                </div>
              ),
            )}
          </div>
        </div>
      )}
    </div>
  );
}
