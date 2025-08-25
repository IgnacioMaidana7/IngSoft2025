"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import Card from "@/components/layout/Card";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { loginSupermercado } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoggedIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Si ya hay sesión activa, no permitir ver el login ni volver con atrás
  useEffect(() => {
    if (isLoggedIn) {
      router.replace("/dashboard");
    }
  }, [isLoggedIn, router]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    
    setLoading(true);
    setError("");
    
    try {
      const response = await loginSupermercado({ email, password });
      
      // Guardar tokens en localStorage
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      
      // Actualizar contexto de autenticación
      await login();
      
      // replace evita que el historial permita volver al login
      router.replace("/dashboard");
    } catch (error: unknown) {
      console.error('Error en login:', error);
      const errorMessage = error instanceof Error ? error.message : 'Error al iniciar sesión. Verifica tus credenciales.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Left side - Branding */}
      <div className="lg:flex-1 bg-gradient-to-br from-primary/20 via-primary/10 to-primary/5 flex items-center justify-center p-8 lg:p-16">
        <div className="max-w-md text-center">
          <div className="inline-block p-6 bg-gradient-to-br from-primary/30 to-primary/20 rounded-3xl mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-primary to-primary/80 rounded-2xl flex items-center justify-center text-4xl text-white shadow-2xl shadow-primary/40">
              🏪
            </div>
          </div>
          <h2 className="text-3xl lg:text-4xl font-bold text-text mb-6">
            Sistema de Gestión
          </h2>
          <p className="text-lg text-lightText leading-relaxed">
            Controla tu inventario, productos y ventas desde una plataforma moderna y eficiente
          </p>
          
          {/* Features */}
          <div className="mt-8 space-y-3">
            <div className="flex items-center gap-3 text-lightText">
              <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center">
                <svg className="w-3 h-3 text-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
              </div>
              <span>Gestión de inventario en tiempo real</span>
            </div>
            <div className="flex items-center gap-3 text-lightText">
              <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center">
                <svg className="w-3 h-3 text-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
              </div>
              <span>Funciona offline</span>
            </div>
            <div className="flex items-center gap-3 text-lightText">
              <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center">
                <svg className="w-3 h-3 text-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
              </div>
              <span>Escáner de códigos integrado</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Login Form */}
      <div className="lg:flex-1 flex items-center justify-center p-8 lg:p-16">
        <div className="w-full max-w-md">
          <Card variant="elevated" className="animate-[fadeInUp_0.8s_ease-out]">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-text mb-2">
                Iniciar Sesión
              </h1>
              <p className="text-lightText">
                Accede a tu cuenta para continuar
              </p>
            </div>
            
            {error && (
              <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                {error}
              </div>
            )}
            
            <form onSubmit={onSubmit} className="space-y-6">
              <Input 
                label="Correo electrónico" 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                placeholder="tu@correo.com"
                icon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                  </svg>
                }
              />
              
              <Input 
                label="Contraseña" 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                placeholder="••••••••"
                icon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                }
              />
              
              <Button 
                className="w-full" 
                type="submit" 
                size="lg"
                loading={loading}
                disabled={!email || !password}
              >
                Iniciar Sesión
              </Button>
              
              <div className="text-center space-y-4">
                <Link 
                  href="/register" 
                  className="text-primary font-semibold hover:text-primary/80 transition-colors"
                >
                  ¿No tienes cuenta? Regístrate
                </Link>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}