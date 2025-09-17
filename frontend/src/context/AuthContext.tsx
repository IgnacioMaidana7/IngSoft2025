"use client";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type AuthContextValue = {
  isLoggedIn: boolean;
  token: string | null;
  login: (email?: string, password?: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Verificar primero access_token (JWT), luego auth_token (token de sesión)
    const access = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    const auth = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    
    if (access) {
      setToken(access);
    } else if (auth && auth !== "fake-token") {
      setToken(auth);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (token) localStorage.setItem("auth_token", token);
    else localStorage.removeItem("auth_token");
  }, [token]);

  const login = useCallback(async (_email?: string, _password?: string) => {
    // Referenciar argumentos para evitar advertencias de no-usados en lint/ts
    void _email;
    void _password;
    
    // Priorizar access_token (JWT) sobre auth_token
    const access = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    
    if (access) {
      setToken(access);
    } else {
      // Solo usar fake-token como último recurso para testing
      console.warn("No hay token real disponible, usando token de prueba");
      setToken("fake-token");
    }
  }, []);

  const logout = useCallback(() => {
    // Limpiar todos los tokens y estado de sesión
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user_type");
      localStorage.removeItem("user_role");
      localStorage.removeItem("empleado_info");
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


