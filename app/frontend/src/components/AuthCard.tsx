import { BookMarked, Clock3, Quote } from "lucide-react";

import { Logo, ThemeToggle, Wordmark } from "./ui";

const POINTS = [
  { icon: Clock3, title: "Còn hạn thì gợi ý, hết hạn mới giải", text: "Gia sư AI chỉ ra bước sai đầu tiên, không làm hộ." },
  { icon: BookMarked, title: "Bám đúng bài giảng của thầy cô", text: "Mỗi ý đều có thẻ nguồn nhảy tới đúng trang." },
  { icon: Quote, title: "Giáo viên thấy em đang vướng ở đâu", text: "Lịch sử hỏi đáp và tin bất thường được gắn cờ." },
];

export function AuthCard({ title, sub, children }: { title: string; sub: string; children: React.ReactNode }) {
  return (
    <main className="grid min-h-screen lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
      {/* Bảng phấn giới thiệu — chỉ hiện trên màn rộng */}
      <section className="relative hidden overflow-hidden border-r border-line bg-surface lg:flex lg:flex-col">
        <div className="chalkboard pointer-events-none absolute inset-0" />
        <div className="relative flex flex-1 flex-col px-14 py-12">
          <div className="flex items-center gap-2.5 text-xl">
            <Logo size={36} />
            <Wordmark />
          </div>
          <div className="my-auto max-w-[460px] py-12">
            <p className="mb-4 text-xs font-semibold uppercase tracking-[0.16em] text-accent">Học từng phút, hiểu từng bước</p>
            <h2 className="text-[2.35rem] font-semibold leading-[1.15]">
              Lớp học của thầy cô, <span className="chalk-underline pb-1">trợ lý</span> của riêng em.
            </h2>
            <ul className="mt-10 flex flex-col gap-6">
              {POINTS.map(({ icon: Icon, title: t, text }) => (
                <li key={t} className="flex gap-4">
                  <span className="grid size-10 flex-none place-items-center rounded-xl border border-line-strong bg-sunken text-accent">
                    <Icon size={18} />
                  </span>
                  <div>
                    <div className="font-semibold">{t}</div>
                    <div className="text-sm text-muted">{text}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <p className="text-xs text-faint">Dành cho giáo viên và học sinh THPT.</p>
        </div>
      </section>

      {/* Form */}
      <section className="relative flex flex-col px-5 py-8 sm:px-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-lg lg:invisible">
            <Logo size={30} />
            <Wordmark />
          </div>
          <ThemeToggle withLabel />
        </div>
        <div className="my-auto w-full max-w-[400px] animate-rise self-center py-10">
          <h1 className="text-[1.75rem] font-semibold">{title}</h1>
          <p className="mb-7 mt-1.5 text-sm text-muted">{sub}</p>
          {children}
        </div>
      </section>
    </main>
  );
}
