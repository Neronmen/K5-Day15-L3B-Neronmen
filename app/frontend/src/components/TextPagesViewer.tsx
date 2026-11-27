"use client";

import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

import type { DocPage } from "@/lib/types";

/** Trình đọc cho Word/Slide/Markdown: hiển thị văn bản đã bóc tách theo từng trang/slide/phần. */
export function TextPagesViewer({ pages, unit, page, flashKey }: { pages: DocPage[]; unit: string; page: number; flashKey: number }) {
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const target = wrapRef.current?.querySelector<HTMLElement>(`[data-page="${page}"]`);
    if (!target || !wrapRef.current) return;
    wrapRef.current.scrollTo({ top: target.offsetTop - wrapRef.current.offsetTop - 8, behavior: "smooth" });
    if (flashKey === 0 && page === 1) return; // mới mở tài liệu: không đánh dấu
    target.classList.add("ring-4", "ring-mark");
    const t = setTimeout(() => target.classList.remove("ring-4", "ring-mark"), 1800);
    return () => clearTimeout(t);
  }, [page, flashKey, pages.length]);

  return (
    <div ref={wrapRef} className="flex h-full flex-col gap-3.5 overflow-y-auto rounded-xl bg-sunken p-3.5">
      {pages.map((p) => (
        <section key={p.page_number} data-page={p.page_number} className="relative rounded bg-surface px-6 pb-9 pt-5 shadow-card transition-shadow">
          <div className="break-words text-[0.92rem] leading-relaxed [&_h1]:mb-2 [&_h1]:text-lg [&_h1]:font-semibold [&_h2]:mb-2 [&_h2]:text-base [&_h2]:font-semibold [&_h3]:font-semibold [&_li]:my-0.5 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-1.5 [&_ul]:list-disc [&_ul]:pl-5">
            {/* Giữ xuống dòng của văn bản gốc (công thức mỗi dòng một ý) */}
            <ReactMarkdown>{p.text.replace(/([^\n])\n(?!\n)/g, "$1  \n")}</ReactMarkdown>
          </div>
          <span className="absolute bottom-2 right-3.5 font-mono text-[11px] text-muted">
            {unit} {p.page_number}/{pages.length}
          </span>
        </section>
      ))}
    </div>
  );
}
