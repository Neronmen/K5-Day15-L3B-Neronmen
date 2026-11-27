"use client";

import { CalendarPlus, CalendarX, Megaphone, Pin, PinOff, Trash2 } from "lucide-react";

import { fmtDate } from "@/lib/format";
import { fmtDay } from "@/lib/schedule";
import type { Announcement } from "@/lib/types";
import { Button, Empty, Pill, cn } from "./ui";

const KIND = {
  general: { label: "Thông báo", tone: "info" as const, icon: Megaphone },
  cancel: { label: "Nghỉ học", tone: "bad" as const, icon: CalendarX },
  makeup: { label: "Học bù", tone: "ok" as const, icon: CalendarPlus },
};

function eventLine(a: Announcement): string | null {
  if (!a.event_date) return null;
  const day = fmtDay(a.event_date);
  if (a.kind === "makeup") {
    const time = `${a.event_start}–${a.event_end}`;
    return a.title.includes(day) && a.title.includes(time) ? null : `Học bù ${day}, ${time}`;
  }
  if (a.title.includes(day)) return a.session_id ? null : "Nghỉ cả ngày";
  return `Nghỉ ${day}${a.session_id ? "" : " (cả ngày)"}`;
}

/** Danh sách thông báo lớp. Truyền onPin/onDelete để hiện nút quản lý cho giáo viên. */
export function AnnouncementList({
  items,
  showClass,
  empty = "Chưa có thông báo nào.",
  onPin,
  onDelete,
}: {
  items: Announcement[];
  showClass?: boolean;
  empty?: string;
  onPin?: (a: Announcement) => void;
  onDelete?: (a: Announcement) => void;
}) {
  if (items.length === 0) return <Empty>{empty}</Empty>;
  return (
    <div className="flex flex-col gap-2.5">
      {items.map((a) => {
        const k = KIND[a.kind] ?? KIND.general;
        const Icon = k.icon;
        const ev = eventLine(a);
        return (
          <article
            key={a.id}
            className={cn(
              "flex gap-3 rounded-xl border border-line p-3.5",
              a.kind === "cancel" && "border-bad/40 bg-bad-soft/40",
              a.pinned && "border-accent/50",
            )}
          >
            <span
              className={cn(
                "grid size-[34px] flex-none place-items-center rounded-full",
                a.kind === "cancel" ? "bg-bad-soft text-bad" : a.kind === "makeup" ? "bg-ok-soft text-ok" : "bg-accent-soft text-accent",
              )}
            >
              <Icon size={17} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <Pill tone={k.tone}>{k.label}</Pill>
                {a.pinned && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-accent">
                    <Pin size={12} /> Đã ghim
                  </span>
                )}
                {showClass && <span className="text-xs text-muted">{a.class_name}</span>}
              </div>
              <h3 className="mt-1 break-words font-semibold">{a.title}</h3>
              {ev && <p className="mt-0.5 text-sm font-medium">{ev}</p>}
              {a.body && <p className="mt-1 whitespace-pre-wrap break-words text-sm text-muted">{a.body}</p>}
              <p className="mt-1.5 text-xs text-muted">Đăng {fmtDate(a.created_at)}</p>
            </div>
            {(onPin || onDelete) && (
              <div className="flex flex-none flex-col gap-1">
                {onPin && (
                  <Button variant="ghost" size="sm" title={a.pinned ? "Bỏ ghim" : "Ghim lên đầu"} onClick={() => onPin(a)}>
                    {a.pinned ? <PinOff size={14} /> : <Pin size={14} />}
                  </Button>
                )}
                {onDelete && (
                  <Button variant="ghost" size="sm" title="Xoá thông báo" onClick={() => onDelete(a)}>
                    <Trash2 size={14} />
                  </Button>
                )}
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}
