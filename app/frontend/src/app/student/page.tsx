"use client";

import Link from "next/link";
import { useState } from "react";
import { CalendarClock, ClipboardList } from "lucide-react";

import { AnnouncementList } from "@/components/AnnouncementList";

import { MyStatusPill } from "@/components/StatusPill";
import { Banner, Button, Card, CardHeader, Empty, ErrorText, Input, LinkButton, Loading, PageHeader, Pill } from "@/components/ui";
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

  return (
    <>
      <PageHeader eyebrow={`Chào ${firstName}`} title="Trang chủ">
        <LinkButton href="/student/schedule">
          <CalendarClock size={16} /> Xem lịch học
        </LinkButton>
      </PageHeader>
      <ErrorText error={error} />
      {data && data.announcements.length > 0 && (
        <Card>
          <CardHeader title="Thông báo từ giáo viên" />
          <AnnouncementList items={data.announcements} showClass />
        </Card>
      )}
      <div className="grid gap-4 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader title="Bài tập sắp đến hạn" />
          {!data ? (
            <Loading />
          ) : data.upcoming.length === 0 ? (
            <Empty>Không có bài tập nào cần làm.</Empty>
          ) : (
            data.upcoming.map((a) => (
              <Link key={a.id} href={`/student/assignments/${a.id}`} className="flex items-center gap-3 rounded-[10px] p-3 hover:bg-sunken">
                <span className="grid size-[30px] flex-none place-items-center rounded-full bg-accent-soft text-accent">
                  <ClipboardList size={16} />
                </span>
                <div className="min-w-0 flex-1">
                  <b className="block truncate">{a.title}</b>
                  <span className="text-xs text-muted">
                    {a.class_name} · hạn {fmtDate(a.due_at)}
                  </span>
                </div>
                <MyStatusPill status={a.my_status} />
              </Link>
            ))
          )}
        </Card>
        <Card className="self-start">
          <CardHeader title="Tham gia lớp mới" />
          <p className="mb-2.5 text-sm text-muted">Nhập mã lớp giáo viên gửi.</p>
          <form onSubmit={join} className="flex gap-2">
            <Input
              aria-label="Mã lớp"
              placeholder="VD: TOAN11-7KQ"
              className="font-mono uppercase"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            <Button variant="primary">Vào lớp</Button>
          </form>
          <div className="mt-2.5">
            <ErrorText error={joinErr} />
            {joined && <Banner tone="ok">Đã vào lớp {joined}.</Banner>}
          </div>
        </Card>
      </div>
      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Lớp của em</h2>
        {data && data.classes.length === 0 && <Empty>Em chưa ở lớp nào. Nhập mã lớp ở trên, hoặc chờ giáo viên thêm em vào lớp.</Empty>}
        <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(240px,1fr))]">
          {data?.classes.map((c) => (
            <Link key={c.id} href={`/student/classes/${c.id}`} className="group">
              <Card className="h-full transition group-hover:border-accent">
                <Pill>{c.subject}</Pill>
                <h3 className="mt-2 text-base font-semibold">{c.name}</h3>
                <p className="mt-1 text-sm text-muted">{c.teacher_name}</p>
                {c.schedule_text && (
                  <p className="mt-2 flex items-start gap-1.5 text-sm">
                    <CalendarClock size={15} className="mt-0.5 flex-none text-muted" />
                    <span>
                      {c.next_session_at && <b className="block text-accent">Buổi tới: {fmtNextSession(c.next_session_at)}</b>}
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
