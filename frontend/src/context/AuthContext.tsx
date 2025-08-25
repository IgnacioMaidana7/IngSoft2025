"use client";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type AuthContextValue = {
  isLoggedIn: boolean;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    if (stored) setToken(stored);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (token) localStorage.setItem("auth_token", token);
    else localStorage.removeItem("auth_token");
  }, [token]);

  const login = useCallback(async () => {
    // Si ya guardaste tokens reales en localStorage desde la pantalla de login,
    // usa el access_token para marcar la sesión como activa.
    const access = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    setToken(access ?? "fake-token");
  }, []);

  const logout = useCallback(() => {
    // Limpiar todos los tokens y estado de sesión
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("auth_token");
    }
    setToken(null);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({ isLoggedIn: !!token, token, login, logout }), [token, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}


