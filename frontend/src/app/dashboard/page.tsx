"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/feedback/ToastProvider";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import Button from "@/components/ui/Button";
import {
  obtenerPerfilAdministrador,
  obtenerEstadisticasProductos,
  obtenerEstadisticasEmpleados,
  obtenerEstadisticasOfertas,
  obtenerMisNotificaciones,
  obtenerHistorialVentas,
  marcarNotificacionLeida,
  UserProfile,
  EstadisticasProductos,
  EstadisticasEmpleados,
  EstadisticasOfertas,
  Notificacion,
} from "@/lib/api";

export default function DashboardPage() {
  const { token } = useAuth();
  const router = useRouter();
  const { showToast } = useToast();
  
  const [loading, setLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [statsProductos, setStatsProductos] = useState<EstadisticasProductos | null>(null);
  const [statsEmpleados, setStatsEmpleados] = useState<EstadisticasEmpleados | null>(null);
  const [statsOfertas, setStatsOfertas] = useState<EstadisticasOfertas | null>(null);
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);
  const [ventasHoy, setVentasHoy] = useState<number>(0);
  const [totalVentasHoy, setTotalVentasHoy] = useState<string>("0.00");

  useEffect(() => {
    if (!token) return;
    
    // Verificar tipo de usuario y redirigir a empleados
    const userType = localStorage.getItem('user_type');
    const userRole = localStorage.getItem('user_role');
    
    if (userType === 'empleado') {
      // Redirigir a dashboard específico según el rol
      if (userRole === 'CAJERO') {
        router.replace('/empleado/cajero/dashboard');
        return;
      } else if (userRole === 'REPONEDOR') {
        router.replace('/empleado/reponedor/dashboard');
        return;
      } else {
        // Fallback al dashboard genérico de empleados
        router.replace('/empleado/dashboard');
        return;
      }
    }
    
    cargarDatosDashboard();
  }, [token, router]);

  const cargarDatosDashboard = async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      
      // Cargar datos en paralelo
      const [
        perfil,
        estadisticasProductos,
        estadisticasEmpleados,
        estadisticasOfertas,
        misNotificaciones,
        historialVentas,
      ] = await Promise.allSettled([
        obtenerPerfilAdministrador(token),
        obtenerEstadisticasProductos(token),
        obtenerEstadisticasEmpleados(token),
        obtenerEstadisticasOfertas(token),
        obtenerMisNotificaciones(token),
        obtenerHistorialVentas({ 
          fecha_desde: new Date().toISOString().split('T')[0],
          page_size: 100 
        }, token),
      ]);

      if (perfil.status === 'fulfilled') setUserProfile(perfil.value);
      if (estadisticasProductos.status === 'fulfilled') setStatsProductos(estadisticasProductos.value);
      if (estadisticasEmpleados.status === 'fulfilled') setStatsEmpleados(estadisticasEmpleados.value);
      if (estadisticasOfertas.status === 'fulfilled') setStatsOfertas(estadisticasOfertas.value);
      if (misNotificaciones.status === 'fulfilled') {
        setNotificaciones(misNotificaciones.value.slice(0, 5));
      }
      
      if (historialVentas.status === 'fulfilled') {
        const ventasCompletadas = historialVentas.value.results.filter(v => v.estado === 'COMPLETADA');
        setVentasHoy(ventasCompletadas.length);
        
        const total = ventasCompletadas.reduce((sum, venta) => {
          return sum + parseFloat(venta.total);
        }, 0);
        setTotalVentasHoy(total.toFixed(2));
      }
    } catch (error) {
      console.error('Error al cargar datos del dashboard:', error);
      showToast('Error al cargar algunos datos del dashboard', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleMarcarNotificacionLeida = async (id: number) => {
    if (!token) return;
    
    try {
      await marcarNotificacionLeida(id, token);
      setNotificaciones(prev => 
        prev.map(n => n.id === id ? { ...n, leida: true } : n)
      );
    } catch (error) {
      console.error('Error al marcar notificación como leída:', error);
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <Container size="lg" className="py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-lightText">Cargando dashboard...</p>
          </div>
        </Container>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">        
        <Container size="xl" className="py-8">
          {/* Header con saludo personalizado */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl md:text-4xl font-bold text-text mb-2">
                  ¡Bienvenido, {userProfile?.nombre_supermercado || 'Administrador'}! 👋
                </h1>
                <p className="text-lg text-lightText">
                  Aquí está el resumen de tu negocio en tiempo real
                </p>
              </div>
              {userProfile?.logo && (
                <img
                  src={userProfile.logo.startsWith('http') 
                    ? userProfile.logo 
                    : `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'}${userProfile.logo}`}
                  alt="Logo"
                  className="h-16 w-16 rounded-full object-cover border-2 border-primary/20"
                />
              )}
            </div>
          </div>

          {/* Tarjetas de métricas principales */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Productos */}
            <Card variant="elevated" padding="lg" hover={true}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-lightText mb-1">Total Productos</p>
                  <p className="text-3xl font-bold text-text">
                    {statsProductos?.total_productos || 0}
                  </p>
                  <p className="text-xs text-lightText mt-2">
                    {statsProductos?.total_categorias || 0} categorías
                  </p>
                </div>
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white text-2xl">
                  📦
                </div>
              </div>
              {statsProductos && statsProductos.productos_sin_stock > 0 && (
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-sm text-red-600 font-medium">
                    ⚠️ {statsProductos.productos_sin_stock} sin stock
                  </p>
                </div>
              )}
            </Card>

            {/* Ventas del día */}
            <Card variant="elevated" padding="lg" hover={true}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-lightText mb-1">Ventas Hoy</p>
                  <p className="text-3xl font-bold text-text">{ventasHoy}</p>
                  <p className="text-xs text-green-600 mt-2 font-medium">
                    ${totalVentasHoy}
                  </p>
                </div>
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center text-white text-2xl">
                  💰
                </div>
              </div>
            </Card>

            {/* Empleados */}
            <Card variant="elevated" padding="lg" hover={true}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-lightText mb-1">Empleados</p>
                  <p className="text-3xl font-bold text-text">
                    {statsEmpleados?.total_empleados || 0}
                  </p>
                  <div className="flex gap-2 mt-2 text-xs text-lightText">
                    <span>👤 {statsEmpleados?.empleados_por_puesto?.CAJERO || 0} cajeros</span>
                    <span>📦 {statsEmpleados?.empleados_por_puesto?.REPONEDOR || 0} reponedores</span>
                  </div>
                </div>
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center text-white text-2xl">
                  👥
                </div>
              </div>
            </Card>

            {/* Ofertas */}
            <Card variant="elevated" padding="lg" hover={true}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-lightText mb-1">Ofertas Activas</p>
                  <p className="text-3xl font-bold text-text">
                    {statsOfertas?.activas || 0}
                  </p>
                  <p className="text-xs text-lightText mt-2">
                    {statsOfertas?.proximas || 0} próximas
                  </p>
                </div>
                <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center text-white text-2xl">
                  🎁
                </div>
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Columna principal */}
            <div className="lg:col-span-2 space-y-6">
              {/* Accesos rápidos */}
              <Card>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-text mb-4 flex items-center gap-2">
                    <span>⚡</span> Acciones Rápidas
                  </h2>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <button
                      onClick={() => router.push('/productos')}
                      className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-blue-200"
                    >
                      <div className="text-3xl mb-2">📦</div>
                      <div className="font-semibold text-text group-hover:text-blue-600 transition-colors">
                        Productos
                      </div>
                      <div className="text-xs text-lightText">Gestionar inventario</div>
                    </button>

                    <button
                      onClick={() => router.push('/empleados')}
                      className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 hover:from-purple-100 hover:to-purple-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-purple-200"
                    >
                      <div className="text-3xl mb-2">👥</div>
                      <div className="font-semibold text-text group-hover:text-purple-600 transition-colors">
                        Empleados
                      </div>
                      <div className="text-xs text-lightText">Administrar equipo</div>
                    </button>

                    <button
                      onClick={() => router.push('/ventas/historial')}
                      className="p-4 bg-gradient-to-br from-green-50 to-green-100 hover:from-green-100 hover:to-green-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-green-200"
                    >
                      <div className="text-3xl mb-2">📊</div>
                      <div className="font-semibold text-text group-hover:text-green-600 transition-colors">
                        Ventas
                      </div>
                      <div className="text-xs text-lightText">Ver historial</div>
                    </button>

                    <button
                      onClick={() => router.push('/ofertas')}
                      className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 hover:from-orange-100 hover:to-orange-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-orange-200"
                    >
                      <div className="text-3xl mb-2">🎁</div>
                      <div className="font-semibold text-text group-hover:text-orange-600 transition-colors">
                        Ofertas
                      </div>
                      <div className="text-xs text-lightText">Crear promociones</div>
                    </button>

                    <button
                      onClick={() => router.push('/inventario/depositos')}
                      className="p-4 bg-gradient-to-br from-indigo-50 to-indigo-100 hover:from-indigo-100 hover:to-indigo-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-indigo-200"
                    >
                      <div className="text-3xl mb-2">🏪</div>
                      <div className="font-semibold text-text group-hover:text-indigo-600 transition-colors">
                        Depósitos
                      </div>
                      <div className="text-xs text-lightText">Gestionar ubicaciones</div>
                    </button>

                    <button
                      onClick={() => router.push('/perfil')}
                      className="p-4 bg-gradient-to-br from-pink-50 to-pink-100 hover:from-pink-100 hover:to-pink-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-pink-200"
                    >
                      <div className="text-3xl mb-2">⚙️</div>
                      <div className="font-semibold text-text group-hover:text-pink-600 transition-colors">
                        Perfil
                      </div>
                      <div className="text-xs text-lightText">Configuración</div>
                    </button>
                  </div>
                </div>
              </Card>

              {/* Distribución de stock por categoría */}
              {statsProductos && statsProductos.stock_por_categoria.length > 0 && (
                <Card>
                  <div className="p-6">
                    <h2 className="text-xl font-bold text-text mb-4 flex items-center gap-2">
                      <span>📊</span> Stock por Categoría
                    </h2>
                    <div className="space-y-3">
                      {statsProductos.stock_por_categoria.slice(0, 5).map((cat, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-text">{cat.categoria}</span>
                              <span className="text-sm text-lightText">
                                {cat.productos_count} productos
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-gradient-to-r from-primary to-primary/80 h-2 rounded-full transition-all duration-500"
                                style={{ 
                                  width: `${Math.min((cat.stock_total / (statsProductos.stock_por_categoria[0]?.stock_total || 1)) * 100, 100)}%` 
                                }}
                              />
                            </div>
                          </div>
                          <span className="ml-4 font-bold text-primary text-lg">
                            {cat.stock_total}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              )}
            </div>

            {/* Sidebar */}
            <aside className="space-y-6">
              {/* Información del perfil */}
              <Card variant="elevated">
                <div className="p-6">
                  <div className="text-center mb-4">
                    {userProfile?.logo ? (
                      <img
                        src={userProfile.logo.startsWith('http') 
                          ? userProfile.logo 
                          : `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'}${userProfile.logo}`}
                        alt="Logo"
                        className="w-20 h-20 rounded-full object-cover mx-auto mb-3 border-4 border-primary/20"
                      />
                    ) : (
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center mx-auto mb-3 text-white text-3xl">
                        🏪
                      </div>
                    )}
                    <h3 className="font-bold text-text text-lg">
                      {userProfile?.nombre_supermercado}
                    </h3>
                    <p className="text-sm text-lightText">{userProfile?.email}</p>
                  </div>
                  <div className="border-t border-border pt-4 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-lightText">Ubicación:</span>
                      <span className="font-medium text-text">
                        {userProfile?.localidad}, {userProfile?.provincia}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-lightText">CUIL:</span>
                      <span className="font-medium text-text">{userProfile?.cuil}</span>
                    </div>
                  </div>
                  <Button
                    onClick={() => router.push('/perfil')}
                    variant="outline"
                    className="w-full mt-4"
                    size="sm"
                  >
                    Ver Perfil Completo
                  </Button>
                </div>
              </Card>

              {/* Notificaciones */}
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-bold text-text mb-4 flex items-center gap-2">
                    <span>🔔</span> Notificaciones
                    {notificaciones.filter(n => !n.leida).length > 0 && (
                      <span className="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                        {notificaciones.filter(n => !n.leida).length}
                      </span>
                    )}
                  </h3>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {notificaciones.length === 0 ? (
                      <p className="text-sm text-lightText text-center py-4">
                        No tienes notificaciones
                      </p>
                    ) : (
                      notificaciones.map((notif) => (
                        <div
                          key={notif.id}
                          className={`p-3 rounded-lg border transition-all ${
                            notif.leida
                              ? 'bg-gray-50 border-gray-200'
                              : 'bg-blue-50 border-blue-200'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <p className="font-medium text-sm text-text">{notif.titulo}</p>
                              <p className="text-xs text-lightText mt-1">{notif.mensaje}</p>
                              <p className="text-xs text-lightText mt-1">
                                {new Date(notif.creada_en).toLocaleDateString('es-AR', {
                                  day: 'numeric',
                                  month: 'short',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </p>
                            </div>
                            {!notif.leida && (
                              <button
                                onClick={() => handleMarcarNotificacionLeida(notif.id)}
                                className="text-blue-600 hover:text-blue-800 text-xs"
                              >
                                Marcar leída
                              </button>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </Card>
            </aside>
          </div>
        </Container>
      </div>
    </ProtectedRoute>
  );
}
