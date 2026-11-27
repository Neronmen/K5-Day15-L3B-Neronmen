"use client";

import { useCallback, useEffect, useState } from "react";

import { THEME_KEY } from "./theme-script";

export type Theme = "dark" | "light";
const EVENT = "ms-theme";

const current = (): Theme => (document.documentElement.dataset.theme === "light" ? "light" : "dark");

/** Theme hiện tại + hàm đổi. Mọi nút đổi theme trên trang cùng cập nhật (qua sự kiện "ms-theme"). */
export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    setTheme(current());
    const sync = () => setTheme(current());
    window.addEventListener(EVENT, sync);
    return () => window.removeEventListener(EVENT, sync);
  }, []);

  const toggle = useCallback(() => {
    const next: Theme = current() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* không có storage: chỉ đổi trong phiên này */
    }
    window.dispatchEvent(new Event(EVENT));
  }, []);

  return [theme, toggle];
}
