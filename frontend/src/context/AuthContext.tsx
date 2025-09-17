"use client";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type AuthContextValue = {
  isLoggedIn: boolean;
  token: string | null;
  login: (email?: string, password?: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Verificar primero access_token (JWT), luego auth_token (token de sesión)
    const access = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    const auth = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    
    if (access) {
      setToken(access);
    } else if (auth && auth !== "fake-token") {
      setToken(auth);
    }
    
    // Marcar como completada la carga inicial
    setIsLoading(false);
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
    
    setIsLoading(true);
    
    // Priorizar access_token (JWT) sobre auth_token
    const access = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    
    if (access) {
      setToken(access);
    } else {
      // Si no hay token real, el usuario no está autenticado
      console.log("No hay token disponible, usuario no autenticado");
      setToken(null);
    }
    
    setIsLoading(false);
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

  const value = useMemo<AuthContextValue>(() => ({ 
    isLoggedIn: !!token, 
    token, 
    login, 
    logout, 
    isLoading 
  }), [token, login, logout, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}


