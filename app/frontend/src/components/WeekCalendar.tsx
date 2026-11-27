"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { CalendarX, ChevronLeft, ChevronRight, MapPin } from "lucide-react";

import { addDays, fmtDay, mondayOf, parseYmd, WEEKDAYS, ymd } from "@/lib/schedule";
import type { CalendarItem } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";
import { Button, ErrorText, Loading, cn } from "./ui";

// Màu theo lớp: 6 tông dịu cùng độ sáng (định nghĩa --cal-1..6 trong globals.css, có bản tối / sáng)
const PALETTE = [
  "border-l-[var(--cal-1)]",
  "border-l-[var(--cal-2)]",
  "border-l-[var(--cal-3)]",
  "border-l-[var(--cal-4)]",
  "border-l-[var(--cal-5)]",
  "border-l-[var(--cal-6)]",
];

function colorFor(classId: string, order: string[]) {
  const i = order.indexOf(classId);
  return PALETTE[(i < 0 ? 0 : i) % PALETTE.length];
}

/** Lịch tuần (Thứ 2 → Chủ nhật). role quyết định API và đường dẫn tới lớp. */
export function WeekCalendar({
  role,
  reloadKey = 0,
  onCancel,
}: {
  role: "teacher" | "student";
  reloadKey?: number;
  onCancel?: (item: CalendarItem) => void;
}) {
  const [monday, setMonday] = useState(() => mondayOf(new Date()));
  const start = ymd(monday);
  const { data, error } = useLoad<CalendarItem[]>(`/${role}/calendar?start=${start}&days=7&k=${reloadKey}`);
  const today = ymd(new Date());

  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => ymd(addDays(monday, i))), [monday]);
  const classOrder = useMemo(() => Array.from(new Set((data ?? []).map((x) => x.class_id))).sort(), [data]);
  const byDay = useMemo(() => {
    const m: Record<string, CalendarItem[]> = {};
    for (const it of data ?? []) (m[it.date] ??= []).push(it);
    return m;
  }, [data]);
  const end = addDays(monday, 6);
  const count = (data ?? []).filter((x) => !x.cancelled).length;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" aria-label="Tuần trước" onClick={() => setMonday((m) => addDays(m, -7))}>
          <ChevronLeft size={15} />
        </Button>
        <Button size="sm" onClick={() => setMonday(mondayOf(new Date()))}>
          Tuần này
        </Button>
        <Button size="sm" aria-label="Tuần sau" onClick={() => setMonday((m) => addDays(m, 7))}>
          <ChevronRight size={15} />
        </Button>
        <b className="ml-1">
          {`${monday.getDate()}/${monday.getMonth() + 1}`} – {`${end.getDate()}/${end.getMonth() + 1}/${end.getFullYear()}`}
        </b>
        {data && <span className="text-sm text-muted">· {count} buổi học</span>}
      </div>
      <ErrorText error={error} />
      {!data && !error && <Loading />}
      {data && (
        <div className="grid gap-2 lg:grid-cols-7">
          {days.map((d, i) => {
            const items = byDay[d] ?? [];
            const isToday = d === today;
            return (
              <section
                key={d}
                className={cn(
                  "flex min-w-0 flex-col gap-2 rounded-xl border border-line bg-surface p-2.5 lg:min-h-40",
                  isToday && "border-accent ring-1 ring-accent",
                  items.length === 0 && "max-lg:hidden",
                )}
              >
                <header className="flex items-baseline justify-between gap-1">
                  <span className={cn("text-sm font-semibold", isToday && "text-accent")}>
                    <span className="lg:hidden">{fmtDay(d)}</span>
                    <span className="hidden lg:inline">{WEEKDAYS[i]}</span>
                  </span>
                  <span className="hidden text-xs tabular-nums text-muted lg:inline">
                    {parseYmd(d).getDate()}/{parseYmd(d).getMonth() + 1}
                  </span>
                  {isToday && <span className="text-xs font-semibold text-accent lg:hidden">Hôm nay</span>}
                </header>
                {items.map((it) => (
                  <div
                    key={`${it.class_id}-${it.start_time}-${it.kind}`}
                    className={cn(
                      "rounded-lg border border-l-4 border-line bg-sunken/60 px-2.5 py-2 text-sm",
                      colorFor(it.class_id, classOrder),
                      it.cancelled && "border-l-bad bg-bad-soft/60",
                    )}
                  >
                    <div className={cn("font-mono text-xs tabular-nums", it.cancelled && "line-through")}>
                      {it.start_time}–{it.end_time}
                    </div>
                    <Link
                      href={`/${role}/classes/${it.class_id}`}
                      className={cn("block break-words font-semibold hover:text-accent", it.cancelled && "text-muted line-through")}
                    >
                      {it.class_name}
                    </Link>
                    {it.room && (
                      <div className="mt-0.5 flex items-center gap-1 text-xs text-muted" title={it.room}>
                        <MapPin size={11} className="flex-none" /> <span className="min-w-0 truncate">{it.room}</span>
                      </div>
                    )}
                    {it.cancelled && (
                      <div className="mt-1 break-words text-xs font-semibold text-bad">
                        {it.note?.toLowerCase().startsWith("nghỉ") ? it.note : `Nghỉ · ${it.note}`}
                      </div>
                    )}
                    {it.kind === "makeup" && (
                      <div className="mt-1 break-words text-xs font-semibold text-ok">
                        {it.note?.toLowerCase().startsWith("học bù") ? it.note : `Học bù · ${it.note}`}
                      </div>
                    )}
                    {onCancel && it.kind === "regular" && !it.cancelled && d >= today && (
                      <button
                        onClick={() => onCancel(it)}
                        className="mt-1.5 inline-flex items-center gap-1 text-xs font-medium text-muted hover:text-bad"
                      >
                        <CalendarX size={12} /> Báo nghỉ
                      </button>
                    )}
                  </div>
                ))}
              </section>
            );
          })}
          {count === 0 && data.length === 0 && (
            <p className="rounded-xl border border-dashed border-line p-4 text-center text-sm text-muted lg:col-span-7">
              Tuần này không có buổi học nào.
              {role === "teacher" && " Thêm lịch học cố định trong tab Lịch học của từng lớp."}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
