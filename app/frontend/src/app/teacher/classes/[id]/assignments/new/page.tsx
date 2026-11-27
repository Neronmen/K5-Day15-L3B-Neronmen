"use client";

import { useParams, useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { Paperclip, X } from "lucide-react";

import { Button, Card, ErrorText, Field, Input, LinkButton, PageHeader, Textarea } from "@/components/ui";
import { api } from "@/lib/api";
import { toLocalInput } from "@/lib/format";
import type { Assignment } from "@/lib/types";

function defaultDue() {
  const d = new Date();
  d.setDate(d.getDate() + 7);
  d.setHours(23, 59, 0, 0);
  return toLocalInput(d);
}

export default function NewAssignmentPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [due, setDue] = useState(defaultDue);
  const [allowLate, setAllowLate] = useState(true);
  const [rubric, setRubric] = useState("");
  const [answer, setAnswer] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const dueDate = new Date(due);
    if (Number.isNaN(dueDate.getTime())) return setError("Chọn hạn nộp hợp lệ.");
    if (!prompt.trim() && !file) return setError("Nhập đề bài hoặc đính kèm file đề.");
    if (file && !/\.(pdf|docx)$/i.test(file.name)) return setError("File đề chỉ nhận PDF hoặc Word (.docx).");
    setBusy(true);
    setError(null);
    try {
      const a = await api<Assignment>(`/teacher/classes/${id}/assignments`, {
        json: {
          title,
          prompt: prompt.trim() || "Xem đề trong file đính kèm.",
          due_at: dueDate.toISOString(),
          allow_late: allowLate,
          rubric: rubric.trim() || null,
          reference_answer: answer.trim() || null,
        },
      });
      if (file) {
        const form = new FormData();
        form.append("file", file);
        try {
          await api(`/teacher/assignments/${a.id}/attachment`, { form });
        } catch (err) {
          // Bài đã giao; báo lỗi file để giáo viên tải lại ở trang bài tập
          window.alert(`Đã giao bài nhưng chưa tải được file đề: ${(err as Error).message}. Hãy tải lại ở trang bài tập.`);
        }
      }
      router.push(`/teacher/assignments/${a.id}`);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Bài tập mới" title="Tạo bài tập" />
      <Card className="max-w-3xl">
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <Field label="Tên bài" htmlFor="title">
            <Input id="title" required placeholder="VD: Bài tập 3 — Đạo hàm hàm hợp" value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>
          <Field label="File đề" htmlFor="file" hint="(PDF hoặc Word, không bắt buộc)">
            <input
              ref={fileRef}
              id="file"
              type="file"
              accept=".pdf,.docx"
              hidden
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            {file ? (
              <div className="flex items-center gap-2 rounded-[9px] border border-line px-3 py-2 text-sm">
                <Paperclip size={15} className="flex-none text-muted" />
                <span className="min-w-0 flex-1 break-all">{file.name}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  aria-label="Bỏ file"
                  onClick={() => {
                    setFile(null);
                    if (fileRef.current) fileRef.current.value = "";
                  }}
                >
                  <X size={14} />
                </Button>
              </div>
            ) : (
              <Button type="button" onClick={() => fileRef.current?.click()} className="self-start">
                <Paperclip size={15} /> Chọn file đề
              </Button>
            )}
            <span className="text-xs text-muted">Học sinh tải được file này. AI gia sư và AI chấm đọc chữ trong file (PDF scan ảnh thì không đọc được).</span>
          </Field>
          <Field label="Đề bài" htmlFor="prompt" hint={file ? "(không bắt buộc khi đã có file đề)" : undefined}>
            <Textarea
              id="prompt"
              required={!file}
              rows={7}
              placeholder={"Câu 1: Tính đạo hàm của y = (2x² − 3x + 1)⁵\nCâu 2: …"}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Hạn nộp" htmlFor="due">
              <Input id="due" type="datetime-local" required value={due} onChange={(e) => setDue(e.target.value)} />
            </Field>
            <Field label="Nộp muộn" htmlFor="late">
              <label className="flex items-center gap-2 rounded-[9px] border border-line px-3 py-2">
                <input id="late" type="checkbox" className="accent-accent" checked={allowLate} onChange={(e) => setAllowLate(e.target.checked)} />
                Cho phép, gắn nhãn &quot;Nộp muộn&quot;
              </label>
            </Field>
          </div>
          <Field label="Rubric chấm" htmlFor="rubric" hint="(không bắt buộc)">
            <Textarea
              id="rubric"
              rows={4}
              placeholder={"Câu 1 — áp dụng đúng quy tắc hàm hợp: 3đ\nCâu 2 — …: 3đ\nCâu 3 — …: 4đ"}
              value={rubric}
              onChange={(e) => setRubric(e.target.value)}
            />
          </Field>
          <Field label="Đáp án mẫu" htmlFor="answer" hint="(học sinh không thấy; AI chỉ dùng sau hạn nộp)">
            <Textarea id="answer" rows={4} value={answer} onChange={(e) => setAnswer(e.target.value)} />
          </Field>
          <ErrorText error={error} />
          <div className="flex justify-end gap-2">
            <LinkButton href={`/teacher/classes/${id}`}>Huỷ</LinkButton>
            <Button variant="primary" disabled={busy}>
              {busy ? "Đang giao…" : "Giao bài cho lớp"}
            </Button>
          </div>
        </form>
      </Card>
    </>
  );
}
