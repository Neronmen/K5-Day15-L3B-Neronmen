/** Dùng được ở server component (layout): không có "use client". */
export const THEME_KEY = "ms_theme";

/** Chạy trong <head> trước khi vẽ: lấy lựa chọn đã lưu, mặc định dark (bản chính). */
export const THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem("${THEME_KEY}");document.documentElement.dataset.theme=t==="light"?"light":"dark"}catch(e){document.documentElement.dataset.theme="dark"}})();`;
