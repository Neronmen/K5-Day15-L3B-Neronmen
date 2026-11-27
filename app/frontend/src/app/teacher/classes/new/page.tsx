"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Card, ErrorText, Field, Input, LinkButton, PageHeader, Select } from "@/components/ui";
import { api } from "@/lib/api";
import type { AIMode, ClassOut } from "@/lib/types";

const SUBJECTS = ["Toán", "Vật lý", "Hoá học", "Sinh học", "Ngữ văn", "Tiếng Anh", "Lịch sử", "Địa lý", "Tin học"];

export default function NewClassPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [subject, setSubject] = useState(SUBJECTS[0]);
  const [mode, setMode] = useState<AIMode>("strict");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const c = await api<ClassOut>("/teacher/classes", { json: { name, subject, ai_mode: mode } });
      router.push(`/teacher/classes/${c.id}`);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="Lớp học" title="Tạo lớp mới" />
      <Card className="max-w-2xl">
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <Field label="Tên lớp" htmlFor="name">
            <Input id="name" required placeholder="VD: Toán 10A1 - Học kỳ 1" value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Môn học" htmlFor="subject">
            <Select id="subject" value={subject} onChange={(e) => setSubject(e.target.value)}>
              {SUBJECTS.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </Select>
          </Field>
          <fieldset className="flex flex-col gap-1.5">
            <legend className="mb-1.5 text-sm font-semibold">Chế độ AI</legend>
            <div className="grid gap-2.5 sm:grid-cols-2">
              <ModeOption value="strict" current={mode} onChange={setMode} title="Khoá cứng" desc="AI chỉ dùng bài giảng của lớp. Ngoài bài giảng thì từ chối trả lời." />
              <ModeOption
                value="extended"
                current={mode}
                onChange={setMode}
                title="Mở rộng có trích nguồn"
                desc="Được dùng kiến thức ngoài, nhưng phải gắn nhãn và ghi rõ nguồn."
              />
            </div>
          </fieldset>
          <ErrorText error={error} />
          <div className="flex justify-end gap-2">
            <LinkButton href="/teacher">Huỷ</LinkButton>
            <Button variant="primary" disabled={busy}>
              {busy ? "Đang tạo…" : "Tạo lớp"}
            </Button>
          </div>
        </form>
      </Card>
    </>
  );
}

function ModeOption({
  value,
  current,
  onChange,
  title,
  desc,
}: {
  value: AIMode;
  current: AIMode;
  onChange: (m: AIMode) => void;
  title: string;
  desc: string;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-2.5 rounded-[10px] border border-line p-3 has-[:checked]:border-accent has-[:checked]:bg-accent-soft">
      <input type="radio" name="mode" className="mt-1 accent-accent" checked={current === value} onChange={() => onChange(value)} />
      <span>
        <b className="block text-sm">{title}</b>
        <span className="text-xs text-muted">{desc}</span>
      </span>
    </label>
  );
}
