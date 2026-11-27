"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CalendarClock, Plus } from "lucide-react";

import { Card, Empty, ErrorText, LinkButton, Loading, ModeLabel, PageHeader, Pill, Select } from "@/components/ui";
import { fmtNextSession } from "@/lib/schedule";
import type { ClassSummary } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

type Sort = "next" | "name" | "subject" | "created";
const SORTS: { id: Sort; label: string }[] = [
  { id: "next", label: "Buổi học sắp tới" },
  { id: "name", label: "Tên lớp (A → Z)" },
  { id: "subject", label: "Môn học" },
  { id: "created", label: "Mới tạo trước" },
];
const SORT_KEY = "ms_class_sort";

function sortClasses(list: ClassSummary[], sort: Sort): ClassSummary[] {
  const byName = (a: ClassSummary, b: ClassSummary) => a.name.localeCompare(b.name, "vi", { numeric: true });
  const out = [...list];
  if (sort === "name") return out.sort(byName);
  if (sort === "subject") return out.sort((a, b) => a.subject.localeCompare(b.subject, "vi") || byName(a, b));
  if (sort === "created") return out.reverse(); // API trả theo thứ tự tạo cũ → mới
  // Lớp có buổi học gần nhất lên trước; lớp chưa có lịch xuống cuối
  return out.sort((a, b) => {
    if (a.next_session_at && b.next_session_at) return a.next_session_at.localeCompare(b.next_session_at);
    if (a.next_session_at) return -1;
    if (b.next_session_at) return 1;
    return byName(a, b);
  });
}

export default function TeacherDashboard() {
  const { data, error } = useLoad<ClassSummary[]>("/teacher/dashboard");
  const [sort, setSort] = useState<Sort>("next");

  useEffect(() => {
    try {
      const s = localStorage.getItem(SORT_KEY) as Sort | null;
      if (s && SORTS.some((x) => x.id === s)) setSort(s);
    } catch {
      /* không có storage: giữ mặc định */
    }
  }, []);

  function changeSort(s: Sort) {
    setSort(s);
    try {
      localStorage.setItem(SORT_KEY, s);
    } catch {
      /* bỏ qua */
    }
  }

  const sorted = useMemo(() => (data ? sortClasses(data, sort) : null), [data, sort]);

  return (
    <>
      <PageHeader eyebrow="Tổng quan" title="Các lớp đang dạy">
        <div className="flex flex-wrap items-center gap-2">
          {data && data.length > 1 && (
            <label className="flex items-center gap-2 text-sm text-muted">
              Xếp theo
              <Select aria-label="Xếp lớp theo" value={sort} onChange={(e) => changeSort(e.target.value as Sort)} className="w-auto py-1.5">
                {SORTS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </Select>
            </label>
          )}
          <LinkButton href="/teacher/classes/new" variant="primary">
            <Plus size={16} /> Tạo lớp mới
          </LinkButton>
        </div>
      </PageHeader>
      <ErrorText error={error} />
      {!data && !error && <Loading />}
      {data && data.length === 0 && (
        <Empty>
          Cô/thầy chưa có lớp nào. Bấm <b>Tạo lớp mới</b>, sau đó gửi mã lớp cho học sinh hoặc thêm học sinh bằng email.
        </Empty>
      )}
      {sorted && sorted.length > 0 && (
        <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(260px,1fr))]">
          {sorted.map((c) => {
            const next = fmtNextSession(c.next_session_at);
            return (
              <Link key={c.id} href={`/teacher/classes/${c.id}`} className="group">
                <Card className="flex h-full flex-col gap-4 transition group-hover:-translate-y-0.5 group-hover:border-line-strong">
                  <div className="flex flex-wrap items-center gap-2">
                    <Pill>{c.subject}</Pill>
                    <ModeLabel mode={c.ai_mode} />
                  </div>
                  <h2 className="text-[1.08rem] font-semibold leading-snug">{c.name}</h2>
                  <div className="flex items-start gap-2 text-sm">
                    <CalendarClock size={16} className="mt-0.5 flex-none text-faint" />
                    {c.schedule_text ? (
                      <span>
                        {next && <b className="block text-accent">Buổi tới: {next}</b>}
                        <span className="text-muted">{c.schedule_text}</span>
                      </span>
                    ) : (
                      <span className="text-muted">Chưa xếp lịch học</span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 divide-x divide-line rounded-xl border border-line bg-sunken">
                    <Stat n={c.students} label="học sinh" />
                    <Stat n={c.documents} label="tài liệu" />
                    <Stat n={c.open_assignments} label="bài đang mở" />
                  </div>
                  <div className="mt-auto flex flex-wrap items-center gap-3 text-sm text-muted">
                    <span>
                      Mã lớp <span className="rounded-md border border-line-strong px-2 py-0.5 font-mono tracking-wider text-ink">{c.class_code}</span>
                    </span>
                    {c.pending_grades > 0 && <Pill tone="warn">{c.pending_grades} bài chờ chấm</Pill>}
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </>
  );
}

function Stat({ n, label }: { n: number; label: string }) {
  return (
    <div className="px-3 py-2.5">
      <b className="block font-display text-[1.4rem] font-semibold leading-tight tabular-nums">{n}</b>
      <span className="text-[0.72rem] text-faint">{label}</span>
    </div>
  );
}
