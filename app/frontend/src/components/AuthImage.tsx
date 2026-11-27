"use client";

import { useEffect, useState } from "react";

import { fetchObjectUrl } from "@/lib/api";

/** Ảnh cần đăng nhập mới xem được (ảnh bài nộp). */
export function AuthImage({ path, alt }: { path: string; alt: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let url: string | null = null;
    let alive = true;
    fetchObjectUrl(path)
      .then((u) => {
        url = u;
        if (alive) setSrc(u);
        else URL.revokeObjectURL(u);
      })
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [path]);

  if (failed) return <p className="text-sm text-bad">Không tải được ảnh.</p>;
  if (!src) return <div className="h-40 animate-pulse rounded-lg bg-sunken" />;
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt={alt} className="max-h-[520px] w-auto max-w-full rounded-lg border border-line" />;
}
