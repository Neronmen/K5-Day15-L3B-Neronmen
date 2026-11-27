// Ngày giờ lịch học. Backend tính theo giờ Việt Nam; trình duyệt người dùng cũng ở VN nên dùng giờ máy.

export const WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];
export const WEEKDAYS_SHORT = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

const pad = (n: number) => String(n).padStart(2, "0");

/** Date → "YYYY-MM-DD" theo giờ máy. */
export function ymd(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** "YYYY-MM-DD" → Date 00:00 giờ máy. */
export function parseYmd(s: string): Date {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function addDays(d: Date, n: number): Date {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

/** Thứ theo kiểu Việt Nam: 0 = Thứ 2 … 6 = Chủ nhật. */
export function vnWeekday(d: Date): number {
  return (d.getDay() + 6) % 7;
}

export function mondayOf(d: Date): Date {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  return addDays(x, -vnWeekday(x));
}

/** "Thứ 5, 27/11" */
export function fmtDay(s: string | Date): string {
  const d = typeof s === "string" ? parseYmd(s) : s;
  return `${WEEKDAYS[vnWeekday(d)]}, ${pad(d.getDate())}/${pad(d.getMonth() + 1)}`;
}

/** "Thứ 3 18:00" hoặc "Hôm nay 18:00" cho buổi học sắp tới. */
export function fmtNextSession(iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  const time = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  const today = ymd(new Date());
  if (ymd(d) === today) return `Hôm nay ${time}`;
  if (ymd(d) === ymd(addDays(new Date(), 1))) return `Ngày mai ${time}`;
  return `${fmtDay(d)} ${time}`;
}
