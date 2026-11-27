"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpen, CalendarDays, LayoutGrid, LogOut, Sparkles } from "lucide-react";

import { initials } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import { NotificationBell } from "./NotificationBell";
import { Avatar, cn } from "./ui";

const NAV = {
  teacher: [
    { href: "/teacher", label: "Các lớp đang dạy", icon: LayoutGrid },
    { href: "/teacher/schedule", label: "Lịch dạy", icon: CalendarDays },
    { href: "/teacher/assistant", label: "Trợ lý AI", icon: Sparkles },
  ],
  student: [
    { href: "/student", label: "Trang chủ", icon: BookOpen },
    { href: "/student/schedule", label: "Lịch học", icon: CalendarDays },
  ],
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  if (!user) return null;
  const nav = NAV[user.role];

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-line bg-surface">
        <div className="flex items-center gap-2 px-4 py-2.5 sm:gap-4">
          <Link href={nav[0].href} className="mr-auto flex items-center gap-2.5 font-display text-lg font-bold">
            <span className="grid size-[30px] place-items-center rounded-lg bg-accent font-mono text-xs text-accent-ink">MS</span>
            MinutesStudy
          </Link>
          <span className="hidden text-xs uppercase tracking-[0.08em] text-muted sm:inline">
            {user.role === "teacher" ? "Giáo viên" : "Học sinh"}
          </span>
          <NotificationBell />
          <div className="flex items-center gap-2 text-sm">
            <Avatar text={initials(user.name)} />
            <span className="hidden sm:inline">{user.name}</span>
          </div>
          <button
            onClick={() => {
              logout();
              router.replace("/login");
            }}
            aria-label="Đăng xuất"
            title="Đăng xuất"
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-muted hover:bg-sunken hover:text-ink"
          >
            <LogOut size={16} /> <span className="hidden sm:inline">Đăng xuất</span>
          </button>
        </div>
      </header>
      <div className="grid flex-1 grid-rows-[auto_minmax(0,1fr)] md:grid-cols-[220px_minmax(0,1fr)] md:grid-rows-1">
        <nav className="flex gap-1 overflow-x-auto border-b border-line bg-surface px-4 py-2 md:flex-col md:border-b-0 md:border-r md:px-2.5 md:py-4">
          {nav.map(({ href, label, icon: Icon }) => {
            // Mục dài nhất khớp đường dẫn mới sáng (để /teacher/schedule không làm sáng cả /teacher)
            const best = nav.filter((n) => pathname === n.href || pathname.startsWith(n.href + "/")).sort((a, b) => b.href.length - a.href.length)[0];
            const active = best?.href === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex flex-none items-center gap-2.5 whitespace-nowrap rounded-lg px-2.5 py-2 text-[0.92rem] font-medium hover:bg-sunken",
                  active && "bg-accent-soft text-accent hover:bg-accent-soft",
                )}
              >
                <Icon size={18} />
                {label}
              </Link>
            );
          })}
        </nav>
        <main className="min-w-0 px-4 pb-12 pt-6">
          <div className="mx-auto flex max-w-[1180px] flex-col gap-5">{children}</div>
        </main>
      </div>
    </div>
  );
}
