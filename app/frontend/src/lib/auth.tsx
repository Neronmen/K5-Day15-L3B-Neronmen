"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api, ApiError, getToken, setToken } from "./api";
import type { Role, TokenOut, User } from "./types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (data: { email: string; password: string; name: string; role: Role }) => Promise<User>;
  loginWithGoogle: (credential: string, role?: Role) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function homeFor(role: Role) {
  return role === "teacher" ? "/teacher" : "/student";
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api<User>("/auth/me")
      .then(setUser)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) setToken(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const r = await api<TokenOut>("/auth/login", { json: { email, password } });
    setToken(r.access_token);
    setUser(r.user);
    return r.user;
  }, []);

  const register = useCallback(async (data: { email: string; password: string; name: string; role: Role }) => {
    const r = await api<TokenOut>("/auth/register", { json: data });
    setToken(r.access_token);
    setUser(r.user);
    return r.user;
  }, []);

  const loginWithGoogle = useCallback(async (credential: string, role?: Role) => {
    const r = await api<TokenOut>("/auth/google", { json: { credential, role: role ?? null } });
    setToken(r.access_token);
    setUser(r.user);
    return r.user;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, loading, login, register, loginWithGoogle, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth phải nằm trong AuthProvider");
  return ctx;
}

/** Chặn trang theo vai trò ở phía giao diện. Quyền thật vẫn kiểm tra ở backend. */
export function RequireRole({ role, children }: { role: Role; children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) router.replace("/login");
    else if (user.role !== role) router.replace(homeFor(user.role));
  }, [user, loading, role, router]);

  if (loading || !user || user.role !== role) {
    return <div className="grid min-h-[60vh] place-items-center text-muted">Đang tải…</div>;
  }
  return <>{children}</>;
}
