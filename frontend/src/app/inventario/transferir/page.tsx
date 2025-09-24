"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TransferSetupPage() {
  const router = useRouter();

  useEffect(() => {
    // Redireccionar a la nueva página de transferencias
    router.replace("/inventario/transferencias/nueva");
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-lightText">Redirigiendo...</p>
      </div>
    </div>
  );
}


