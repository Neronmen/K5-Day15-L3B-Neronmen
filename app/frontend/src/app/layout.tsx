import type { Metadata } from "next";
import { Be_Vietnam_Pro, Lexend } from "next/font/google";

import { AuthProvider } from "@/lib/auth";
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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${body.variable} ${heading.variable}`}>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
