"use client";

import { useState } from "react";
import { CalendarX, X } from "lucide-react";

import { WeekCalendar } from "@/components/WeekCalendar";
import { Banner, Button, Card, CardHeader, ErrorText, Field, Input, PageHeader, Textarea } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDay } from "@/lib/schedule";
import type { CalendarItem } from "@/lib/types";

export default function TeacherSchedulePage() {
  const [target, setTarget] = useState<CalendarItem | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  function pick(it: CalendarItem) {
    setTarget(it);
    setTitle(`Nghỉ học ${fmtDay(it.date)} (${it.start_time}–${it.end_time})`);
    setBody("");
    setError(null);
    setDone(null);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!target) return;
    setBusy(true);
    setError(null);
    try {
      await api(`/teacher/classes/${target.class_id}/announcements`, {
        json: { kind: "cancel", title: title.trim() || `Nghỉ học ${fmtDay(target.date)}`, body, event_date: target.date, session_id: target.session_id },
      });
      setDone(`Đã báo nghỉ ${target.class_name} (${fmtDay(target.date)}) và gửi thông báo cho học sinh.`);
      setTarget(null);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Thời khoá biểu" title="Lịch dạy" />
      {done && <Banner tone="ok">{done}</Banner>}
      {target && (
        <Card className="max-w-2xl border-bad/50">
          <CardHeader title={`Báo nghỉ: ${target.class_name}`}>
            <Button variant="ghost" size="sm" aria-label="Đóng" onClick={() => setTarget(null)}>
              <X size={15} />
            </Button>
          </CardHeader>
          <p className="mb-3 text-sm text-muted">
            {fmtDay(target.date)}, {target.start_time}–{target.end_time}. Học sinh trong lớp sẽ nhận thông báo và thấy buổi này bị gạch trên lịch.
          </p>
          <form onSubmit={submit} className="flex flex-col gap-3">
            <Field label="Tiêu đề" htmlFor="c-title">
              <Input id="c-title" maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} />
            </Field>
            <Field label="Lý do / dặn dò" htmlFor="c-body" hint="(không bắt buộc)">
              <Textarea id="c-body" rows={3} maxLength={5000} placeholder="VD: Cô bận họp hội đồng. Các em làm trước bài tập 4." value={body} onChange={(e) => setBody(e.target.value)} />
            </Field>
            <ErrorText error={error} />
            <div className="flex justify-end gap-2">
              <Button type="button" onClick={() => setTarget(null)}>
                Huỷ
              </Button>
              <Button variant="primary" disabled={busy}>
                <CalendarX size={15} /> {busy ? "Đang gửi…" : "Báo nghỉ buổi này"}
              </Button>
            </div>
          </form>
        </Card>
      )}
      <WeekCalendar role="teacher" reloadKey={reloadKey} onCancel={pick} />
    </>
  );
}
