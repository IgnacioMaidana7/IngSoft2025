"use client";
import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

type Toast = { id: number; message: string; type?: "success" | "error" | "info" };

type ToastContextValue = {
  showToast: (message: string, type?: Toast["type"]) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counterRef = useRef(0);

  const showToast = useCallback((message: string, type: Toast["type"] = "success") => {
    // Generate a unique ID using counter + timestamp to prevent duplicates
    const id = Date.now() + (counterRef.current++);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 2500);
  }, []);

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed top-4 right-4 grid gap-2 z-[1000]">
        {toasts.map((t) => {
          const base = "px-3.5 py-2.5 rounded-[10px] text-white font-semibold shadow-[0_6px_18px_rgba(0,0,0,0.12)]";
          const variant =
            t.type === "error" ? "bg-red-600" : t.type === "info" ? "bg-sky-500" : "bg-green-600";
          return (
            <div key={t.id} className={[base, variant, "animate-slide-in-right"].join(" ")}>{t.message}</div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}


