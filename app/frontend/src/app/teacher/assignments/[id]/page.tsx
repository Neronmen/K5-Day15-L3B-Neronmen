"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { Check, RefreshCw, Sparkles, Trash2, Upload } from "lucide-react";

import { AttachmentLink } from "@/components/AttachmentLink";

import { AuthImage } from "@/components/AuthImage";
import {
  Avatar, Banner, Button, Card, CardHeader, Empty, ErrorText, Field, Input, Loading, PageHeader, Pill, Textarea, cn,
} from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate, initials, isPast } from "@/lib/format";
import type { Assignment, GradeDetail, RubricItem, Submission, SubmissionRow } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

const AI_RUNNING = new Set(["queued", "running"]);

export default function TeacherAssignmentPage() {
  const { id } = useParams<{ id: string }>();
  const asg = useLoad<Assignment>(`/teacher/assignments/${id}`);
  const rows = useLoad<SubmissionRow[]>(`/teacher/assignments/${id}/submissions`);
  const [selected, setSelected] = useState<string | null>(null);
  const list = rows.data ?? [];
  const anyRunning = list.some((r) => r.ai_status && AI_RUNNING.has(r.ai_status));

  // Cập nhật bảng khi có bài đang được AI chấm (realtime đơn giản bằng polling)
  useEffect(() => {
    const t = setInterval(rows.reload, anyRunning ? 4000 : 20000);
    return () => clearInterval(t);
  }, [anyRunning, rows.reload]);

  if (asg.error) return <ErrorText error={asg.error} />;
  if (!asg.data) return <Loading />;
  const a = asg.data;
  const count = (s: SubmissionRow["status"]) => list.filter((r) => r.status === s).length;
  const sel = list.find((r) => r.submission_id === selected) ?? null;

  return (
    <>
      <PageHeader
        eyebrow={
          <Link href={`/teacher/classes/${a.class_id}`} className="hover:text-accent">
            ← Về lớp
          </Link>
        }
        title={a.title}
      >
        {isPast(a.due_at) ? <Pill>Đã hết hạn</Pill> : <Pill tone="info">Đang mở</Pill>}
      </PageHeader>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader title="Trạng thái nộp bài">
            <span className="text-xs text-muted">Tự cập nhật</span>
          </CardHeader>
          <div className="flex flex-wrap gap-6">
            <Stat n={count("submitted")} label="đã nộp" />
            <Stat n={count("late")} label="nộp muộn" />
            <Stat n={count("missing")} label="chưa nộp" />
            <Stat n={list.filter((r) => r.submission_id && r.grade_status !== "published").length} label="chờ duyệt" />
          </div>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-sunken">
            <i
              className="block h-full bg-accent transition-all"
              style={{ width: list.length ? `${((count("submitted") + count("late")) / list.length) * 100}%` : "0%" }}
            />
          </div>
        </Card>
        <Card>
          <CardHeader title="Thông tin bài" />
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
            <dt className="text-muted">Hạn nộp</dt>
            <dd className="font-semibold">{fmtDate(a.due_at)}</dd>
            <dt className="text-muted">Nộp muộn</dt>
            <dd>{a.allow_late ? "Cho phép" : "Không cho phép"}</dd>
            <dt className="text-muted">Phiên bản đề</dt>
            <dd>v{a.version}</dd>
            <dt className="text-muted">Đáp án mẫu</dt>
            <dd>{a.reference_answer ? "Có · AI gia sư chỉ dùng sau hạn" : "Chưa có"}</dd>
            <dt className="text-muted">File đề</dt>
            <dd className="min-w-0">
              <AttachmentManager a={a} onChange={(x) => asg.setData(x)} />
            </dd>
          </dl>
        </Card>
      </div>

      <details className="rounded-xl border border-line bg-surface p-[18px]">
        <summary className="cursor-pointer font-semibold">Đề bài & rubric</summary>
        <p className="mt-3 whitespace-pre-wrap">{a.prompt}</p>
        {a.rubric && <p className="mt-3 whitespace-pre-wrap text-sm text-muted">{a.rubric}</p>}
      </details>

      <div className={cn("grid items-start gap-4", sel && "xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]")}>
        <Card>
          <CardHeader title="Học sinh" />
          <ErrorText error={rows.error} />
          {list.length === 0 ? (
            <Empty>Lớp chưa có học sinh.</Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider text-muted">
                    <th className="border-b border-line px-2.5 py-2 font-semibold">Học sinh</th>
                    <th className="border-b border-line px-2.5 py-2 font-semibold">Nộp bài</th>
                    <th className="border-b border-line px-2.5 py-2 font-semibold">Điểm</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((r) => (
                    <tr
                      key={r.student_id}
                      onClick={() => r.submission_id && setSelected(r.submission_id)}
                      className={cn(
                        "border-b border-line last:border-0",
                        r.submission_id && "cursor-pointer hover:bg-sunken",
                        selected && r.submission_id === selected && "bg-accent-soft hover:bg-accent-soft",
                      )}
                    >
                      <td className="px-2.5 py-2.5">
                        <div className="flex items-center gap-2.5">
                          <Avatar text={initials(r.name)} />
                          <span className="min-w-0">
                            {r.name}
                            {r.submitted_at && <span className="block text-xs tabular-nums text-muted">{fmtDate(r.submitted_at)}</span>}
                          </span>
                        </div>
                      </td>
                      <td className="px-2.5 py-2.5">
                        {r.status === "submitted" ? <Pill tone="ok">Đã nộp</Pill> : r.status === "late" ? <Pill tone="warn">Nộp muộn</Pill> : <Pill>Chưa nộp</Pill>}
                      </td>
                      <td className="px-2.5 py-2.5 tabular-nums">
                        <ScoreCell r={r} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
        {sel?.submission_id && <GradePanel key={sel.submission_id} row={sel} onChanged={rows.reload} />}
      </div>
    </>
  );
}

function ScoreCell({ r }: { r: SubmissionRow }) {
  if (!r.submission_id) return <span className="text-muted">—</span>;
  if (r.grade_status === "published") return <b>{r.score}</b>;
  if (r.ai_status && AI_RUNNING.has(r.ai_status)) return <Pill tone="info">AI đang chấm</Pill>;
  if (r.ai_status === "done") return <Pill tone="warn">AI: {r.ai_score} · chờ duyệt</Pill>;
  if (r.ai_status === "manual") return <Pill tone="warn">Cần chấm tay</Pill>;
  if (r.ai_status === "failed") return <Pill tone="bad">AI lỗi</Pill>;
  return <Pill tone="warn">Chờ chấm</Pill>;
}

const VERDICT: Record<string, { tone: "ok" | "warn" | "bad" | "mute"; label: string; mark: string }> = {
  correct: { tone: "ok", label: "Đúng", mark: "✓" },
  partial: { tone: "warn", label: "Đúng một phần", mark: "!" },
  wrong: { tone: "bad", label: "Sai", mark: "✕" },
  missing: { tone: "mute", label: "Thiếu", mark: "–" },
};

function GradePanel({ row, onChanged }: { row: SubmissionRow; onChanged: () => void }) {
  const subId = row.submission_id!;
  const [sub, setSub] = useState<Submission | null>(null);
  const [grade, setGrade] = useState<GradeDetail | null>(null);
  const [items, setItems] = useState<RubricItem[]>([]);
  const [score, setScore] = useState("");
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [touched, setTouched] = useState(false);

  const load = useCallback(async () => {
    try {
      const g = await api<GradeDetail>(`/teacher/submissions/${subId}/grade`);
      setGrade(g);
      return g;
    } catch (e) {
      setError((e as Error).message);
      return null;
    }
  }, [subId]);

  useEffect(() => {
    api<Submission>(`/teacher/submissions/${subId}`).then(setSub).catch((e) => setError((e as Error).message));
    load();
  }, [subId, load]);

  // Điền sẵn từ bản nháp AI (hoặc điểm đã công bố) khi chưa sửa tay
  useEffect(() => {
    if (!grade || touched) return;
    if (grade.status === "published") {
      setScore(String(grade.score ?? ""));
      setFeedback(grade.feedback ?? "");
      setItems(grade.breakdown ?? []);
    } else if (grade.ai_breakdown) {
      setItems(grade.ai_breakdown.items ?? []);
      setScore(grade.ai_score != null ? String(grade.ai_score) : "");
      setFeedback(grade.ai_breakdown.feedback ?? "");
    }
  }, [grade, touched]);

  // Đang chấm: hỏi lại mỗi 3 giây
  useEffect(() => {
    if (!grade?.ai_status || !AI_RUNNING.has(grade.ai_status)) return;
    const t = setInterval(async () => {
      const g = await load();
      if (g && !AI_RUNNING.has(g.ai_status ?? "")) onChanged();
    }, 3000);
    return () => clearInterval(t);
  }, [grade?.ai_status, load, onChanged]);

  function editItem(i: number, points: string) {
    setTouched(true);
    const next = items.map((it, j) => (j === i ? { ...it, points: Math.min(Math.max(Number(points.replace(",", ".")) || 0, 0), it.max_points) } : it));
    setItems(next);
    const max = next.reduce((s, it) => s + it.max_points, 0);
    if (max > 0) setScore(String(Math.round((next.reduce((s, it) => s + it.points, 0) / max) * 10 * 4) / 4));
  }

  async function regrade() {
    setError(null);
    setTouched(false);
    try {
      setGrade(await api<GradeDetail>(`/teacher/submissions/${subId}/regrade`, { method: "POST" }));
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function publish(e: React.FormEvent) {
    e.preventDefault();
    const n = Number(score.replace(",", "."));
    if (score.trim() === "" || Number.isNaN(n) || n < 0 || n > 10) return setError("Nhập điểm từ 0 đến 10.");
    setBusy(true);
    setError(null);
    try {
      await api(`/teacher/grades/${subId}/publish`, {
        json: { score: n, feedback: feedback.trim() || null, breakdown: items.length ? JSON.stringify(items) : null },
      });
      await load();
      onChanged();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const published = grade?.status === "published";
  const ai = grade?.ai_breakdown;
  const running = grade?.ai_status && AI_RUNNING.has(grade.ai_status);

  return (
    <div className="flex min-w-0 flex-col gap-4">
      <Card>
        <CardHeader title={`Bài làm · ${row.name}`}>
          {sub?.is_late && <Pill tone="warn">Nộp muộn</Pill>}
          {sub && <Pill>Đề v{sub.assignment_version}</Pill>}
        </CardHeader>
        {!sub ? (
          <Loading />
        ) : (
          <div className="flex flex-col gap-3">
            {sub.content && <div className="paper whitespace-pre-wrap break-words rounded-[10px] border border-line p-3.5">{sub.content}</div>}
            {sub.has_image && <AuthImage path={`/files/submissions/${sub.id}/image`} alt={`Ảnh bài làm của ${row.name}`} />}
          </div>
        )}
      </Card>

      <Card>
        <CardHeader title={<span className="inline-flex items-center gap-2"><Sparkles size={16} className="text-accent" /> AI chấm nháp</span>}>
          {!published && !running && (
            <Button size="sm" onClick={regrade}>
              <RefreshCw size={14} /> AI chấm lại
            </Button>
          )}
        </CardHeader>
        {!grade ? (
          <Loading />
        ) : running ? (
          <p className="text-sm text-muted">AI đang đọc bài, kiểm tra logic từng bước và chấm theo rubric…</p>
        ) : grade.ai_status === "manual" || grade.ai_status === "failed" ? (
          <Banner tone={grade.ai_status === "failed" ? "bad" : "warn"}>{grade.ai_error}</Banner>
        ) : !ai ? (
          <p className="text-sm text-muted">Chưa có bản chấm nháp. Bấm &quot;AI chấm lại&quot; để AI chấm bài này.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {ai.summary && <Banner>{ai.summary}</Banner>}
            {ai.ocr_text && (
              <details className="text-sm">
                <summary className="cursor-pointer font-semibold">AI đọc được từ ảnh (độ tin cậy {Math.round((ai.image_confidence ?? 0) * 100)}%)</summary>
                <p className="mt-2 whitespace-pre-wrap rounded-lg bg-sunken p-3">{ai.ocr_text}</p>
              </details>
            )}
            <div className="flex flex-col">
              {ai.checks.map((c, i) => {
                const v = VERDICT[c.verdict] ?? VERDICT.missing;
                return (
                  <div key={i} className="grid grid-cols-[26px_minmax(0,1fr)] gap-2.5 border-b border-line py-2.5 last:border-0">
                    <span
                      className={cn(
                        "grid size-[26px] place-items-center rounded-full text-xs font-bold",
                        { ok: "bg-ok-soft text-ok", warn: "bg-warn-soft text-warn", bad: "bg-bad-soft text-bad", mute: "bg-sunken text-muted" }[v.tone],
                      )}
                      title={v.label}
                    >
                      {v.mark}
                    </span>
                    <div className="text-sm">
                      <b>{c.question}</b> · <span className="text-muted">{c.step}</span>
                      <p className="mt-0.5">{c.explanation}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </Card>

      <Card>
        <CardHeader title="Duyệt điểm">
          <div className="font-display text-3xl font-bold tabular-nums leading-none">
            {score || "—"}
            <span className="text-sm text-muted">/10</span>
          </div>
        </CardHeader>
        {!published && <Banner tone="warn">Điểm AI chỉ là bản nháp. Học sinh chỉ thấy điểm sau khi cô/thầy bấm Duyệt &amp; Công bố.</Banner>}
        <form onSubmit={publish} className="mt-3 flex flex-col gap-3">
          {items.length > 0 && (
            <div className="flex flex-col">
              <div className="grid grid-cols-[minmax(0,1fr)_64px_84px] gap-2 pb-1 text-xs font-semibold uppercase tracking-wider text-muted">
                <span>Tiêu chí</span>
                <span className="text-right">Tối đa</span>
                <span className="text-right">Điểm</span>
              </div>
              {items.map((it, i) => (
                <div key={i} className="grid grid-cols-[minmax(0,1fr)_64px_84px] items-center gap-2 border-b border-line py-2 text-sm last:border-0">
                  <span className="min-w-0">
                    {it.criterion}
                    {it.reason && <span className="block text-xs text-muted">{it.reason}</span>}
                  </span>
                  <span className="text-right tabular-nums text-muted">{it.max_points}</span>
                  <Input
                    aria-label={`Điểm ${it.criterion}`}
                    inputMode="decimal"
                    className="px-2 py-1 text-right tabular-nums"
                    value={String(it.points)}
                    disabled={published}
                    onChange={(e) => editItem(i, e.target.value)}
                  />
                </div>
              ))}
            </div>
          )}
          <Field label="Điểm tổng" htmlFor="score" hint="(thang 10)">
            <Input
              id="score"
              inputMode="decimal"
              className="max-w-32 tabular-nums"
              value={score}
              onChange={(e) => {
                setTouched(true);
                setScore(e.target.value);
              }}
              disabled={published}
            />
          </Field>
          <Field label="Nhận xét gửi học sinh" htmlFor="fb">
            <Textarea
              id="fb"
              rows={3}
              value={feedback}
              onChange={(e) => {
                setTouched(true);
                setFeedback(e.target.value);
              }}
              disabled={published}
            />
          </Field>
          <ErrorText error={error} />
          <div className="flex justify-end">
            {published ? (
              <Pill tone="ok">Đã công bố</Pill>
            ) : (
              <Button variant="ok" disabled={busy}>
                <Check size={16} /> Duyệt &amp; Công bố
              </Button>
            )}
          </div>
        </form>
      </Card>
    </div>
  );
}

function Stat({ n, label }: { n: number; label: string }) {
  return (
    <div>
      <b className="block font-display text-2xl tabular-nums">{n}</b>
      <span className="text-xs text-muted">{label}</span>
    </div>
  );
}

function AttachmentManager({ a, onChange }: { a: Assignment; onChange: (a: Assignment) => void }) {
  const ref = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(p: Promise<Assignment>) {
    setBusy(true);
    setError(null);
    try {
      onChange(await p);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function upload(f: File) {
    const form = new FormData();
    form.append("file", f);
    run(api<Assignment>(`/teacher/assignments/${a.id}/attachment`, { form }));
  }

  return (
    <div className="flex flex-col items-start gap-1.5">
      {a.attachment_name && <AttachmentLink assignmentId={a.id} name={a.attachment_name} />}
      <div className="flex flex-wrap gap-1">
        <input
          ref={ref}
          type="file"
          hidden
          accept=".pdf,.docx"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) upload(f);
            e.target.value = "";
          }}
        />
        <Button size="sm" disabled={busy} onClick={() => ref.current?.click()}>
          <Upload size={13} /> {busy ? "Đang tải…" : a.attachment_name ? "Thay file" : "Tải file đề (PDF/Word)"}
        </Button>
        {a.attachment_name && (
          <Button
            size="sm"
            variant="ghost"
            disabled={busy}
            title="Gỡ file đề"
            onClick={() => window.confirm("Gỡ file đề khỏi bài tập?") && run(api<Assignment>(`/teacher/assignments/${a.id}/attachment`, { method: "DELETE" }))}
          >
            <Trash2 size={13} />
          </Button>
        )}
      </div>
      {error && <span className="text-xs text-bad">{error}</span>}
    </div>
  );
}
