"use client";

import { WeekCalendar } from "@/components/WeekCalendar";
import { PageHeader } from "@/components/ui";

export default function StudentSchedulePage() {
  return (
    <>
      <PageHeader eyebrow="Thời khoá biểu" title="Lịch học" />
      <WeekCalendar role="student" />
    </>
  );
}
