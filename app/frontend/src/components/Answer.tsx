"use client";

import "katex/dist/katex.min.css";
import { FileText, Globe } from "lucide-react";
import ReactMarkdown, { defaultUrlTransform } from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";

import type { Citation } from "@/lib/types";

const CITE_RE = /\[Nguồn:\s*([^\]]+?)\s*\]/g;
const EXT_RE = /⚠️?\s*\[Kiến thức mở rộng ngoài bài giảng\]/g;

/** Câu trả lời AI: Markdown + công thức KaTeX + thẻ [Nguồn: …] bấm để nhảy đúng trang (hoặc mở trang web nguồn). */
export function Answer({
  text,
  citations,
  streaming,
  onCite,
}: {
  text: string;
  citations: Citation[];
  streaming?: boolean;
  onCite?: (c: Citation) => void;
}) {
  const byLabel = new Map(citations.map((c) => [c.label, c]));
  const md = text
    .replace(/\\\[(.+?)\\\]/gs, (_, m) => `$$${m}$$`)
    .replace(/\\\((.+?)\\\)/g, (_, m) => `$${m}$`)
    .replace(CITE_RE, (_, label: string) => ` [${label}](#cite:${encodeURIComponent(label)})`)
    .replace(EXT_RE, " [ext](#ext)");

  return (
    <div className="prose-answer min-w-0 break-words text-[0.93rem] leading-relaxed [&_.katex-display]:overflow-x-auto [&_.katex-display]:py-1 [&_li]:my-0.5 [&_ol]:list-decimal [&_ol]:pl-5 [&_p+p]:mt-2 [&_p]:my-1 [&_ul]:list-disc [&_ul]:pl-5">
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        urlTransform={(url) => (url.startsWith("#") ? url : defaultUrlTransform(url))}
        components={{
          a: ({ href, children }) => {
            if (href === "#ext") {
              return (
                <span className="mr-1 inline-block rounded bg-warn-soft px-1.5 py-px text-xs font-semibold text-warn">
                  ⚠️ Kiến thức mở rộng ngoài bài giảng
                </span>
              );
            }
            if (href?.startsWith("#cite:")) {
              const label = decodeURIComponent(href.slice(6));
              const c = byLabel.get(label);
              if (c?.url) {
                return (
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    title={c.title ? `${c.title}\n${c.url}` : c.url}
                    className="mx-0.5 inline-flex items-center gap-1 rounded-[5px] bg-mark px-1.5 py-px align-baseline text-xs font-semibold text-mark-ink no-underline hover:brightness-95"
                  >
                    <Globe size={11} /> {label}
                  </a>
                );
              }
              if (c && onCite) {
                return (
                  <button
                    type="button"
                    onClick={() => onCite(c)}
                    title={`Mở ${label}`}
                    className="mx-0.5 inline-flex items-center gap-1 rounded-[5px] bg-mark px-1.5 py-px align-baseline text-xs font-semibold text-mark-ink hover:brightness-95"
                  >
                    <FileText size={11} /> {label}
                  </button>
                );
              }
              // Đang stream hoặc nguồn không có thật trong tài liệu: hiện mờ, không bấm được
              return (
                <span
                  className="mx-0.5 inline-flex items-center gap-1 rounded-[5px] bg-sunken px-1.5 py-px text-xs text-muted"
                  title={streaming ? "Đang xác minh nguồn…" : "Nguồn không khớp tài liệu / kết quả tìm kiếm"}
                >
                  <FileText size={11} /> {label}
                </span>
              );
            }
            return (
              <a href={href} target="_blank" rel="noreferrer" className="text-accent underline">
                {children}
              </a>
            );
          },
        }}
      >
        {md}
      </ReactMarkdown>
      {streaming && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-muted align-middle" />}
    </div>
  );
}
