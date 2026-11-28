"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Copy, FileText, MapPin, Paperclip, Plus, RefreshCw, Trash2, Upload } from "lucide-react";

import { AnnouncementForm } from "@/components/AnnouncementForm";
import { AnnouncementList } from "@/components/AnnouncementList";
import { ChatInsights } from "@/components/ChatInsights";
import {
  Avatar, Banner, Button, Card, CardHeader, Empty, ErrorText, Field, Input, LinkButton, Loading, ModeLabel, PageHeader, Pill,
  Select, Textarea, cn,
} from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate, initials, isPast } from "@/lib/format";
import { WEEKDAYS } from "@/lib/schedule";
import type { AddStudentsOut, Announcement, ClassDetail, DocumentOut } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

type Tab = "students" | "documents" | "assignments" | "chats" | "announcements" | "schedule";
const TABS: { id: Tab; label: string }[] = [
  { id: "assignments", label: "Bài tập" },
  { id: "announcements", label: "Thông báo" },
  { id: "schedule", label: "Lịch học" },
  { id: "students", label: "Học sinh" },
  { id: "documents", label: "Tài liệu bài giảng" },
  { id: "chats", label: "Lịch sử hỏi AI" },
];

export default function ClassPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, reload } = useLoad<ClassDetail>(`/teacher/classes/${id}`);
  const [tab, setTab] = useState<Tab>("assignments");

  // Mở thẳng một tab qua ?tab=... (vd từ trang Lịch dạy)
  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get("tab") as Tab | null;
    if (t && TABS.some((x) => x.id === t)) setTab(t);
  }, []);

  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  const c = data.cls;

  return (
    <>
      <PageHeader
        eyebrow={
          <Link href="/teacher" className="normal-case tracking-normal hover:underline">
            ← Các lớp · {c.subject}
          </Link>
        }
        title={c.name}
      >
        <ModeLabel mode={c.ai_mode} />
      </PageHeader>
      <ClassCode code={c.class_code} />
      <div role="tablist" className="no-scrollbar flex gap-1 overflow-x-auto border-b border-line">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "-mb-px whitespace-nowrap border-b-2 border-transparent px-3 py-2 font-medium text-muted hover:text-ink",
              tab === t.id && "border-accent text-accent hover:text-accent",
            )}
          >
            {t.label}
            {t.id !== "chats" && (
              <span className="ml-1.5 text-xs tabular-nums">
                {
                  {
                    students: data.members.length,
                    documents: data.documents.length,
                    assignments: data.assignments.length,
                    announcements: data.announcements.length,
                    schedule: data.sessions.length,
                  }[t.id]
                }
              </span>
            )}
          </button>
        ))}
      </div>
      {tab === "students" && <StudentsTab classId={c.id} data={data} reload={reload} />}
      {tab === "documents" && <DocumentsTab classId={c.id} docs={data.documents} reload={reload} />}
      {tab === "assignments" && <AssignmentsTab classId={c.id} data={data} />}
      {tab === "chats" && <ChatInsights classId={c.id} />}
      {tab === "announcements" && <AnnouncementsTab classId={c.id} data={data} reload={reload} />}
      {tab === "schedule" && <ScheduleTab classId={c.id} data={data} reload={reload} />}
    </>
  );
}

function ClassCode({ code }: { code: string }) {
  const [msg, setMsg] = useState<string | null>(null);
  const ref = useRef<HTMLSpanElement>(null);
  return (
    <Card className="flex flex-wrap items-center gap-3">
      <span className="text-sm text-muted">Mã tham gia lớp</span>
      <span ref={ref} className="rounded-md bg-sunken px-3 py-1 font-mono text-lg tracking-wider">
        {code}
      </span>
      <Button
        size="sm"
        onClick={() =>
          navigator.clipboard
            ?.writeText(code)
            .then(() => setMsg("Đã sao chép"))
            .catch(() => {
              if (ref.current) getSelection()?.selectAllChildren(ref.current);
              setMsg("Bôi đen mã rồi nhấn Ctrl+C");
            })
        }
      >
        <Copy size={14} /> Sao chép
      </Button>
      <span className="text-sm text-muted">{msg ?? "Học sinh nhập mã này ở trang chủ để vào lớp."}</span>
    </Card>
  );
}

function StudentsTab({ classId, data, reload }: { classId: string; data: ClassDetail; reload: () => void }) {
  const [emails, setEmails] = useState("");
  const [result, setResult] = useState<AddStudentsOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function run(p: Promise<AddStudentsOut>) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await p);
      setEmails("");
      reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function addByEmail(e: React.FormEvent) {
    e.preventDefault();
    const list = emails.split(/[\s,;]+/).map((s) => s.trim()).filter(Boolean);
    if (!list.length) return setError("Nhập ít nhất một email.");
    run(api<AddStudentsOut>(`/teacher/classes/${classId}/students`, { json: { emails: list } }));
  }

  function importCsv(file: File) {
    const form = new FormData();
    form.append("file", file);
    run(api<AddStudentsOut>(`/teacher/classes/${classId}/students/import`, { form }));
  }

  async function remove(studentId: string, name: string) {
    if (!window.confirm(`Xoá ${name} khỏi lớp?`)) return;
    try {
      await api(`/teacher/classes/${classId}/students/${studentId}`, { method: "DELETE" });
      reload();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
      <Card className="flex flex-col gap-3 self-start">
        <CardHeader title="Thêm học sinh" />
        <form onSubmit={addByEmail} className="flex flex-col gap-3">
          <label htmlFor="emails" className="text-sm text-muted">
            Email học sinh, mỗi dòng một người. Email chưa có tài khoản sẽ được tạo sẵn, học sinh đăng ký bằng email đó là vào lớp.
          </label>
          <Textarea id="emails" rows={4} placeholder={"minhanh@hs.edu.vn\ngiabao@hs.edu.vn"} value={emails} onChange={(e) => setEmails(e.target.value)} />
          <Button variant="primary" disabled={busy}>
            <Plus size={16} /> Thêm vào lớp
          </Button>
        </form>
        <div className="border-t border-line pt-3">
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) importCsv(f);
              e.target.value = "";
            }}
          />
          <Button onClick={() => fileRef.current?.click()} disabled={busy} className="w-full">
            <Upload size={16} /> Import file CSV
          </Button>
          <p className="mt-2 text-xs text-muted">Cần cột Email, cột Họ tên không bắt buộc. Với Excel: Lưu dưới dạng CSV UTF-8.</p>
        </div>
        <ErrorText error={error} />
        {result && (
          <Banner tone={result.added.length ? "ok" : "warn"}>
            Đã thêm {result.added.length} học sinh.
            {result.already_in_class.length > 0 && ` ${result.already_in_class.length} người đã có trong lớp.`}
            {result.invalid.length > 0 && ` Bỏ qua ${result.invalid.length} email không hợp lệ: ${result.invalid.join(", ")}.`}
          </Banner>
        )}
      </Card>
      <Card>
        <CardHeader title={`Danh sách lớp (${data.members.length})`} />
        {data.members.length === 0 ? (
          <Empty>Lớp chưa có học sinh.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-muted">
                  <th className="border-b border-line px-2.5 py-2 font-semibold">Họ tên</th>
                  <th className="border-b border-line px-2.5 py-2 font-semibold">Email</th>
                  <th className="border-b border-line px-2.5 py-2 font-semibold">Trạng thái</th>
                  <th className="border-b border-line px-2.5 py-2" />
                </tr>
              </thead>
              <tbody>
                {data.members.map((m) => (
                  <tr key={m.id} className="border-b border-line last:border-0">
                    <td className="px-2.5 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <Avatar text={initials(m.name)} />
                        {m.name}
                      </div>
                    </td>
                    <td className="px-2.5 py-2.5 text-muted">{m.email}</td>
                    <td className="px-2.5 py-2.5">{m.activated ? <Pill tone="ok">Đã kích hoạt</Pill> : <Pill tone="warn">Chờ đăng ký</Pill>}</td>
                    <td className="px-2.5 py-2.5 text-right">
                      <Button variant="ghost" size="sm" onClick={() => remove(m.id, m.name)}>
                        Xoá
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function DocStatusPill({ d }: { d: DocumentOut }) {
  if (d.status === "ready") return <Pill tone="ok">Sẵn sàng cho AI</Pill>;
  if (d.status === "failed") return <Pill tone="bad">Lỗi xử lý</Pill>;
  return <Pill tone="info">Đang bóc tách…</Pill>;
}

function DocumentsTab({ classId, docs, reload }: { classId: string; docs: DocumentOut[]; reload: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const processing = docs.some((d) => d.status === "processing");

  // Tài liệu đang xử lý ở worker: hỏi lại trạng thái mỗi 3 giây
  useEffect(() => {
    if (!processing) return;
    const t = setInterval(reload, 3000);
    return () => clearInterval(t);
  }, [processing, reload]);

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    setError(null);
    try {
      for (const f of Array.from(files)) {
        const form = new FormData();
        form.append("file", f);
        await api(`/teacher/classes/${classId}/documents`, { form });
      }
      reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function act(path: string, method: string) {
    setError(null);
    try {
      await api(path, { method });
      reload();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Banner>
        AI chỉ dùng tài liệu ở đây để trả lời học sinh của lớp này. Mỗi tài liệu được bóc tách theo trang, nên câu trả lời luôn ghi được
        nguồn dạng <span className="rounded bg-mark px-1 text-xs font-semibold text-mark-ink">Nguồn: Ten_file.pdf - Trang 7</span>.
      </Banner>
      <Card>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            upload(e.dataTransfer.files);
          }}
          disabled={busy}
          className={cn(
            "w-full rounded-xl border-[1.5px] border-dashed border-line p-6 text-center text-muted transition hover:border-accent hover:text-accent",
            drag && "border-accent bg-accent-soft text-accent",
          )}
        >
          <Upload className="mx-auto mb-2" />
          <b>{busy ? "Đang tải lên…" : "Chọn hoặc kéo thả PDF, Word (.docx), Slide (.pptx)"}</b>
          <span className="block text-xs">Tối đa 50MB mỗi file · PDF scan ảnh chưa đọc được chữ</span>
        </button>
        <input ref={inputRef} type="file" multiple hidden accept=".pdf,.docx,.pptx" onChange={(e) => upload(e.target.files)} />
        <div className="mt-2">
          <ErrorText error={error} />
        </div>
      </Card>
      <Card>
        <CardHeader title={`Đã đăng (${docs.length})`} />
        {docs.length === 0 ? (
          <Empty>Chưa có tài liệu nào.</Empty>
        ) : (
          docs.map((d) => (
            <div key={d.id} className="flex flex-wrap items-center gap-3 border-b border-line py-3 last:border-0">
              <FileText className="flex-none text-muted" />
              <div className="min-w-0 flex-1">
                <div className="break-words font-semibold">{d.file_name}</div>
                <div className="text-xs text-muted">
                  Tải lên {fmtDate(d.uploaded_at)}
                  {d.page_count ? ` · ${d.page_count} trang` : ""}
                </div>
                {d.error && <div className="mt-1 text-xs text-bad">{d.error}</div>}
              </div>
              <DocStatusPill d={d} />
              <div className="flex gap-1">
                {d.status !== "processing" && (
                  <Button variant="ghost" size="sm" title="Xử lý lại" onClick={() => act(`/teacher/documents/${d.id}/reprocess`, "POST")}>
                    <RefreshCw size={14} />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  title="Xoá tài liệu"
                  onClick={() => {
                    if (window.confirm(`Xoá ${d.file_name}? AI sẽ không dùng tài liệu này nữa.`)) act(`/teacher/documents/${d.id}`, "DELETE");
                  }}
                >
                  <Trash2 size={14} />
                </Button>
              </div>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}

function AssignmentsTab({ classId, data }: { classId: string; data: ClassDetail }) {
  return (
    <Card>
      <CardHeader title="Bài tập">
        <LinkButton href={`/teacher/classes/${classId}/assignments/new`} variant="primary" size="sm">
          <Plus size={15} /> Tạo bài tập
        </LinkButton>
      </CardHeader>
      {data.assignments.length === 0 ? (
        <Empty>Chưa có bài tập. Tạo bài tập đầu tiên với hạn nộp và rubric chấm.</Empty>
      ) : (
        data.assignments.map((a) => (
          <LinkRow key={a.id} href={`/teacher/assignments/${a.id}`}>
            <div className="min-w-0 flex-1">
              <b>{a.title}</b>
              <div className="text-xs text-muted">
                Hạn {fmtDate(a.due_at)} · đề v{a.version}
                {a.attachment_name && (
                  <span className="ml-1 inline-flex items-center gap-0.5">
                    · <Paperclip size={11} /> có file đề
                  </span>
                )}
              </div>
            </div>
            {isPast(a.due_at) ? <Pill>Đã hết hạn</Pill> : <Pill tone="info">Đang mở</Pill>}
          </LinkRow>
        ))
      )}
    </Card>
  );
}

function LinkRow({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="flex items-center gap-3 rounded-xl px-3 py-3 hover:bg-sunken">
      {children}
    </Link>
  );
}

function AnnouncementsTab({ classId, data, reload }: { classId: string; data: ClassDetail; reload: () => void }) {
  const [error, setError] = useState<string | null>(null);

  async function act(p: Promise<unknown>) {
    setError(null);
    try {
      await p;
      reload();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,400px)_minmax(0,1fr)]">
      <Card>
        <CardHeader title="Đăng thông báo" />
        <AnnouncementForm classId={classId} sessions={data.sessions} onDone={reload} />
      </Card>
      <Card>
        <CardHeader title={`Đã đăng (${data.announcements.length})`} />
        <p className="mb-3 text-sm text-muted">
          Học sinh nhận thông báo ở chuông góc trên. Báo nghỉ / học bù tự cập nhật trên lịch học của lớp.
        </p>
        <ErrorText error={error} />
        <AnnouncementList
          items={data.announcements}
          empty="Lớp chưa có thông báo nào."
          onPin={(a: Announcement) => act(api(`/teacher/announcements/${a.id}`, { method: "PATCH", json: { pinned: !a.pinned } }))}
          onDelete={(a: Announcement) => {
            const msg = a.kind === "cancel" ? "Xoá báo nghỉ này? Buổi học sẽ hiện lại bình thường trên lịch." : "Xoá thông báo này?";
            if (window.confirm(msg)) act(api(`/teacher/announcements/${a.id}`, { method: "DELETE" }));
          }}
        />
      </Card>
    </div>
  );
}

function ScheduleTab({ classId, data, reload }: { classId: string; data: ClassDetail; reload: () => void }) {
  const [weekday, setWeekday] = useState("0");
  const [start, setStart] = useState("18:00");
  const [end, setEnd] = useState("19:30");
  const [room, setRoom] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api(`/teacher/classes/${classId}/sessions`, {
        json: { weekday: Number(weekday), start_time: start, end_time: end, room: room.trim() || null },
      });
      setRoom("");
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Xoá buổi học này khỏi lịch hằng tuần?")) return;
    setError(null);
    try {
      await api(`/teacher/sessions/${id}`, { method: "DELETE" });
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
      <Card>
        <CardHeader title="Thêm buổi học hằng tuần" />
        <form onSubmit={add} className="flex flex-col gap-3">
          <Field label="Thứ" htmlFor="s-day">
            <Select id="s-day" value={weekday} onChange={(e) => setWeekday(e.target.value)}>
              {WEEKDAYS.map((w, i) => (
                <option key={w} value={i}>
                  {w}
                </option>
              ))}
            </Select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Bắt đầu" htmlFor="s-start">
              <Input id="s-start" type="time" required value={start} onChange={(e) => setStart(e.target.value)} />
            </Field>
            <Field label="Kết thúc" htmlFor="s-end">
              <Input id="s-end" type="time" required value={end} onChange={(e) => setEnd(e.target.value)} />
            </Field>
          </div>
          <Field label="Phòng / link học online" htmlFor="s-room" hint="(không bắt buộc)">
            <Input id="s-room" maxLength={200} placeholder="VD: P.204 hoặc meet.google.com/…" value={room} onChange={(e) => setRoom(e.target.value)} />
          </Field>
          <ErrorText error={error} />
          <Button variant="primary" disabled={busy}>
            <Plus size={16} /> Thêm vào lịch
          </Button>
        </form>
      </Card>
      <Card>
        <CardHeader title="Lịch học cố định">
          <LinkButton href="/teacher/schedule" size="sm">
            Xem lịch dạy theo tuần
          </LinkButton>
        </CardHeader>
        {data.sessions.length === 0 ? (
          <Empty>Lớp chưa có lịch học. Thêm các buổi học lặp lại hằng tuần ở bên trái.</Empty>
        ) : (
          data.sessions.map((s) => (
            <div key={s.id} className="flex items-center gap-3 border-b border-line py-3 last:border-0">
              <span className="w-[78px] flex-none font-semibold">{WEEKDAYS[s.weekday]}</span>
              <span className="font-mono tabular-nums">
                {s.start_time}–{s.end_time}
              </span>
              <span className="flex min-w-0 flex-1 items-center gap-1 break-all text-sm text-muted">
                {s.room && (
                  <>
                    <MapPin size={13} className="flex-none" /> {s.room}
                  </>
                )}
              </span>
              <Button variant="ghost" size="sm" title="Xoá buổi học" onClick={() => remove(s.id)}>
                <Trash2 size={14} />
              </Button>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
