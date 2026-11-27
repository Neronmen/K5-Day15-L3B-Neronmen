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

  useEffect(() => {
    if (!numPages) return;
    const target = wrapRef.current?.querySelector<HTMLElement>(`[data-page="${page}"]`);
    if (!target || !wrapRef.current) return;
    wrapRef.current.scrollTo({ top: target.offsetTop - wrapRef.current.offsetTop - 8, behavior: "smooth" });
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
              <div key={i} data-page={i + 1} className="relative rounded-sm bg-white shadow transition-shadow">
                <Page pageNumber={i + 1} width={width} renderTextLayer={false} renderAnnotationLayer={false} />
                <span className="absolute bottom-1.5 right-3 font-mono text-[11px] text-neutral-500">Trang {i + 1}</span>
              </div>
            ))}
          </div>
        </Document>
      )}
    </div>
  );
}
