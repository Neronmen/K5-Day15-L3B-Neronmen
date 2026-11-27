import type { Metadata, Viewport } from "next";
import { Be_Vietnam_Pro, Lexend } from "next/font/google";

import { AuthProvider } from "@/lib/auth";
import { THEME_INIT_SCRIPT } from "@/lib/theme-script";
import "./globals.css";

const body = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});
const heading = Lexend({
  subsets: ["latin", "vietnamese"],
  weight: ["500", "600", "700"],
  variable: "--font-heading",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MinutesStudy",
  description: "Nơi giáo viên đăng bài giảng, giao bài tập và học sinh học cùng trợ lý AI.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0d1311" },
    { media: "(prefers-color-scheme: light)", color: "#f4f2eb" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" data-theme="dark" className={`${body.variable} ${heading.variable}`} suppressHydrationWarning>
      <head>
        {/* Đặt theme trước khi vẽ trang để không nháy sáng → tối */}
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
