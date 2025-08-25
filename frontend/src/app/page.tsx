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
      router.replace("/dashboard");
    }
  }, [isLoggedIn, router]);

  return null; // No renderizar nada, solo redirigir
}
