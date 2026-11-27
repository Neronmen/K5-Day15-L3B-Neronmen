"use client";

import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";

type GoogleId = {
  accounts: {
    id: {
      initialize: (o: { client_id: string; callback: (r: { credential: string }) => void; ux_mode?: string }) => void;
      renderButton: (el: HTMLElement, o: Record<string, unknown>) => void;
    };
  };
};

let scriptPromise: Promise<void> | null = null;
function loadScript(): Promise<void> {
  scriptPromise ??= new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "https://accounts.google.com/gsi/client";
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Không tải được Google"));
    document.head.appendChild(s);
  });
  return scriptPromise;
}

/** Nút "Đăng nhập với Google". Không hiện gì nếu backend chưa cấu hình GOOGLE_CLIENT_ID. */
export function GoogleButton({ text, onCredential }: { text: "signin_with" | "signup_with"; onCredential: (c: string) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const cb = useRef(onCredential);
  cb.current = onCredential;
  const [clientId, setClientId] = useState<string | null>(null);

  useEffect(() => {
    api<{ google_client_id: string | null }>("/auth/config")
      .then((c) => setClientId(c.google_client_id))
      .catch(() => setClientId(null));
  }, []);

  useEffect(() => {
    if (!clientId) return;
    loadScript()
      .then(() => {
        const g = (window as unknown as { google?: GoogleId }).google;
        if (!g || !ref.current) return;
        g.accounts.id.initialize({ client_id: clientId, callback: (r) => cb.current(r.credential) });
        g.accounts.id.renderButton(ref.current, {
          text,
          theme: "outline",
          size: "large",
          shape: "rectangular",
          locale: "vi",
          width: Math.min(ref.current.clientWidth || 360, 400),
        });
      })
      .catch(() => {});
  }, [clientId, text]);

  if (!clientId) return null;
  return (
    <>
      <div className="flex items-center gap-3 text-xs text-muted">
        <span className="h-px flex-1 bg-line" /> hoặc <span className="h-px flex-1 bg-line" />
      </div>
      <div ref={ref} className="flex min-h-11 w-full justify-center" />
    </>
  );
}
