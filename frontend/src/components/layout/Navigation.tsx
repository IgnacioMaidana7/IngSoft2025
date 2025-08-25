"use client";
import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";

export default function Navigation() {
  const { isLoggedIn, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
  // replace evita que se pueda volver con el botón atrás
  router.replace("/login");
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-border/30 bg-white/80 backdrop-blur-xl supports-[backdrop-filter]:bg-white/70 shadow-lg shadow-black/5">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="inline-flex items-center gap-3 font-bold tracking-tight text-text hover:text-primary transition-colors duration-300 group">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center text-white shadow-lg shadow-primary/25 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-300">
              🏪
            </div>
            <span className="text-xl hidden sm:block">Sistema</span>
          </Link>
          
          {/* Show navigation only when logged in */}
          {isLoggedIn && (
            <>
              {/* Desktop Navigation */}
              <div className="hidden md:flex items-center gap-1">
                <Link href="/ventas" className="px-4 py-2 rounded-xl hover:bg-primary/10 hover:text-primary transition-all duration-300 text-sm font-medium flex items-center gap-2 group">
                  <span className="group-hover:scale-110 transition-transform duration-200">🛒</span>
                  Ventas
                </Link>
                <Link href="/productos" className="px-4 py-2 rounded-xl hover:bg-primary/10 hover:text-primary transition-all duration-300 text-sm font-medium flex items-center gap-2 group">
                  <span className="group-hover:scale-110 transition-transform duration-200">🏷️</span>
                  Productos
                </Link>
                <Link href="/inventario" className="px-4 py-2 rounded-xl hover:bg-primary/10 hover:text-primary transition-all duration-300 text-sm font-medium flex items-center gap-2 group">
                  <span className="group-hover:scale-110 transition-transform duration-200">📦</span>
                  Inventario
                </Link>
                <Link href="/ofertas" className="px-4 py-2 rounded-xl hover:bg-primary/10 hover:text-primary transition-all duration-300 text-sm font-medium flex items-center gap-2 group">
                  <span className="group-hover:scale-110 transition-transform duration-200">🎁</span>
                  Ofertas
                </Link>
                <Link href="/empleados" className="px-4 py-2 rounded-xl hover:bg-primary/10 hover:text-primary transition-all duration-300 text-sm font-medium flex items-center gap-2 group">
                  <span className="group-hover:scale-110 transition-transform duration-200">👥</span>
                  Empleados
                </Link>
              </div>

              {/* Right Section */}
              <div className="flex items-center gap-3">
                {/* Camera Button */}
                <Link href="/camera" className="p-2 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary transition-all duration-300 hover:scale-110 active:scale-95">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </Link>

                {/* Logout Button */}
                <button 
                  onClick={handleLogout}
                  className="p-2 rounded-xl bg-red-100 hover:bg-red-200 text-red-600 transition-all duration-300 hover:scale-110 active:scale-95"
                  title="Cerrar sesión"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>

                {/* Mobile Menu Button */}
                <button className="md:hidden p-2 rounded-xl hover:bg-primary/10 text-text transition-all duration-300">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}