"use client";
import React from "react";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import HomeButton from "@/components/common/HomeButton";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";

export default function DashboardPage() {
  return (
    <ProtectedRoute>
    <Container size="xl" className="min-h-[calc(100vh-200px)]">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="inline-block p-4 bg-gradient-to-br from-primary/20 to-primary/10 rounded-3xl mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-primary to-primary/80 rounded-2xl flex items-center justify-center text-3xl text-white shadow-xl shadow-primary/30">
            🏪
          </div>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-text mb-4 tracking-tight">
          Bienvenido al Sistema
        </h1>
        <p className="text-xl text-lightText max-w-2xl mx-auto leading-relaxed">
          Gestiona tu inventario, productos y ventas desde un solo lugar
        </p>
      </div>

      <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Navigation */}
        <div className="lg:col-span-2">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-text mb-4 flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary/80 rounded-lg flex items-center justify-center text-white text-sm">
                🚀
              </div>
              Módulos Principales
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <HomeButton 
              title="Ventas" 
              icon="🛒" 
              href="/ventas"
              description="Procesar ventas y cobros"
            />
            <HomeButton 
              title="Inventario" 
              icon="📦" 
              href="/inventario"
              description="Control de stock y depósitos"
            />
            <HomeButton 
              title="Productos" 
              icon="🏷️" 
              href="/productos"
              description="Catálogo y precios"
            />
            <HomeButton 
              title="Ofertas" 
              icon="🎁" 
              href="/ofertas"
              description="Promociones especiales"
            />
            <HomeButton 
              title="Empleados" 
              icon="👥" 
              href="/empleados"
              description="Gestión de personal"
            />
            <HomeButton 
              title="Cámara" 
              icon="📸" 
              href="/camera"
              description="Escanear códigos y productos"
            />
          </div>
        </div>

        {/* Sidebar */}
        <aside className="space-y-6">
          <Card variant="elevated" padding="lg">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white text-sm">
                ⚡
              </div>
              <h3 className="text-lg font-bold text-text">Acciones Rápidas</h3>
            </div>
            <div className="space-y-3">
              <button className="w-full p-3 bg-primary/10 hover:bg-primary/20 rounded-xl text-left transition-all duration-300 hover:scale-[1.02] group">
                <div className="flex items-center gap-3">
                  <span className="text-lg">📸</span>
                  <div>
                    <div className="font-semibold text-text group-hover:text-primary transition-colors">Escanear Producto</div>
                    <div className="text-sm text-lightText">Usar cámara</div>
                  </div>
                </div>
              </button>
              
              <button className="w-full p-3 bg-primary/10 hover:bg-primary/20 rounded-xl text-left transition-all duration-300 hover:scale-[1.02] group">
                <div className="flex items-center gap-3">
                  <span className="text-lg">📝</span>
                  <div>
                    <div className="font-semibold text-text group-hover:text-primary transition-colors">Nueva Venta</div>
                    <div className="text-sm text-lightText">Procesar venta rápida</div>
                  </div>
                </div>
              </button>
              
              <button className="w-full p-3 bg-primary/10 hover:bg-primary/20 rounded-xl text-left transition-all duration-300 hover:scale-[1.02] group">
                <div className="flex items-center gap-3">
                  <span className="text-lg">🎁</span>
                  <div>
                    <div className="font-semibold text-text group-hover:text-primary transition-colors">Crear Oferta</div>
                    <div className="text-sm text-lightText">Promoción especial</div>
                  </div>
                </div>
              </button>
            </div>
          </Card>

          <Card variant="gradient" padding="lg">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center text-white text-sm">
                💡
              </div>
              <h3 className="text-lg font-bold text-text">Consejos</h3>
            </div>
            <div className="space-y-3 text-sm text-lightText">
              <div className="p-3 bg-white/50 rounded-xl">
                <div className="font-medium text-text mb-1">⌨️ Navegación rápida</div>
                Usa <kbd className="px-2 py-1 bg-primary/20 rounded-md text-primary font-mono text-xs">Ctrl+K</kbd> para buscar
              </div>
              <div className="p-3 bg-white/50 rounded-xl">
                <div className="font-medium text-text mb-1">📱 Funciona offline</div>
                La app funciona sin conexión a internet
              </div>
            </div>
          </Card>

          {/* Status Card */}
          <Card variant="glass" padding="lg">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <h3 className="text-lg font-bold text-text">Estado del Sistema</h3>
            </div>
            <div className="text-sm text-lightText">
              <div className="flex justify-between items-center">
                <span>Última sincronización</span>
                <span className="text-green-600 font-medium">Hace 2 min</span>
              </div>
            </div>
          </Card>
        </aside>
      </main>
  </Container>
  </ProtectedRoute>
  );
}
