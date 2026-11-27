"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthCard } from "@/components/AuthCard";
import { GoogleButton } from "@/components/GoogleButton";
import { Button, ErrorText, Field, Input } from "@/components/ui";
import { homeFor, useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

export default function RegisterPage() {
  const { register, loginWithGoogle } = useAuth();
  const router = useRouter();
  const [role, setRole] = useState<Role>("student");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) {
      setError("Mật khẩu cần ít nhất 8 ký tự.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const u = await register({ email, password, name, role });
      router.replace(homeFor(u.role));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Tạo tài khoản" sub="Học sinh được giáo viên thêm vào lớp: đăng ký bằng đúng email đó để thấy lớp ngay.">
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Vai trò">
          {(["student", "teacher"] as const).map((r) => (
            <label
              key={r}
              className="flex cursor-pointer items-center gap-2 rounded-[10px] border border-line p-3 has-[:checked]:border-accent has-[:checked]:bg-accent-soft"
            >
              <input type="radio" name="role" value={r} checked={role === r} onChange={() => setRole(r)} className="accent-accent" />
              <span className="font-semibold">{r === "student" ? "Học sinh" : "Giáo viên"}</span>
            </label>
          ))}
        </div>
        <Field label="Họ tên" htmlFor="name">
          <Input id="name" required autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label="Email" htmlFor="email">
          <Input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>
        <Field label="Mật khẩu" htmlFor="password" hint="(ít nhất 8 ký tự)">
          <Input
            id="password"
            type="password"
            required
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <ErrorText error={error} />
        <Button variant="primary" disabled={busy}>
          {busy ? "Đang tạo…" : "Tạo tài khoản"}
        </Button>
        <GoogleButton
          text="signup_with"
          onCredential={async (c) => {
            setError(null);
            try {
              const u = await loginWithGoogle(c, role);
              router.replace(homeFor(u.role));
            } catch (err) {
              setError((err as Error).message);
            }
          }}
        />
        <p className="text-center text-sm text-muted">
          Đã có tài khoản?{" "}
          <Link href="/login" className="font-semibold text-accent">
            Đăng nhập
          </Link>
        </p>
      </form>
    </AuthCard>
  );
}
