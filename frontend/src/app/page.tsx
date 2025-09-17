"use client";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const { isLoggedIn, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // No redirigir hasta que termine de cargar el contexto de autenticación
    if (isLoading) return;
    
    if (!isLoggedIn) {
      router.replace("/login");
    } else {
      router.replace("/dashboard");
    }
  }, [isLoggedIn, isLoading, router]);

  // Mostrar un spinner mientras se verifica la autenticación
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-lightText">Verificando autenticación...</p>
        </div>
      </div>
    );
  }

  return null; // No renderizar nada, solo redirigir
}
