"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AuthCard } from "@/components/AuthCard";
import { GoogleButton } from "@/components/GoogleButton";
import { Button, ErrorText, Field, Input } from "@/components/ui";
import { homeFor, useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { user, loading, login, loginWithGoogle } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace(homeFor(user.role));
  }, [user, loading, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const u = await login(email, password);
      router.replace(homeFor(u.role));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Đăng nhập" sub="Dành cho giáo viên và học sinh.">
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <Field label="Email" htmlFor="email">
          <Input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>
        <Field label="Mật khẩu" htmlFor="password">
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <ErrorText error={error} />
        <Button variant="primary" disabled={busy}>
          {busy ? "Đang đăng nhập…" : "Đăng nhập"}
        </Button>
        <GoogleButton
          text="signin_with"
          onCredential={async (c) => {
            setError(null);
            try {
              const u = await loginWithGoogle(c, undefined);
              router.replace(homeFor(u.role));
            } catch (err) {
              setError((err as Error).message);
            }
          }}
        />
        <p className="text-center text-sm text-muted">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="font-semibold text-accent">
            Đăng ký
          </Link>
        </p>
      </form>
    </AuthCard>
  );
}
