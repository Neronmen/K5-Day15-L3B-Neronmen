import { clsx, type ClassValue } from "clsx";
import Link from "next/link";
import { twMerge } from "tailwind-merge";

export function cn(...c: ClassValue[]) {
  return twMerge(clsx(c));
}

type BtnVariant = "primary" | "default" | "ok" | "ghost";
const btnBase =
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-[9px] border px-3.5 py-2 font-medium transition disabled:cursor-not-allowed disabled:opacity-50";
const btnVariants: Record<BtnVariant, string> = {
  primary: "border-accent bg-accent text-accent-ink hover:brightness-110",
  default: "border-line bg-surface text-ink hover:bg-sunken",
  ok: "border-ok bg-ok text-surface hover:brightness-110",
  ghost: "border-transparent bg-transparent text-muted hover:bg-sunken hover:text-ink",
};

export function Button({
  variant = "default",
  size,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant; size?: "sm" }) {
  return (
    <button
      className={cn(btnBase, btnVariants[variant], size === "sm" && "px-2.5 py-1 text-sm", className)}
      {...props}
    />
  );
}

export function LinkButton({
  variant = "default",
  size,
  className,
  ...props
}: React.ComponentProps<typeof Link> & { variant?: BtnVariant; size?: "sm" }) {
  return (
    <Link
      className={cn(btnBase, btnVariants[variant], size === "sm" && "px-2.5 py-1 text-sm", className)}
      {...props}
    />
  );
}

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("min-w-0 rounded-xl border border-line bg-surface p-[18px]", className)} {...props} />;
}

export function CardHeader({ title, children }: { title: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="mb-3 flex flex-wrap items-center gap-2.5">
      <h2 className="mr-auto text-base font-semibold">{title}</h2>
      {children}
    </div>
  );
}

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
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold before:size-1.5 before:rounded-full before:bg-current",
        tones[tone],
      )}
    >
      {children}
    </span>
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
    <div className="flex flex-wrap items-end gap-4">
      <div className="min-w-0 flex-1">
        {eyebrow && <div className="mb-1 text-xs uppercase tracking-[0.08em] text-muted">{eyebrow}</div>}
        <h1 className="text-2xl font-semibold leading-tight [overflow-wrap:anywhere]">{title}</h1>
      </div>
      {children}
    </div>
  );
}

const inputCls = "w-full rounded-[9px] border border-line bg-surface px-3 py-2 text-ink placeholder:text-muted/70";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn(inputCls, props.className)} />;
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn(inputCls, "min-h-24 resize-y", props.className)} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn(inputCls, props.className)} />;
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

export function Banner({ tone = "info", children }: { tone?: "info" | "warn" | "ok" | "bad"; children: React.ReactNode }) {
  const cls = { info: "bg-accent-soft", warn: "bg-warn-soft", ok: "bg-ok-soft", bad: "bg-bad-soft" }[tone];
  return <div className={cn("rounded-[10px] px-3.5 py-3 text-sm", cls)}>{children}</div>;
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
  return <div className="rounded-[10px] border border-dashed border-line px-4 py-8 text-center text-sm text-muted">{children}</div>;
}

export function Avatar({ text }: { text: string }) {
  return (
    <span className="grid size-[30px] flex-none place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent">
      {text}
    </span>
  );
}

export function Loading() {
  return <div className="py-10 text-center text-muted">Đang tải…</div>;
}

export function ModeLabel({ mode }: { mode: "strict" | "extended" }) {
  return mode === "strict" ? <Pill tone="info">AI khoá cứng</Pill> : <Pill tone="warn">AI mở rộng có trích nguồn</Pill>;
}
