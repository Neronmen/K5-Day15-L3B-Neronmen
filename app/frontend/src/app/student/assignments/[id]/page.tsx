"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { ImagePlus, Lock, X } from "lucide-react";

import { AttachmentLink } from "@/components/AttachmentLink";
import { AuthImage } from "@/components/AuthImage";
import { ChatPanel } from "@/components/ChatPanel";
import { Banner, Button, Card, CardHeader, ErrorText, Loading, PageHeader, Pill, Textarea, cn } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate, isPast } from "@/lib/format";
import type { Result, RubricItem, StudentAssignmentDetail, Submission } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

export default function StudentAssignmentPage() {
  const { id } = useParams<{ id: string }>();
  const detail = useLoad<StudentAssignmentDetail>(`/student/assignments/${id}`);
  const result = useLoad<Result>(detail.data?.submission ? `/student/assignments/${id}/result` : null);
  const router = useRouter();

  if (detail.error) return <ErrorText error={detail.error} />;
  if (!detail.data) return <Loading />;
  const { assignment: a, submission, can_submit } = detail.data;
  const overdue = isPast(a.due_at);

  return (
    <>
      <PageHeader
        eyebrow={
          <Link href={`/student/classes/${a.class_id}`} className="hover:text-accent">
            ← Về lớp
          </Link>
        }
        title={a.title}
      >
        {submission ? (
          result.data?.published ? <Pill tone="ok">Đã có điểm</Pill> : <Pill tone="info">Đã nộp · chờ chấm</Pill>
        ) : overdue ? (
          <Pill tone="bad">Quá hạn</Pill>
        ) : (
          <Pill tone="warn">Chưa nộp</Pill>
        )}
      </PageHeader>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="flex min-w-0 flex-col gap-4">
        <Card>
          <CardHeader title="Đề bài">
            <span className="text-xs text-muted">Đề v{a.version}</span>
          </CardHeader>
          <p className="whitespace-pre-wrap">{a.prompt}</p>
          {a.attachment_name && (
            <div className="mt-3">
              <p className="mb-1.5 text-sm text-muted">File đề giáo viên gửi:</p>
              <AttachmentLink assignmentId={a.id} name={a.attachment_name} />
            </div>
          )}
          <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 border-t border-line pt-3 text-sm">
            <dt className="text-muted">Hạn nộp</dt>
            <dd className="font-semibold">{fmtDate(a.due_at)}</dd>
            <dt className="text-muted">Nộp muộn</dt>
            <dd>{a.allow_late ? "Được, bài sẽ gắn nhãn nộp muộn" : "Không"}</dd>
          </dl>
          {a.rubric && (
            <>
              <h3 className="mb-1 mt-4 text-sm font-semibold">Tiêu chí chấm</h3>
              <p className="whitespace-pre-wrap text-sm text-muted">{a.rubric}</p>
            </>
          )}
        </Card>
        <div className="flex min-w-0 flex-col gap-4">
          {submission ? (
            <>
              {result.data?.published && <ResultCard r={result.data} />}
              <SubmittedCard s={submission} published={!!result.data?.published} />
            </>
          ) : can_submit ? (
            <SubmitCard assignmentId={a.id} late={overdue} onDone={detail.reload} />
          ) : (
            <Card>
              <Banner tone="bad">
                <span className="flex items-center gap-2">
                  <Lock size={16} /> Đã hết hạn nộp. Bài này không nhận bài muộn.
                </span>
              </Banner>
            </Card>
          )}
        </div>
        </div>
        <ChatPanel
          className="h-[600px] lg:sticky lg:top-20 lg:h-[calc(100vh-120px)]"
          title="Trợ lý giải bài"
          badge={overdue ? <Pill tone="ok">Đã qua hạn · có lời giải</Pill> : <Pill tone="warn">Chế độ gợi ý</Pill>}
          intro={
            overdue
              ? "Bài đã qua hạn nộp. Em có thể hỏi lời giải chi tiết từng câu."
              : "Mình là trợ lý giải bài. Bài còn hạn nên mình sẽ kiểm tra bước làm và gợi ý phương pháp từ bài giảng, không đưa đáp án cuối. Em gửi bước đang làm để mình xem nhé."
          }
          historyPath={`/student/assignments/${id}/chat`}
          postPath={`/student/assignments/${id}/chat`}
          suggestions={overdue ? ["Giải chi tiết câu 1", "Em sai ở đâu?"] : ["Câu 1 bắt đầu từ đâu?", "Em làm thế này có đúng không?", "Cần dùng công thức nào?"]}
          placeholder={overdue ? "Hỏi lời giải…" : "Gửi bước làm của em hoặc hỏi phương pháp…"}
          onCite={(c) => router.push(`/student/documents/${c.document_id}?page=${c.page_number}`)}
        />
      </div>
    </>
  );
}

const IMG_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic"];

function SubmitCard({ assignmentId, late, onDone }: { assignmentId: string; late: boolean; onDone: () => void }) {
  const [mode, setMode] = useState<"text" | "photo">("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function pick(f: File | undefined) {
    if (!f) return;
    if (!IMG_TYPES.includes(f.type)) return setError("Ảnh cần là JPG, PNG, WEBP hoặc HEIC.");
    if (f.size > 10 * 1024 * 1024) return setError("Ảnh tối đa 10MB.");
    setError(null);
    if (preview) URL.revokeObjectURL(preview);
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  async function submit() {
    const form = new FormData();
    if (text.trim()) form.append("content", text);
    if (file) form.append("image", file);
    if (!text.trim() && !file) {
      setConfirm(false);
      return setError("Bài nộp cần có nội dung hoặc ảnh.");
    }
    setBusy(true);
    setError(null);
    try {
      await api<Submission>(`/student/assignments/${assignmentId}/submit`, { form });
      onDone();
    } catch (e) {
      setError((e as Error).message);
      setConfirm(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Nộp bài">
        <div className="inline-flex gap-0.5 rounded-[10px] bg-sunken p-[3px]" role="group" aria-label="Cách nộp">
          {(["text", "photo"] as const).map((m) => (
            <button
              key={m}
              type="button"
              aria-pressed={mode === m}
              onClick={() => setMode(m)}
              className={cn("rounded-lg px-3 py-1.5 text-sm font-medium text-muted", mode === m && "bg-surface text-ink shadow-sm")}
            >
              {m === "text" ? "Gõ trực tiếp" : "Chụp ảnh vở"}
            </button>
          ))}
        </div>
      </CardHeader>
      {late && (
        <div className="mb-3">
          <Banner tone="warn">Đã qua hạn nộp. Bài nộp bây giờ sẽ được gắn nhãn nộp muộn.</Banner>
        </div>
      )}
      {mode === "text" ? (
        <Textarea
          aria-label="Bài làm"
          rows={10}
          className="paper leading-5"
          placeholder="Câu 1: …"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      ) : (
        <div className="flex flex-col gap-3">
          <input ref={inputRef} type="file" accept="image/*" capture="environment" hidden onChange={(e) => pick(e.target.files?.[0])} />
          {preview ? (
            <div className="relative self-start">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={preview} alt="Ảnh bài làm sẽ nộp" className="max-h-[420px] max-w-full rounded-lg border border-line" />
              <button
                type="button"
                aria-label="Bỏ ảnh"
                onClick={() => {
                  setFile(null);
                  if (preview) URL.revokeObjectURL(preview);
                  setPreview(null);
                }}
                className="absolute right-2 top-2 grid size-8 place-items-center rounded-full bg-ink/70 text-bg"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="rounded-xl border-[1.5px] border-dashed border-line p-8 text-center text-muted hover:border-accent hover:text-accent"
            >
              <ImagePlus className="mx-auto mb-2" />
              <b>Chụp hoặc chọn ảnh bài làm</b>
              <span className="block text-xs">Chụp thẳng, đủ sáng, rõ chữ · tối đa 10MB</span>
            </button>
          )}
        </div>
      )}
      <div className="mt-3">
        <ErrorText error={error} />
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <span className="text-sm text-muted">Nộp xong bài sẽ bị khoá, không sửa được.</span>
        {confirm ? (
          <div className="flex gap-2">
            <Button onClick={() => setConfirm(false)} disabled={busy}>
              Xem lại
            </Button>
            <Button variant="primary" onClick={submit} disabled={busy}>
              {busy ? "Đang nộp…" : "Chắc chắn nộp"}
            </Button>
          </div>
        ) : (
          <Button variant="primary" onClick={() => setConfirm(true)}>
            Nộp bài
          </Button>
        )}
      </div>
    </Card>
  );
}

function SubmittedCard({ s, published }: { s: Submission; published: boolean }) {
  return (
    <Card>
      <CardHeader title="Bài đã nộp">
        <Pill>
          <Lock size={11} /> Đã khoá
        </Pill>
        {s.is_late && <Pill tone="warn">Nộp muộn</Pill>}
      </CardHeader>
      <div className="flex flex-col gap-3">
        {s.content && <div className="paper whitespace-pre-wrap break-words rounded-[10px] border border-line p-3.5">{s.content}</div>}
        {s.has_image && <AuthImage path={`/files/submissions/${s.id}/image`} alt="Ảnh bài làm đã nộp" />}
        {!published && <Banner>Nộp lúc {fmtDate(s.submitted_at)}. Điểm và nhận xét hiện ra khi giáo viên chấm xong và công bố.</Banner>}
      </div>
    </Card>
  );
}

function ResultCard({ r }: { r: Result }) {
  let items: RubricItem[] = [];
  try {
    items = r.breakdown ? (JSON.parse(r.breakdown) as RubricItem[]) : [];
  } catch {
    items = [];
  }
  return (
    <Card>
      <CardHeader title="Kết quả">
        <div className="font-display text-4xl font-bold tabular-nums leading-none">
          {r.score}
          <span className="text-base text-muted">/10</span>
        </div>
      </CardHeader>
      {items.length > 0 && (
        <div className="mb-3 flex flex-col">
          {items.map((it, i) => (
            <div key={i} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 border-b border-line py-2 text-sm last:border-0">
              <span className="font-medium">{it.criterion}</span>
              <span className="tabular-nums">
                <b>{it.points}</b>
                <span className="text-muted">/{it.max_points}</span>
              </span>
              {it.reason && <span className="col-span-2 text-xs text-muted">{it.reason}</span>}
            </div>
          ))}
        </div>
      )}
      {r.feedback && (
        <Banner tone="ok">
          <b>Nhận xét của giáo viên:</b> {r.feedback}
        </Banner>
      )}
    </Card>
  );
}
