"use client";

import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";

import { fetchObjectUrl } from "@/lib/api";

pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

/** Trình đọc PDF: cuộn tới đúng trang khi `page` đổi (bấm thẻ nguồn). Không render lớp chữ để nhẹ. */
export default function PdfViewer({ documentId, page, flashKey }: { documentId: string; page: number; flashKey: number }) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [width, setWidth] = useState(600);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let u: string | null = null;
    fetchObjectUrl(`/files/documents/${documentId}`)
      .then((x) => setUrl((u = x)))
      .catch((e) => setError((e as Error).message));
    return () => {
      if (u) URL.revokeObjectURL(u);
    };
  }, [documentId]);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setWidth(Math.max(260, el.clientWidth - 28)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Cuộn tới trang `page`. Trang PDF vẽ dần: mỗi khung trang giữ sẵn chiều cao khổ A4, và cuộn lại lần nữa khi
  // chính trang đích vẽ xong (onRenderSuccess) — nếu không, bấm thẻ nguồn "Trang 3" có thể dừng ở trang 1.
  function scrollToPage(smooth: boolean) {
    const target = wrapRef.current?.querySelector<HTMLElement>(`[data-page="${page}"]`);
    if (!target || !wrapRef.current) return null;
    wrapRef.current.scrollTo({ top: target.offsetTop - wrapRef.current.offsetTop - 8, behavior: smooth ? "smooth" : "auto" });
    return target;
  }

  useEffect(() => {
    if (!numPages) return;
    const target = scrollToPage(true);
    if (!target) return;
    if (flashKey === 0 && page === 1) return; // mới mở tài liệu: không đánh dấu
    target.classList.add("ring-4", "ring-mark");
    const t = setTimeout(() => target.classList.remove("ring-4", "ring-mark"), 1800);
    return () => clearTimeout(t);
  }, [page, numPages, flashKey]);

  return (
    <div ref={wrapRef} className="h-full overflow-y-auto rounded-xl bg-sunken p-3.5">
      {error && <p className="text-sm text-bad">{error}</p>}
      {url && (
        <Document
          file={url}
          onLoadSuccess={({ numPages }) => setNumPages(numPages)}
          onLoadError={() => setError("Không mở được PDF.")}
          loading={<p className="text-sm text-muted">Đang mở tài liệu…</p>}
        >
          <div className="flex flex-col gap-3.5">
            {Array.from({ length: numPages }, (_, i) => (
              <div key={i} data-page={i + 1} className="relative rounded-sm bg-white shadow transition-shadow"
                   style={{ minHeight: Math.round(width * 1.414) }}>
                <Page pageNumber={i + 1} width={width} renderTextLayer={false} renderAnnotationLayer={false}
                      onRenderSuccess={i + 1 === page ? () => scrollToPage(false) : undefined} />
                <span className="absolute bottom-1.5 right-3 font-mono text-[11px] text-neutral-500">Trang {i + 1}</span>
              </div>
            ))}
          </div>
        </Document>
      )}
    </div>
  );
}
