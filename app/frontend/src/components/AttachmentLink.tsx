"use client";

import { useState } from "react";
import { Paperclip } from "lucide-react";

import { fetchObjectUrl } from "@/lib/api";

/** Nút tải file đề bài tập (cần đăng nhập nên tải qua fetch rồi mở bằng URL tạm). */
export function AttachmentLink({ assignmentId, name }: { assignmentId: string; name: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function open() {
    setBusy(true);
    setError(null);
    try {
      const url = await fetchObjectUrl(`/files/assignments/${assignmentId}/attachment`);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="inline-flex flex-col gap-1">
      <button
        type="button"
        onClick={open}
        disabled={busy}
        className="inline-flex max-w-full items-center gap-2 rounded-[9px] border border-line bg-surface px-3 py-2 text-left text-sm font-medium hover:border-accent hover:text-accent disabled:opacity-60"
      >
        <Paperclip size={15} className="flex-none" />
        <span className="min-w-0 break-all">{busy ? "Đang tải…" : name}</span>
      </button>
      {error && <span className="text-xs text-bad">{error}</span>}
    </span>
  );
}
