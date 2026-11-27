"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { ChatPanel } from "@/components/ChatPanel";
import { TextPagesViewer } from "@/components/TextPagesViewer";
import { ErrorText, Loading, ModeLabel, PageHeader, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import type { Citation, DocPage, StudentDocument } from "@/lib/types";
import { useLoad } from "@/lib/useLoad";

const PdfViewer = dynamic(() => import("@/components/PdfViewer"), {
  ssr: false,
  loading: () => <div className="h-full rounded-xl bg-sunken p-4 text-sm text-muted">Đang mở tài liệu…</div>,
});

export default function Page() {
  return (
    <Suspense fallback={<Loading />}>
      <LecturePage />
    </Suspense>
  );
}

function LecturePage() {
  const { id } = useParams<{ id: string }>();
  const search = useSearchParams();
  const router = useRouter();
  const doc = useLoad<StudentDocument>(`/student/documents/${id}`);
  const [pages, setPages] = useState<DocPage[] | null>(null);
  const [page, setPage] = useState(() => Number(search.get("page")) || 1);
  const [flashKey, setFlashKey] = useState(0);

  useEffect(() => {
    if (doc.data && !doc.data.is_pdf) api<DocPage[]>(`/student/documents/${id}/pages`).then(setPages).catch(() => setPages([]));
  }, [doc.data, id]);

  function onCite(c: Citation) {
    if (c.document_id !== id) {
      router.push(`/student/documents/${c.document_id}?page=${c.page_number}`);
      return;
    }
    setPage(c.page_number);
    setFlashKey((k) => k + 1);
  }

  if (doc.error) return <ErrorText error={doc.error} />;
  if (!doc.data) return <Loading />;
  const d = doc.data;

  return (
    <>
      <PageHeader
        eyebrow={
          <Link href={`/student/classes/${d.class_id}`} className="hover:text-accent">
            ← {d.class_name}
          </Link>
        }
        title={d.file_name}
      >
        <ModeLabel mode={d.ai_mode} />
      </PageHeader>
      {/* grid-rows-1 = minmax(0,1fr): giữ 2 khung trong chiều cao màn hình, mỗi khung tự cuộn */}
      <div className="grid gap-4 lg:h-[calc(100vh_-_190px)] lg:min-h-[520px] lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] lg:grid-rows-1">
        <div className="h-[460px] min-w-0 lg:h-full">
          {d.is_pdf ? (
            <PdfViewer documentId={id} page={page} flashKey={flashKey} />
          ) : pages ? (
            <TextPagesViewer pages={pages} unit={d.unit} page={page} flashKey={flashKey} />
          ) : (
            <Loading />
          )}
        </div>
        <ChatPanel
          className="h-[560px] lg:h-full"
          title="Hỏi về bài giảng"
          badge={<Pill tone="info">{d.ai_mode === "strict" ? "Chỉ dùng tài liệu lớp" : "Ưu tiên tài liệu lớp"}</Pill>}
          intro={
            <>
              Mình trả lời dựa trên tài liệu giáo viên đăng cho lớp. Bấm vào thẻ{" "}
              <span className="rounded bg-mark px-1 text-xs font-semibold text-mark-ink">nguồn</span> để nhảy đến đúng trang.
            </>
          }
          historyPath={`/student/documents/${id}/chat`}
          postPath={`/student/documents/${id}/chat`}
          suggestions={["Tóm tắt ý chính của bài này", "Cho mình một ví dụ minh hoạ", "Phần nào hay bị nhầm?"]}
          placeholder="Hỏi về bài giảng… (Enter để gửi)"
          onCite={onCite}
        />
      </div>
    </>
  );
}
