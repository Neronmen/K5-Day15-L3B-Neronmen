"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";

import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { NotificationItem } from "@/lib/types";

function describe(n: NotificationItem): { text: string; href?: string } {
  const p = n.payload as { file_name?: string; class_id?: string; error?: string };
  if (n.kind === "doc_ready") return { text: `${p.file_name} đã sẵn sàng cho AI`, href: p.class_id && `/teacher/classes/${p.class_id}` };
  if (n.kind === "announcement") {
    const a = n.payload as { class_id?: string; class_name?: string; title?: string; kind?: string };
    const tag = a.kind === "cancel" ? "Nghỉ học" : a.kind === "makeup" ? "Học bù" : "Thông báo";
    return { text: `[${tag}] ${a.class_name}: ${a.title}`, href: a.class_id && `/student/classes/${a.class_id}` };
  }
  if (n.kind === "doc_failed") return { text: `${p.file_name} xử lý lỗi: ${p.error ?? ""}`, href: p.class_id && `/teacher/classes/${p.class_id}` };
  return { text: n.kind };
}

export function NotificationBell() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const unread = items.filter((n) => !n.read).length;

  const load = useCallback(() => {
    api<NotificationItem[]>("/notifications").then(setItems).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  function toggle() {
    setOpen((o) => !o);
    if (!open && unread) {
      api("/notifications/read", { method: "POST" })
        .then(() => setItems((all) => all.map((n) => ({ ...n, read: true }))))
        .catch(() => {});
    }
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={toggle}
        aria-label={unread ? `${unread} thông báo mới` : "Thông báo"}
        className="relative grid size-9 place-items-center rounded-lg text-muted hover:bg-sunken hover:text-ink"
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute right-1 top-1 grid min-w-4 place-items-center rounded-full bg-bad px-1 text-[10px] font-bold text-surface">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-11 z-20 w-[min(340px,calc(100vw-32px))] rounded-xl border border-line bg-surface p-2 shadow-lg">
          {items.length === 0 ? (
            <p className="p-3 text-sm text-muted">Chưa có thông báo.</p>
          ) : (
            items.map((n) => {
              const d = describe(n);
              const body = (
                <>
                  <span className="block text-sm">{d.text}</span>
                  <span className="text-xs text-muted">{fmtDate(n.created_at)}</span>
                </>
              );
              return d.href ? (
                <Link key={n.id} href={d.href} onClick={() => setOpen(false)} className="block rounded-lg p-2.5 hover:bg-sunken">
                  {body}
                </Link>
              ) : (
                <div key={n.id} className="rounded-lg p-2.5">
                  {body}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
