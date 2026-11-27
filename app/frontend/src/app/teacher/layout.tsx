"use client";

import { AppShell } from "@/components/AppShell";
import { RequireRole } from "@/lib/auth";

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireRole role="teacher">
      <AppShell>{children}</AppShell>
    </RequireRole>
  );
}
