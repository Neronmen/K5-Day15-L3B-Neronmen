import { API_URL, ApiError, getToken } from "./api";
import type { Citation, WebSource } from "./types";

export type ChatEvent =
  | { type: "start"; mode: "lecture" | "hint" | "answer" | "teacher"; route: string; remaining_today?: number; sources?: number; truncated?: boolean; web_sources?: WebSource[]; query?: string }
  | { type: "delta"; text: string }
  | { type: "done"; citations: Citation[]; mode: string; route: string }
  | { type: "error"; message: string };

/** POST + đọc stream SSE (EventSource không gửi được header Authorization). */
export async function streamChat(
  path: string,
  question: string | Record<string, unknown>,
  onEvent: (e: ChatEvent) => void,
  signal?: AbortSignal,
) {
  const payload = typeof question === "string" ? { question } : question;
  const token = getToken();
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(payload),
      signal,
    });
  } catch {
    throw new ApiError(0, "Không kết nối được máy chủ.");
  }
  if (!res.ok || !res.body) {
    const data = await res.json().catch(() => null);
    throw new ApiError(res.status, (data && typeof data.detail === "string" && data.detail) || `Lỗi ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const block = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      for (const line of block.split("\n")) {
        if (line.startsWith("data: ")) {
          try {
            onEvent(JSON.parse(line.slice(6)) as ChatEvent);
          } catch {
            /* bỏ qua dòng hỏng */
          }
        }
      }
    }
  }
}
