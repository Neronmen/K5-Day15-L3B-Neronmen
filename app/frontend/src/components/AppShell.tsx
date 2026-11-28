"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpen, CalendarDays, LayoutGrid, LogOut, Sparkles } from "lucide-react";

import { initials } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import { NotificationBell } from "./NotificationBell";
import { Avatar, cn, Logo, ThemeToggle, Wordmark } from "./ui";

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
  const roleLabel = user.role === "teacher" ? "Giáo viên" : "Học sinh";
  // Mục dài nhất khớp đường dẫn mới sáng (để /teacher/schedule không làm sáng cả /teacher)
  const active = nav
    .filter((n) => pathname === n.href || pathname.startsWith(n.href + "/"))
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;
  const signOut = () => {
    logout();
    router.replace("/login");
  };

  const links = nav.map(({ href, label, icon: Icon }) => (
    <Link
      key={href}
      href={href}
      aria-current={active === href ? "page" : undefined}
      className={cn(
        "group relative flex flex-none items-center gap-3 whitespace-nowrap rounded-lg px-3 py-2 text-[0.9rem] font-medium text-muted transition hover:bg-sunken hover:text-ink",
        active === href && "bg-sunken text-ink",
      )}
    >
      {/* vạch phấn đánh dấu mục đang mở */}
      <span
        className={cn(
          "absolute left-0 top-1/2 hidden h-5 w-[3px] -translate-y-1/2 rounded-r bg-accent lg:block",
          active === href ? "opacity-100" : "opacity-0",
        )}
      />
      <Icon size={18} className={cn("transition", active === href ? "text-accent" : "text-faint group-hover:text-muted")} />
      {label}
    </Link>
  ));

  return (
    <div className="min-h-screen lg:grid lg:h-screen lg:grid-cols-[248px_minmax(0,1fr)] lg:overflow-hidden">
      {/* Thanh bên — máy tính */}
      <aside className="sticky top-0 hidden h-screen flex-col border-r border-line bg-surface lg:flex">
        <Link href={nav[0].href} className="flex items-center gap-2.5 px-5 pb-5 pt-6 text-[1.05rem]">
          <Logo size={30} />
          <Wordmark />
        </Link>
        <div className="px-5 pb-2 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-faint">{roleLabel}</div>
        <nav className="flex flex-col gap-0.5 px-3">{links}</nav>
        <div className="mt-auto border-t border-line p-3">
          <div className="flex items-center gap-2.5 rounded-xl px-2 py-2">
            <Avatar text={initials(user.name)} />
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold">{user.name}</div>
              <div className="truncate text-xs text-faint">{user.email}</div>
            </div>
          </div>
          <div className="mt-1 flex items-center gap-1">
            <ThemeToggle withLabel className="flex-1" />
            <button
              onClick={signOut}
              aria-label="Đăng xuất"
              title="Đăng xuất"
              className="inline-flex items-center rounded-lg p-2 text-muted transition hover:bg-bad-soft hover:text-bad"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Máy tính: khung phải cao đúng 1 màn hình; chỉ vùng nội dung tự cuộn khi trang dài (trang vừa màn hình thì không cuộn) */}
      <div className="flex min-w-0 flex-col lg:h-screen lg:min-h-0">
        {/* Thanh trên — điện thoại; trên máy tính chỉ còn chuông thông báo */}
        <header className="sticky top-0 z-20 border-b border-line bg-bg/85 backdrop-blur lg:border-b-0 lg:bg-transparent lg:backdrop-blur-none">
          <div className="flex items-center gap-2 px-4 py-2.5 lg:justify-end lg:px-8 lg:py-2">
            <Link href={nav[0].href} className="mr-auto flex items-center gap-2 lg:hidden">
              <Logo size={28} />
              <Wordmark />
            </Link>
            <NotificationBell />
            <ThemeToggle className="lg:hidden" />
            <button
              onClick={signOut}
              aria-label="Đăng xuất"
              className="inline-flex items-center rounded-lg p-2 text-muted hover:bg-sunken hover:text-ink lg:hidden"
            >
              <LogOut size={16} />
            </button>
          </div>
          <nav className="no-scrollbar flex gap-1 overflow-x-auto px-3 pb-2 lg:hidden">{links}</nav>
        </header>
        <main className="min-w-0 px-4 pb-16 pt-4 lg:min-h-0 lg:flex-1 lg:overflow-y-auto lg:px-8 lg:pb-6 lg:pt-0">
          <div className="mx-auto flex max-w-[1180px] flex-col gap-6 lg:h-full">{children}</div>
        </main>
      </div>
    </div>
  );
}
