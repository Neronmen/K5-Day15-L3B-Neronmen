"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, CalendarClock, ClipboardList } from "lucide-react";

import { AnnouncementList } from "@/components/AnnouncementList";

import { MyStatusPill } from "@/components/StatusPill";
import { Banner, Button, Card, CardHeader, DueChip, Empty, ErrorText, Input, LinkButton, Loading, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { fmtDate } from "@/lib/format";
import { fmtNextSession } from "@/lib/schedule";
import type { ClassOut, StudentHome } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

export default function StudentHomePage() {
  const { user } = useAuth();
  const { data, error, reload } = useLoad<StudentHome>("/student/home");
  const [code, setCode] = useState("");
  const [joinErr, setJoinErr] = useState<string | null>(null);
  const [joined, setJoined] = useState<string | null>(null);

  async function join(e: React.FormEvent) {
    e.preventDefault();
    setJoinErr(null);
    setJoined(null);
    try {
      const c = await api<ClassOut>("/student/join", { json: { class_code: code } });
      setJoined(c.name);
      setCode("");
      reload();
    } catch (err) {
      setJoinErr((err as Error).message);
    }
  }

  const firstName = user?.name.trim().split(/\s+/).slice(-1)[0] ?? "";
  const todo = data?.upcoming.filter((a) => a.my_status === "missing" && new Date(a.due_at).getTime() > Date.now()) ?? [];
  const next = [...todo].sort((a, b) => a.due_at.localeCompare(b.due_at))[0];

  return (
    <>
      <section className="relative overflow-hidden rounded-2xl border border-line bg-surface px-6 py-7 shadow-card sm:px-8">
        <div className="chalkboard pointer-events-none absolute inset-0" />
        <div className="relative flex flex-wrap items-end gap-5">
          <div className="min-w-0 flex-1">
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-accent">Trang chủ</p>
            <h1 className="text-[1.9rem] font-semibold leading-tight">Chào {firstName}</h1>
            <p className="mt-2 max-w-[560px] text-sm text-muted">
              {!data
                ? "Đang xem hôm nay em có gì…"
                : todo.length === 0
                  ? "Em không còn bài nào cần làm. Mở bài giảng ôn lại, hoặc hỏi gia sư khi bí nhé."
                  : `Em còn ${todo.length} bài cần làm. Bài gần nhất: ${next.title}.`}
            </p>
          </div>
          {next && (
            <Link
              href={`/student/assignments/${next.id}`}
              className="group flex items-center gap-3 rounded-xl border border-line-strong bg-sunken px-4 py-3 transition hover:border-accent"
            >
              <div>
                <div className="text-xs text-faint">Làm tiếp</div>
                <div className="max-w-[240px] truncate text-sm font-semibold">{next.title}</div>
              </div>
              <DueChip due={next.due_at} />
              <ArrowRight size={16} className="text-faint transition group-hover:translate-x-0.5 group-hover:text-accent" />
            </Link>
          )}
        </div>
      </section>
      <ErrorText error={error} />
      {data && data.announcements.length > 0 && (
        <Card>
          <CardHeader title="Thông báo từ giáo viên" />
          <AnnouncementList items={data.announcements} showClass />
        </Card>
      )}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <Card className="p-3 sm:p-4">
          <div className="px-2 pb-2 pt-1">
            <CardHeader title="Bài tập">
              <LinkButton href="/student/schedule" variant="ghost" size="sm">
                <CalendarClock size={15} /> Lịch học
              </LinkButton>
            </CardHeader>
          </div>
          {!data ? (
            <Loading />
          ) : data.upcoming.length === 0 ? (
            <Empty>Không có bài tập nào cần làm.</Empty>
          ) : (
            <ul className="flex flex-col">
              {data.upcoming.map((a) => (
                <li key={a.id}>
                  <Link
                    href={`/student/assignments/${a.id}`}
                    className="group flex items-center gap-3.5 rounded-xl px-3 py-3 transition hover:bg-sunken"
                  >
                    <span className="grid size-9 flex-none place-items-center rounded-lg border border-line bg-sunken text-faint transition group-hover:border-accent/40 group-hover:text-accent">
                      <ClipboardList size={16} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <b className="block truncate text-[0.92rem] font-semibold">{a.title}</b>
                      <span className="block truncate text-xs text-faint">
                        {a.class_name} · hạn {fmtDate(a.due_at)}
                      </span>
                    </div>
                    <div className="flex-none">
                      {a.my_status === "missing" ? <DueChip due={a.due_at} /> : <MyStatusPill status={a.my_status} />}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card className="self-start">
          <CardHeader title="Tham gia lớp mới" />
          <p className="mb-3 text-sm text-muted">Nhập mã lớp giáo viên gửi cho em.</p>
          <form onSubmit={join} className="flex gap-2">
            <Input
              aria-label="Mã lớp"
              placeholder="VD: TOAN10-7KQ"
              className="font-mono uppercase tracking-wider"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            <Button variant="primary">Vào lớp</Button>
          </form>
          <div className="mt-3">
            <ErrorText error={joinErr} />
            {joined && <Banner tone="ok">Đã vào lớp {joined}.</Banner>}
          </div>
        </Card>
      </div>
      <section className="flex flex-col gap-3">
        <h2 className="text-[0.98rem] font-semibold">Lớp của em</h2>
        {data && data.classes.length === 0 && <Empty>Em chưa ở lớp nào. Nhập mã lớp ở trên, hoặc chờ giáo viên thêm em vào lớp.</Empty>}
        <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(260px,1fr))]">
          {data?.classes.map((c) => (
            <Link key={c.id} href={`/student/classes/${c.id}`} className="group">
              <Card className="flex h-full flex-col transition group-hover:-translate-y-0.5 group-hover:border-line-strong">
                <div className="flex items-center justify-between">
                  <Pill>{c.subject}</Pill>
                  <ArrowRight size={16} className="text-faint transition group-hover:translate-x-0.5 group-hover:text-accent" />
                </div>
                <h3 className="mt-3 text-[1.02rem] font-semibold leading-snug">{c.name}</h3>
                <p className="mt-1 text-sm text-muted">{c.teacher_name}</p>
                {c.schedule_text && (
                  <p className="mt-auto flex items-start gap-1.5 border-t border-line pt-3 text-sm">
                    <CalendarClock size={15} className="mt-0.5 flex-none text-faint" />
                    <span>
                      {c.next_session_at && <b className="block font-semibold text-accent">Buổi tới: {fmtNextSession(c.next_session_at)}</b>}
                      <span className="text-muted">{c.schedule_text}</span>
                    </span>
                  </p>
                )}
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}
