"use client";

import { useMemo, useState } from "react";
import { Send } from "lucide-react";

import { api } from "@/lib/api";
import { fmtDay, parseYmd, vnWeekday, WEEKDAYS, ymd } from "@/lib/schedule";
import type { AnnouncementKind, ClassSession } from "@/lib/types";
import { Button, ErrorText, Field, Input, Select, Textarea, cn } from "./ui";

const KINDS: { id: AnnouncementKind; label: string }[] = [
  { id: "cancel", label: "Báo nghỉ học" },
  { id: "makeup", label: "Báo học bù" },
  { id: "general", label: "Thông báo chung" },
];

/** Form đăng thông báo cho một lớp: báo nghỉ (một buổi / cả ngày), học bù, hoặc thông báo chung. */
export function AnnouncementForm({ classId, sessions, onDone }: { classId: string; sessions: ClassSession[]; onDone: () => void }) {
  const [kind, setKind] = useState<AnnouncementKind>("cancel");
  const [date, setDate] = useState(() => ymd(new Date()));
  const [sessionId, setSessionId] = useState("");
  const [start, setStart] = useState("14:00");
  const [end, setEnd] = useState("15:30");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [pinned, setPinned] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Chỉ cho chọn các buổi học rơi đúng thứ của ngày nghỉ
  const sameDay = useMemo(() => (date ? sessions.filter((s) => s.weekday === vnWeekday(parseYmd(date))) : []), [date, sessions]);
  const effectiveSession = sameDay.some((s) => s.id === sessionId) ? sessionId : "";

  const autoTitle =
    kind === "cancel" && date ? `Nghỉ học ${fmtDay(date)}` : kind === "makeup" && date ? `Học bù ${fmtDay(date)}, ${start}–${end}` : "";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setOk(null);
    const finalTitle = title.trim() || autoTitle;
    if (!finalTitle) return setError("Nhập tiêu đề thông báo.");
    setBusy(true);
    try {
      await api(`/teacher/classes/${classId}/announcements`, {
        json: {
          kind,
          title: finalTitle,
          body,
          pinned,
          event_date: kind === "general" ? null : date,
          session_id: kind === "cancel" && effectiveSession ? effectiveSession : null,
          event_start: kind === "makeup" ? start : null,
          event_end: kind === "makeup" ? end : null,
        },
      });
      setTitle("");
      setBody("");
      setPinned(false);
      setOk("Đã gửi thông báo tới học sinh trong lớp.");
      onDone();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <div role="radiogroup" aria-label="Loại thông báo" className="grid grid-cols-3 gap-1 rounded-[10px] bg-sunken p-1">
        {KINDS.map((k) => (
          <button
            key={k.id}
            type="button"
            role="radio"
            aria-checked={kind === k.id}
            onClick={() => setKind(k.id)}
            className={cn(
              "rounded-lg px-2 py-1.5 text-sm font-medium text-muted",
              kind === k.id && "bg-surface text-ink shadow-sm",
            )}
          >
            {k.label}
          </button>
        ))}
      </div>

      {kind !== "general" && (
        <Field label={kind === "cancel" ? "Ngày nghỉ" : "Ngày học bù"} htmlFor="ev-date">
          <Input id="ev-date" type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
        </Field>
      )}
      {kind === "cancel" && (
        <Field label="Buổi nghỉ" htmlFor="ev-session">
          <Select id="ev-session" value={effectiveSession} onChange={(e) => setSessionId(e.target.value)}>
            <option value="">Nghỉ cả ngày</option>
            {sameDay.map((s) => (
              <option key={s.id} value={s.id}>
                {WEEKDAYS[s.weekday]} {s.start_time}–{s.end_time}
                {s.room ? ` · ${s.room}` : ""}
              </option>
            ))}
          </Select>
          {date && sameDay.length === 0 && (
            <span className="text-xs text-muted">Lớp không có buổi học cố định vào {WEEKDAYS[vnWeekday(parseYmd(date))]}.</span>
          )}
        </Field>
      )}
      {kind === "makeup" && (
        <div className="grid grid-cols-2 gap-3">
          <Field label="Từ" htmlFor="ev-start">
            <Input id="ev-start" type="time" required value={start} onChange={(e) => setStart(e.target.value)} />
          </Field>
          <Field label="Đến" htmlFor="ev-end">
            <Input id="ev-end" type="time" required value={end} onChange={(e) => setEnd(e.target.value)} />
          </Field>
        </div>
      )}
      <Field label="Tiêu đề" htmlFor="an-title" hint={autoTitle ? "(để trống sẽ dùng tiêu đề gợi ý)" : undefined}>
        <Input
          id="an-title"
          maxLength={200}
          placeholder={autoTitle || "VD: Mang máy tính bỏ túi buổi sau"}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </Field>
      <Field label="Nội dung" htmlFor="an-body" hint="(không bắt buộc)">
        <Textarea
          id="an-body"
          rows={3}
          maxLength={5000}
          placeholder={kind === "cancel" ? "VD: Cô đi tập huấn. Các em tự ôn bài 3, buổi sau kiểm tra 15 phút." : ""}
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
      </Field>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="accent-accent" checked={pinned} onChange={(e) => setPinned(e.target.checked)} />
        Ghim lên đầu trang lớp
      </label>
      <ErrorText error={error} />
      {ok && <p className="text-sm text-ok">{ok}</p>}
      <Button variant="primary" disabled={busy}>
        <Send size={15} /> {busy ? "Đang gửi…" : "Gửi cho cả lớp"}
      </Button>
    </form>
  );
}
