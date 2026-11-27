"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FileText, MapPin, MessageCircle } from "lucide-react";

import { AnnouncementList } from "@/components/AnnouncementList";

import { MyStatusPill } from "@/components/StatusPill";
import { Card, CardHeader, Empty, ErrorText, Loading, ModeLabel, PageHeader } from "@/components/ui";
import { fmtDate } from "@/lib/format";
import { WEEKDAYS } from "@/lib/schedule";
import type { StudentClassView } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

export default function StudentClassPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error } = useLoad<StudentClassView>(`/student/classes/${id}`);

  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;

  return (
    <>
      <PageHeader eyebrow={data.cls.subject} title={data.cls.name}>
        <ModeLabel mode={data.cls.ai_mode} />
      </PageHeader>
      <div className="grid items-start gap-4 md:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader title="Thông báo" />
          <AnnouncementList items={data.announcements} empty="Giáo viên chưa đăng thông báo nào." />
        </Card>
        <Card>
          <CardHeader title="Lịch học hằng tuần" />
          {data.sessions.length === 0 ? (
            <Empty>Lớp chưa có lịch học cố định.</Empty>
          ) : (
            data.sessions.map((s) => (
              <div key={s.id} className="flex flex-wrap items-center gap-x-3 gap-y-0.5 border-b border-line py-2.5 text-sm last:border-0">
                <b className="w-[72px]">{WEEKDAYS[s.weekday]}</b>
                <span className="font-mono tabular-nums">
                  {s.start_time}–{s.end_time}
                </span>
                {s.room && (
                  <span className="flex min-w-0 items-center gap-1 break-all text-muted">
                    <MapPin size={12} className="flex-none" /> {s.room}
                  </span>
                )}
              </div>
            ))
          )}
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader title="Bài tập" />
          {data.assignments.length === 0 ? (
            <Empty>Lớp chưa có bài tập.</Empty>
          ) : (
            data.assignments.map((a) => (
              <Link key={a.id} href={`/student/assignments/${a.id}`} className="flex items-center gap-3 rounded-[10px] p-3 hover:bg-sunken">
                <div className="min-w-0 flex-1">
                  <b className="block truncate">{a.title}</b>
                  <span className="text-xs text-muted">Hạn {fmtDate(a.due_at)}</span>
                </div>
                <MyStatusPill status={a.my_status} />
              </Link>
            ))
          )}
        </Card>
        <Card>
          <CardHeader title="Bài giảng" />
          {data.documents.length === 0 ? (
            <Empty>Chưa có bài giảng sẵn sàng. Tài liệu hiện ra ở đây sau khi hệ thống xử lý xong.</Empty>
          ) : (
            data.documents.map((d) => (
              <Link
                key={d.id}
                href={`/student/documents/${d.id}`}
                className="flex w-full items-center gap-3 rounded-[10px] p-3 text-left hover:bg-sunken"
              >
                <FileText className="flex-none text-muted" />
                <span className="min-w-0 flex-1">
                  <b className="block break-words">{d.file_name}</b>
                  {d.page_count && <span className="text-xs text-muted">{d.page_count} trang</span>}
                </span>
                <span className="inline-flex items-center gap-1 text-sm text-accent">
                  <MessageCircle size={15} /> Đọc & hỏi AI
                </span>
              </Link>
            ))
          )}
        </Card>
      </div>
    </>
  );
}
