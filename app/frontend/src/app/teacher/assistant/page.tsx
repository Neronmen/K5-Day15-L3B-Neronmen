"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { BookOpen, Copy, FileText, Globe, Save, Search, SendHorizontal, Sparkles, Trash2, X } from "lucide-react";

import { Answer } from "@/components/Answer";
import { TextPagesViewer } from "@/components/TextPagesViewer";
import { Banner, Button, Card, CardHeader, Empty, ErrorText, Input, Loading, PageHeader, Pill, Select, cn } from "@/components/ui";
import { api } from "@/lib/api";
import { streamChat } from "@/lib/sse";
import type { AssistantTask, Citation, DocPage, DocumentOut, SearchHit, SourceClass, SourceDoc, WebSource } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

const PdfViewer = dynamic(() => import("@/components/PdfViewer"), {
  ssr: false,
  loading: () => <div className="h-full rounded-xl bg-sunken p-4 text-sm text-muted">Đang mở tài liệu…</div>,
});

const TASKS: { id: AssistantTask; label: string; prompt: (doc?: string) => string; hint: string }[] = [
  { id: "ask", label: "Hỏi & tìm", prompt: () => "", hint: "VD: Bài giảng nào nói về quy tắc dây chuyền?" },
  { id: "summary", label: "Tóm tắt", prompt: (d) => (d ? `Tóm tắt tài liệu ${d}` : ""), hint: "Chủ đề cần tóm tắt, vd: Đạo hàm hàm hợp" },
  { id: "outline", label: "Đề cương ôn tập", prompt: (d) => (d ? `Soạn đề cương ôn tập từ ${d}` : ""), hint: "Chủ đề ôn tập, vd: Chương Đạo hàm" },
  { id: "quiz", label: "Câu hỏi ôn tập", prompt: (d) => (d ? `Soạn câu hỏi ôn tập từ ${d}` : ""), hint: "Chủ đề ra câu hỏi, vd: Đạo hàm lượng giác" },
  { id: "lesson", label: "Dàn ý bài giảng", prompt: (d) => (d ? `Gợi ý dàn ý bài giảng từ ${d}` : ""), hint: "Chủ đề tiết học, vd: Đạo hàm của hàm hợp" },
];

type Source = "docs" | "web";
type Msg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  streaming?: boolean;
  error?: boolean;
  /** Tìm trên Google: câu truy vấn đã dùng và các trang tìm được */
  query?: string;
  webSources?: WebSource[];
};

const WEB_HINT = "Chủ đề cần tìm trên Google, vd: Ứng dụng của đạo hàm trong thực tế";

export default function TeacherAssistantPage() {
  const sources = useLoad<SourceClass[]>("/teacher/assistant/sources");
  const status = useLoad<{ web_search: boolean }>("/teacher/assistant/status");
  const webEnabled = !!status.data?.web_search;
  const [classIds, setClassIds] = useState<string[]>([]);
  const [docId, setDocId] = useState("");
  const [tab, setTab] = useState<"chat" | "search">("chat");
  const [view, setView] = useState<{ doc: SourceDoc; page: number; key: number } | null>(null);

  const docs = useMemo(() => {
    const m = new Map<string, SourceDoc & { class_id: string; class_name: string }>();
    for (const c of sources.data ?? []) for (const d of c.documents) m.set(d.id, { ...d, class_id: c.id, class_name: c.name });
    return m;
  }, [sources.data]);
  const inScope = (sources.data ?? []).filter((c) => !classIds.length || classIds.includes(c.id));
  const selectedDoc = docId ? docs.get(docId) : undefined;
  const scope = { class_ids: classIds, document_ids: docId ? [docId] : [] };
  const totalDocs = (sources.data ?? []).reduce((n, c) => n + c.documents.length, 0);

  function toggleClass(id: string) {
    setClassIds((all) => {
      const next = all.includes(id) ? all.filter((x) => x !== id) : [...all, id];
      if (docId && next.length && !next.includes(docs.get(docId)?.class_id ?? "")) setDocId("");
      return next;
    });
  }

  function open(documentId: string, page: number) {
    const d = docs.get(documentId);
    if (d) setView((v) => ({ doc: d, page, key: (v?.key ?? 0) + 1 }));
  }

  return (
    <>
      <PageHeader eyebrow="Tìm kiếm & tổng hợp tài liệu" title="Trợ lý AI">
        <span className="hidden sm:block">
          <Pill tone="info">{webEnabled ? "Tài liệu lớp hoặc Google, luôn kèm nguồn" : "Chỉ dùng tài liệu các lớp của cô/thầy"}</Pill>
        </span>
      </PageHeader>
      <ErrorText error={sources.error} />
      {!sources.data && !sources.error && <Loading />}
      {sources.data && totalDocs === 0 && (
        <Banner tone="warn">
          Chưa có tài liệu nào sẵn sàng. Vào một lớp → tab <b>Tài liệu bài giảng</b> để tải PDF, Word hoặc Slide, rồi quay lại đây.
          {webEnabled && (
            <>
              {" "}
              Trong lúc chờ, cô/thầy vẫn có thể chọn <b>Google</b> bên dưới để AI tìm và tổng hợp tài liệu trên mạng.
            </>
          )}
        </Banner>
      )}
      {sources.data && (totalDocs > 0 || webEnabled) && (
        <>
          {totalDocs > 0 && (
            <Card className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold">Phạm vi:</span>
                <button
                  onClick={() => {
                    setClassIds([]);
                  }}
                  className={cn("rounded-full border px-3 py-1 text-sm", !classIds.length ? "border-accent bg-accent-soft text-accent" : "border-line text-muted")}
                >
                  Tất cả lớp
                </button>
                {sources.data.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => toggleClass(c.id)}
                    aria-pressed={classIds.includes(c.id)}
                    className={cn(
                      "rounded-full border px-3 py-1 text-sm",
                      classIds.includes(c.id) ? "border-accent bg-accent-soft text-accent" : "border-line text-muted hover:text-ink",
                    )}
                  >
                    {c.name} <span className="text-xs">({c.documents.length})</span>
                  </button>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <label htmlFor="doc" className="text-sm font-semibold">
                  Tài liệu:
                </label>
                <Select id="doc" value={docId} onChange={(e) => setDocId(e.target.value)} className="w-auto max-w-full">
                  <option value="">Tất cả tài liệu trong phạm vi</option>
                  {inScope.map((c) => (
                    <optgroup key={c.id} label={c.name}>
                      {c.documents.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.file_name}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </Select>
                {selectedDoc && (
                  <span className="text-xs text-muted">Tóm tắt / đề cương / câu hỏi sẽ đọc toàn bộ tài liệu này.</span>
                )}
              </div>
            </Card>
          )}

          <div role="tablist" className="flex gap-1 border-b border-line">
            {[
              { id: "chat" as const, label: "Hỏi & tổng hợp", icon: Sparkles },
              { id: "search" as const, label: "Tìm kiếm nhanh", icon: Search },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                role="tab"
                aria-selected={tab === id}
                onClick={() => setTab(id)}
                className={cn(
                  "-mb-px inline-flex items-center gap-1.5 border-b-2 border-transparent px-3 py-2 font-medium text-muted hover:text-ink",
                  tab === id && "border-accent text-accent hover:text-accent",
                )}
              >
                <Icon size={15} /> {label}
              </button>
            ))}
          </div>

          <div className={cn("grid gap-4", view && "lg:h-[calc(100vh_-_120px)] lg:min-h-[560px] lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:grid-rows-1")}>
            <div className={cn("min-w-0", view && "lg:h-full")}>
              {tab === "chat" ? (
                <AssistantChat
                  scope={scope}
                  selectedDoc={selectedDoc}
                  classes={sources.data}
                  onCite={(c) => open(c.document_id, c.page_number)}
                  tall={!!view}
                  webEnabled={webEnabled}
                  hasDocs={totalDocs > 0}
                />
              ) : (
                <SearchPanel scope={scope} onOpen={open} />
              )}
            </div>
            {view && (
              <div className="flex h-[560px] min-w-0 flex-col gap-2 lg:h-full">
                <div className="flex items-center gap-2">
                  <FileText size={16} className="flex-none text-muted" />
                  <b className="min-w-0 flex-1 truncate text-sm">{view.doc.file_name}</b>
                  <Button variant="ghost" size="sm" aria-label="Đóng tài liệu" onClick={() => setView(null)}>
                    <X size={15} />
                  </Button>
                </div>
                <div className="min-h-0 flex-1">
                  <DocViewer doc={view.doc} page={view.page} flashKey={view.key} />
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
}

function DocViewer({ doc, page, flashKey }: { doc: SourceDoc; page: number; flashKey: number }) {
  const [pages, setPages] = useState<DocPage[] | null>(null);
  useEffect(() => {
    setPages(null);
    if (!doc.is_pdf) api<DocPage[]>(`/teacher/assistant/documents/${doc.id}/pages`).then(setPages).catch(() => setPages([]));
  }, [doc]);
  if (doc.is_pdf) return <PdfViewer documentId={doc.id} page={page} flashKey={flashKey} />;
  if (!pages) return <Loading />;
  return <TextPagesViewer pages={pages} unit={doc.unit} page={page} flashKey={flashKey} />;
}

type Scope = { class_ids: string[]; document_ids: string[] };

function SearchPanel({ scope, onOpen }: { scope: Scope; onOpen: (docId: string, page: number) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setHits(await api<SearchHit[]>("/teacher/assistant/search", { json: { ...scope, query: q } }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="flex h-full min-h-0 flex-col">
      <form onSubmit={run} className="flex gap-2">
        <Input aria-label="Từ khoá" placeholder="Từ khoá, gõ có dấu hoặc không dấu: dao ham ham hop" value={q} onChange={(e) => setQ(e.target.value)} />
        <Button variant="primary" disabled={busy}>
          <Search size={15} /> Tìm
        </Button>
      </form>
      <p className="mt-2 text-xs text-muted">Tìm theo từ khoá trong tài liệu đã đăng, không dùng lượt AI. Bấm kết quả để mở đúng trang.</p>
      <ErrorText error={error} />
      <div className="mt-3 flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto">
        {hits && hits.length === 0 && <Empty>Không tìm thấy đoạn nào khớp. Thử từ khoá khác hoặc mở rộng phạm vi.</Empty>}
        {hits?.map((h, i) => (
          <button
            key={`${h.document_id}-${h.page_number}-${i}`}
            onClick={() => onOpen(h.document_id, h.page_number)}
            className="rounded-[10px] border border-line p-3 text-left hover:border-accent"
          >
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded bg-mark px-1.5 py-0.5 font-semibold text-mark-ink">{h.source_label}</span>
              <span className="text-muted">{h.class_name}</span>
            </div>
            <p className="mt-1.5 whitespace-pre-wrap break-words text-sm">{h.snippet.replace(/^#{1,6}\s+/gm, "")}</p>
          </button>
        ))}
      </div>
    </Card>
  );
}

function AssistantChat({
  scope,
  selectedDoc,
  classes,
  onCite,
  tall,
  webEnabled,
  hasDocs,
}: {
  scope: Scope;
  selectedDoc?: SourceDoc & { class_id: string };
  classes: SourceClass[];
  onCite: (c: Citation) => void;
  tall: boolean;
  webEnabled: boolean;
  hasDocs: boolean;
}) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [task, setTask] = useState<AssistantTask>("ask");
  const [source, setSource] = useState<Source>(hasDocs || !webEnabled ? "docs" : "web");
  const web = source === "web" && webEnabled;
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState<Msg | null>(null);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<Msg[]>("/teacher/assistant/history")
      .then((rows) => setMsgs(rows.map((m) => ({ id: m.id, role: m.role, content: m.content, citations: m.citations }))))
      .catch(() => setMsgs([]));
  }, []);

  useEffect(() => {
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight });
  }, [msgs]);

  async function send(q: string, t: AssistantTask = task) {
    const question = q.trim();
    if (!question || busy) return;
    setBusy(true);
    setNotice(null);
    setInput("");
    const aid = `a-${Date.now()}`;
    setMsgs((m) => [
      ...m,
      { id: `u-${Date.now()}`, role: "user", content: question, citations: [] },
      { id: aid, role: "assistant", content: "", citations: [], streaming: true },
    ]);
    const patch = (fn: (m: Msg) => Msg) => setMsgs((all) => all.map((m) => (m.id === aid ? fn(m) : m)));
    try {
      const body = web ? { question, task: t, source: "web" } : { question, task: t, ...scope };
      await streamChat("/teacher/assistant/chat", body, (e) => {
        if (e.type === "start") {
          if (e.web_sources) patch((m) => ({ ...m, query: e.query, webSources: e.web_sources }));
          if (e.sources === 0)
            setNotice(
              web
                ? "Google không trả về kết quả phù hợp; thử diễn đạt chủ đề khác đi."
                : "Không tìm thấy đoạn tài liệu liên quan; câu trả lời có thể dựa trên kiến thức mở rộng.",
            );
          else if (e.truncated) setNotice("Tài liệu dài: AI chỉ đọc phần đầu tài liệu.");
        } else if (e.type === "delta") patch((m) => ({ ...m, content: m.content + e.text }));
        else if (e.type === "done") patch((m) => ({ ...m, citations: e.citations, streaming: false }));
        else if (e.type === "error") patch((m) => ({ ...m, content: m.content || e.message, streaming: false, error: true }));
      });
      patch((m) => ({ ...m, streaming: false }));
    } catch (err) {
      patch((m) => ({ ...m, content: (err as Error).message, streaming: false, error: true }));
    } finally {
      setBusy(false);
    }
  }

  function pickTask(t: (typeof TASKS)[number]) {
    setTask(t.id);
    const auto = web ? "" : t.prompt(selectedDoc?.file_name);
    if (auto && !input.trim()) send(auto, t.id);
  }

  async function clear() {
    if (!window.confirm("Xoá toàn bộ lịch sử trò chuyện với Trợ lý AI?")) return;
    await api("/teacher/assistant/history", { method: "DELETE" }).catch(() => {});
    setMsgs([]);
  }

  const current = TASKS.find((t) => t.id === task)!;

  return (
    <div className={cn("flex min-h-0 flex-col rounded-xl border border-line bg-surface p-4", tall ? "h-[620px] lg:h-full" : "h-[calc(100vh_-_330px)] min-h-[520px]")}>
      {webEnabled && (
        <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="font-semibold">Tổng hợp từ:</span>
          <div role="radiogroup" aria-label="Nguồn tài liệu" className="inline-flex rounded-full border border-line p-0.5">
            {[
              { id: "docs" as const, label: "Tài liệu lớp", icon: BookOpen },
              { id: "web" as const, label: "Google", icon: Globe },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                role="radio"
                aria-checked={source === id}
                disabled={busy}
                onClick={() => setSource(id)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-3 py-1 disabled:opacity-60",
                  source === id ? "bg-accent text-accent-ink" : "text-muted hover:text-ink",
                )}
              >
                <Icon size={14} /> {label}
              </button>
            ))}
          </div>
          <span className="text-xs text-muted">
            {web
              ? "AI tìm trên Google, đọc các trang đầu rồi tổng hợp kèm link nguồn. Nên kiểm tra lại trước khi dùng."
              : "Chỉ dùng tài liệu đã đăng trong các lớp."}
          </span>
        </div>
      )}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-line pb-3">
        {TASKS.map((t) => (
          <button
            key={t.id}
            onClick={() => pickTask(t)}
            disabled={busy}
            aria-pressed={task === t.id}
            className={cn(
              "rounded-full border px-3 py-1 text-sm disabled:opacity-60",
              task === t.id ? "border-accent bg-accent text-accent-ink" : "border-line text-muted hover:border-accent hover:text-accent",
            )}
          >
            {t.label}
          </button>
        ))}
        {msgs.length > 0 && (
          <Button variant="ghost" size="sm" className="ml-auto" onClick={clear} title="Xoá lịch sử">
            <Trash2 size={14} />
          </Button>
        )}
      </div>
      <div ref={boxRef} className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto py-3" aria-live="polite">
        {msgs.length === 0 && (
          <div className="max-w-[94%] self-start rounded-xl rounded-bl-sm bg-sunken px-3.5 py-2.5 text-sm">
            Chào cô/thầy. Mình tìm và tổng hợp nội dung từ tài liệu bài giảng của các lớp, kèm thẻ nguồn để bấm mở đúng trang.
            <br />
            Chọn một tài liệu ở trên rồi bấm <b>Tóm tắt</b>, <b>Đề cương ôn tập</b> hoặc <b>Câu hỏi ôn tập</b>; hoặc gõ chủ đề cần tìm.
            {webEnabled && (
              <>
                {" "}
                Muốn tìm thêm tài liệu trên mạng, chọn <b>Google</b>: mình tìm, đọc các trang đầu rồi tổng hợp kèm link nguồn.
              </>
            )}{" "}
            Bản tổng hợp có thể <b>lưu thành tài liệu lớp</b> để học sinh đọc.
          </div>
        )}
        {msgs.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="max-w-[88%] self-end whitespace-pre-wrap break-words rounded-xl rounded-br-sm bg-accent px-3.5 py-2.5 text-sm text-accent-ink">
              {m.content}
            </div>
          ) : (
            <div key={m.id} className={cn("max-w-[96%] self-start rounded-xl rounded-bl-sm bg-sunken px-3.5 py-2.5", m.error && "bg-bad-soft text-bad")}>
              {m.query && (
                <p className="mb-1.5 flex items-center gap-1.5 text-xs text-muted">
                  <Globe size={12} /> Đã tìm Google: “{m.query}” · {m.webSources?.length ?? 0} trang
                </p>
              )}
              {m.content ? (
                <Answer text={m.content} citations={m.citations} streaming={m.streaming} onCite={onCite} />
              ) : (
                <span className="inline-flex gap-1" aria-label="AI đang trả lời">
                  {[0, 1, 2].map((i) => (
                    <i key={i} className="size-1.5 animate-pulse rounded-full bg-muted" style={{ animationDelay: `${i * 150}ms` }} />
                  ))}
                </span>
              )}
              {!m.streaming && <WebSourceList citations={m.citations} />}
              {!m.streaming && !m.error && m.content && (
                <div className="mt-2 flex flex-wrap gap-1 border-t border-line pt-2">
                  <CopyButton text={m.content} />
                  <Button size="sm" variant="ghost" onClick={() => setSaving(m)}>
                    <Save size={13} /> Lưu thành tài liệu lớp
                  </Button>
                </div>
              )}
              {saving?.id === m.id && <SaveForm msg={m} classes={classes} defaultClass={selectedDoc?.class_id} onClose={() => setSaving(null)} />}
            </div>
          ),
        )}
      </div>
      {notice && <p className="pb-2 text-xs text-warn">{notice}</p>}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2 border-t border-line pt-3"
      >
        <textarea
          aria-label="Yêu cầu cho Trợ lý AI"
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          placeholder={`${current.label}: ${web ? WEB_HINT : current.hint}`}
          className="max-h-40 min-w-0 flex-1 resize-none rounded-[9px] border border-line bg-surface px-3 py-2 text-sm"
        />
        <button
          disabled={busy || !input.trim()}
          aria-label="Gửi"
          className="grid size-10 flex-none place-items-center self-end rounded-[9px] bg-accent text-accent-ink disabled:opacity-50"
        >
          <SendHorizontal size={17} />
        </button>
      </form>
    </div>
  );
}

function WebSourceList({ citations }: { citations: Citation[] }) {
  const web = citations.filter((c) => c.url);
  if (!web.length) return null;
  return (
    <div className="mt-2 border-t border-line pt-2 text-xs">
      <b>Nguồn tham khảo</b>
      <ol className="mt-1 flex list-decimal flex-col gap-0.5 pl-5">
        {web.map((c) => (
          <li key={c.label} className="break-words">
            <a href={c.url} target="_blank" rel="noreferrer noopener" className="text-accent underline">
              {c.title || c.url}
            </a>{" "}
            <span className="text-muted">({c.label})</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** Nội dung lưu thành tài liệu lớp: bỏ thẻ nguồn tài liệu, đổi nguồn web thành [1], [2]… kèm danh sách link cuối bài. */
function contentForSave(msg: Msg): string {
  const web = msg.citations.filter((c) => c.url);
  const num = new Map(web.map((c, i) => [c.label, i + 1]));
  let text = msg.content.replace(/\s*\[Nguồn:\s*([^\]]+?)\s*\]/g, (_, label: string) => (num.has(label) ? ` [${num.get(label)}]` : ""));
  if (web.length) text += `\n\n## Nguồn tham khảo\n${web.map((c, i) => `${i + 1}. ${c.title || c.url}: ${c.url}`).join("\n")}`;
  return text;
}

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <Button
      size="sm"
      variant="ghost"
      onClick={() =>
        navigator.clipboard
          ?.writeText(text)
          .then(() => {
            setDone(true);
            setTimeout(() => setDone(false), 1500);
          })
          .catch(() => {})
      }
    >
      <Copy size={13} /> {done ? "Đã chép" : "Sao chép"}
    </Button>
  );
}

function SaveForm({ msg, classes, defaultClass, onClose }: { msg: Msg; classes: SourceClass[]; defaultClass?: string; onClose: () => void }) {
  const firstHeading = msg.content.match(/^#{1,3}\s+(.+)$/m)?.[1]?.replace(/[*_`]/g, "").trim();
  const [classId, setClassId] = useState(defaultClass ?? classes[0]?.id ?? "");
  const [title, setTitle] = useState(firstHeading?.slice(0, 150) || "Tổng hợp từ Trợ lý AI");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      // Bỏ thẻ nguồn tài liệu (tài liệu mới tự có số trang riêng); nguồn web giữ lại thành danh sách link
      const content = contentForSave(msg);
      const d = await api<DocumentOut>("/teacher/assistant/save", { json: { class_id: classId, title, content } });
      setDone(`Đã lưu ${d.file_name}. Học sinh thấy tài liệu này ở trang lớp sau khi xử lý xong (vài giây).`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="mt-2 flex flex-col gap-2 rounded-lg border border-line bg-surface p-3 text-sm">
      <CardHeader title="Lưu thành tài liệu lớp">
        <Button type="button" variant="ghost" size="sm" aria-label="Đóng" onClick={onClose}>
          <X size={14} />
        </Button>
      </CardHeader>
      <Select aria-label="Lớp" value={classId} onChange={(e) => setClassId(e.target.value)}>
        {classes.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </Select>
      <Input aria-label="Tên tài liệu" maxLength={150} required value={title} onChange={(e) => setTitle(e.target.value)} />
      <ErrorText error={error} />
      {done ? (
        <p className="text-ok">{done}</p>
      ) : (
        <Button variant="primary" size="sm" disabled={busy || !classId}>
          <Save size={13} /> {busy ? "Đang lưu…" : "Lưu vào lớp"}
        </Button>
      )}
    </form>
  );
}
