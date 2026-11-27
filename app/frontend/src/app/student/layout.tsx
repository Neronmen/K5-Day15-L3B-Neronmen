"use client";

import { AppShell } from "@/components/AppShell";
import { RequireRole } from "@/lib/auth";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireRole role="student">
      <AppShell>{children}</AppShell>
    </RequireRole>
  );
}
