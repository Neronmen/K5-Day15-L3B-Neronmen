"use client";

import { clsx, type ClassValue } from "clsx";
import { Moon, Sun } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { twMerge } from "tailwind-merge";

import { useTheme } from "@/lib/theme";

export function cn(...c: ClassValue[]) {
  return twMerge(clsx(c));
}

/* ---------- Thương hiệu ---------- */

/** Logo: mặt đồng hồ phấn với kim phút — "Minutes" — trên ô vuông vàng phấn. */
export function Logo({ size = 32, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden className={cn("flex-none", className)}>
      <rect width="32" height="32" rx="9" fill="var(--accent)" />
      <circle cx="16" cy="16" r="9.5" fill="none" stroke="var(--accent-ink)" strokeWidth="2.2" />
      <path d="M16 16V9.6" stroke="var(--accent-ink)" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M16 16l4.2 2.6" stroke="var(--accent-ink)" strokeWidth="2.4" strokeLinecap="round" />
      <circle cx="16" cy="16" r="1.6" fill="var(--accent-ink)" />
    </svg>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-display font-semibold tracking-tight", className)}>
      Minutes<span className="text-accent">Study</span>
    </span>
  );
}

export function ThemeToggle({ className, withLabel }: { className?: string; withLabel?: boolean }) {
  const [theme, toggle] = useTheme();
  const dark = theme === "dark";
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối"}
      title={dark ? "Giao diện sáng" : "Giao diện tối"}
      className={cn(
        "inline-flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-muted transition hover:bg-sunken hover:text-ink",
        className,
      )}
    >
      {dark ? <Sun size={16} /> : <Moon size={16} />}
      {withLabel && <span>{dark ? "Giao diện sáng" : "Giao diện tối"}</span>}
    </button>
  );
}

/* ---------- Nút ---------- */

type BtnVariant = "primary" | "default" | "ok" | "ghost";
const btnBase =
  "inline-flex h-9 items-center justify-center gap-1.5 whitespace-nowrap rounded-lg border px-3.5 text-sm font-semibold transition duration-150 active:translate-y-px disabled:pointer-events-none disabled:opacity-45";
const btnVariants: Record<BtnVariant, string> = {
  primary: "border-transparent bg-accent text-accent-ink hover:shadow-glow hover:brightness-105",
  default: "border-line-strong bg-surface text-ink hover:border-faint hover:bg-sunken",
  ok: "border-transparent bg-ok text-surface hover:brightness-110",
  ghost: "border-transparent bg-transparent text-muted hover:bg-sunken hover:text-ink",
};
const btnSm = "h-8 px-2.5 text-[0.8rem]";

export function Button({
  variant = "default",
  size,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant; size?: "sm" }) {
  return <button className={cn(btnBase, btnVariants[variant], size === "sm" && btnSm, className)} {...props} />;
}

export function LinkButton({
  variant = "default",
  size,
  className,
  ...props
}: React.ComponentProps<typeof Link> & { variant?: BtnVariant; size?: "sm" }) {
  return <Link className={cn(btnBase, btnVariants[variant], size === "sm" && btnSm, className)} {...props} />;
}

/* ---------- Khung ---------- */

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("min-w-0 animate-rise rounded-2xl border border-line bg-surface p-5 shadow-card", className)}
      {...props}
    />
  );
}

export function CardHeader({ title, children }: { title: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2.5">
      <h2 className="mr-auto text-[0.98rem] font-semibold">{title}</h2>
      {children}
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  children,
}: {
  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end gap-4 pb-1">
      <div className="min-w-0 flex-1">
        {eyebrow && (
          <div className="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-accent">
            <span className="h-px w-5 bg-accent" />
            {eyebrow}
          </div>
        )}
        <h1 className="text-[1.7rem] font-semibold leading-tight [overflow-wrap:anywhere]">{title}</h1>
      </div>
      {children}
    </div>
  );
}

/* ---------- Nhãn ---------- */

type Tone = "ok" | "warn" | "bad" | "info" | "mute";
const tones: Record<Tone, string> = {
  ok: "bg-ok-soft text-ok",
  warn: "bg-warn-soft text-warn",
  bad: "bg-bad-soft text-bad",
  info: "bg-accent-soft text-accent",
  mute: "bg-sunken text-muted",
};

export function Pill({ tone = "mute", children }: { tone?: Tone; children: React.ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-[3px] text-[0.72rem] font-semibold leading-none before:size-1.5 before:rounded-full before:bg-current",
        tones[tone],
      )}
    >
      {children}
    </span>
  );
}

function left(ms: number): string {
  const m = Math.round(ms / 60000);
  if (m < 60) return `${Math.max(m, 1)} phút`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} giờ${m % 60 ? ` ${m % 60} phút` : ""}`;
  const d = Math.floor(h / 24);
  return `${d} ngày${h % 24 ? ` ${h % 24} giờ` : ""}`;
}

/**
 * Đồng hồ hạn nộp — dấu ấn của MinutesStudy: hạn nộp quyết định gia sư chỉ gợi ý hay được giải.
 * Còn > 1 ngày: trung tính · < 24 giờ: vàng phấn · < 1 giờ: vàng phấn nhấp nháy · hết hạn: mờ.
 */
export function DueChip({ due, className }: { due: string; className?: string }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const t = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(t);
  }, []);
  if (now === null) return <span className={cn("inline-block h-5 w-20 rounded-full bg-sunken", className)} />;
  const ms = new Date(due).getTime() - now;
  const base = "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-[3px] text-[0.72rem] font-semibold tabular-nums";
  if (ms <= 0) return <span className={cn(base, "bg-sunken text-faint", className)}>Đã hết hạn</span>;
  const soon = ms < 24 * 3600e3;
  const urgent = ms < 3600e3;
  return (
    <span
      className={cn(base, soon ? "bg-accent-soft text-accent" : "bg-sunken text-muted", className)}
      title={new Date(due).toLocaleString("vi-VN")}
    >
      <span className={cn("size-1.5 rounded-full bg-current", urgent && "animate-tick")} />
      còn {left(ms)}
    </span>
  );
}

/* ---------- Form ---------- */

const inputCls =
  "w-full rounded-lg border border-line-strong bg-field px-3 py-2 text-ink transition placeholder:text-faint hover:border-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn(inputCls, props.className)} />;
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn(inputCls, "min-h-24 resize-y", props.className)} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn(inputCls, "cursor-pointer", props.className)} />;
}

export function Field({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: React.ReactNode;
  htmlFor?: string;
  hint?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={htmlFor} className="text-sm font-semibold">
        {label} {hint && <span className="font-normal text-muted">{hint}</span>}
      </label>
      {children}
    </div>
  );
}

/* ---------- Phản hồi ---------- */

export function Banner({ tone = "info", children }: { tone?: "info" | "warn" | "ok" | "bad"; children: React.ReactNode }) {
  const cls = {
    info: "border-accent/30 bg-accent-soft",
    warn: "border-warn/30 bg-warn-soft",
    ok: "border-ok/30 bg-ok-soft",
    bad: "border-bad/30 bg-bad-soft",
  }[tone];
  return <div className={cn("rounded-xl border px-3.5 py-3 text-sm", cls)}>{children}</div>;
}

export function ErrorText({ error }: { error: string | null | undefined }) {
  if (!error) return null;
  return (
    <p role="alert" className="text-sm text-bad">
      {error}
    </p>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-line-strong px-4 py-9 text-center text-sm text-muted">
      {children}
    </div>
  );
}

export function Avatar({ text }: { text: string }) {
  return (
    <span className="grid size-8 flex-none place-items-center rounded-full border border-line-strong bg-sunken font-display text-[0.7rem] font-semibold text-ink">
      {text}
    </span>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-shimmer rounded-lg bg-sunken", className)} />;
}

export function Loading() {
  return (
    <div className="flex flex-col gap-2.5 py-3" aria-label="Đang tải" role="status">
      <Skeleton className="h-4 w-2/5" />
      <Skeleton className="h-4 w-4/5" />
      <Skeleton className="h-4 w-3/5" />
    </div>
  );
}

export function ModeLabel({ mode }: { mode: "strict" | "extended" }) {
  return mode === "strict" ? <Pill tone="info">AI khoá cứng</Pill> : <Pill tone="warn">AI mở rộng có trích nguồn</Pill>;
}
