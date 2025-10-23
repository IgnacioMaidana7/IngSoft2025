"use client";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const { isLoggedIn } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoggedIn) {
      router.replace("/login");
    } else {
      // Verificar tipo de usuario y redirigir según el rol
      const userType = localStorage.getItem('user_type');
      const userRole = localStorage.getItem('user_role');
      
      if (userType === 'empleado') {
        // Redirigir a dashboard específico según el rol del empleado
        if (userRole === 'CAJERO') {
          router.replace('/empleado/cajero/dashboard');
        } else if (userRole === 'REPONEDOR') {
          router.replace('/empleado/reponedor/dashboard');
        } else {
          // Fallback al dashboard genérico de empleados
          router.replace('/empleado/dashboard');
        }
      } else {
        // Usuario administrador
        router.replace("/dashboard");
      }
    }
  }, [isLoggedIn, router]);

  return null; // No renderizar nada, solo redirigir
}
