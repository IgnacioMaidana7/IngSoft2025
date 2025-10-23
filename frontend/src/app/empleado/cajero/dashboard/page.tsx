"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/feedback/ToastProvider";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import Button from "@/components/ui/Button";
import {
  obtenerPerfilEmpleado,
  obtenerVentas,
  EmpleadoAuthResponse,
  Venta
} from "@/lib/api";

interface EmpleadoData {
  nombre: string;
  nombre_completo: string;
  email: string;
  dni: string;
  puesto: 'CAJERO';
  supermercado_nombre: string;
  deposito_nombre: string | null;
  fecha_registro: string;
}

export default function CajeroDashboard() {
  const { token } = useAuth();
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [empleadoData, setEmpleadoData] = useState<EmpleadoData | null>(null);
  const [ventasHoy, setVentasHoy] = useState<number>(0);
  const [totalVentasHoy, setTotalVentasHoy] = useState<string>("0.00");
  const [ventasPendientes, setVentasPendientes] = useState<number>(0);
  const [ultimasVentas, setUltimasVentas] = useState<Venta[]>([]);
  const [ventasTotales, setVentasTotales] = useState<number>(0);
  const [montoTotalHistorico, setMontoTotalHistorico] = useState<string>("0.00");

  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    cargarDatosCajero();
  }, [token, router]);

  const cargarDatosCajero = async () => {
    if (!token) return;

    try {
      setLoading(true);

      // Verificar que el usuario es cajero
      const userRole = localStorage.getItem('user_role');
      if (userRole !== 'CAJERO') {
        showToast('Acceso no autorizado', 'error');
        router.push('/empleado/dashboard');
        return;
      }

      // Cargar datos del empleado
      const perfil = await obtenerPerfilEmpleado(token);
      
      setEmpleadoData({
        nombre: perfil.nombre || perfil.nombre_completo || 'Cajero',
        nombre_completo: perfil.nombre_completo,
        email: perfil.email,
        dni: perfil.dni,
        puesto: 'CAJERO',
        supermercado_nombre: perfil.supermercado_nombre,
        deposito_nombre: perfil.deposito_nombre,
        fecha_registro: perfil.fecha_registro
      });

      // Cargar ventas pendientes y completadas desde el endpoint de ventas
      try {
        const todasVentas = await obtenerVentas(token);
        
        // Contar ventas pendientes
        const pendientes = todasVentas.filter(v => v.estado === 'PENDIENTE');
        setVentasPendientes(pendientes.length);
        
        // Filtrar ventas completadas
        const completadas = todasVentas.filter(v => v.estado === 'COMPLETADA');
        
        // Calcular ventas del día de hoy
        const hoy = new Date().toISOString().split('T')[0];
        const ventasHoyData = completadas.filter(v => {
          const fechaVenta = new Date(v.fecha_creacion).toISOString().split('T')[0];
          return fechaVenta === hoy;
        });
        
        setVentasHoy(ventasHoyData.length);
        
        const totalHoy = ventasHoyData.reduce((sum, venta) => {
          return sum + parseFloat(venta.total);
        }, 0);
        setTotalVentasHoy(totalHoy.toFixed(2));

        // Obtener últimas 5 ventas completadas
        const ventasOrdenadas = [...completadas].sort((a, b) => 
          new Date(b.fecha_creacion).getTime() - new Date(a.fecha_creacion).getTime()
        );
        setUltimasVentas(ventasOrdenadas.slice(0, 5));

        // Estadísticas totales
        setVentasTotales(completadas.length);
        
        const montoTotal = completadas.reduce((sum, venta) => {
          return sum + parseFloat(venta.total);
        }, 0);
        setMontoTotalHistorico(montoTotal.toFixed(2));
        
      } catch (error) {
        console.error('Error al cargar ventas:', error);
        setVentasPendientes(0);
        setVentasHoy(0);
        setVentasTotales(0);
      }

    } catch (error) {
      console.error('Error al cargar datos del cajero:', error);
      showToast('Error al cargar los datos del dashboard', 'error');
      
      // Datos de respaldo
      const userRole = localStorage.getItem('user_role');
      if (userRole === 'CAJERO') {
        setEmpleadoData({
          nombre: 'Cajero',
          nombre_completo: 'Cajero',
          email: 'cajero@supermercado.com',
          dni: '00000000',
          puesto: 'CAJERO',
          supermercado_nombre: 'Supermercado',
          deposito_nombre: null,
          fecha_registro: new Date().toISOString()
        });
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-lightText">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Container size="xl" className="py-8">
        {/* Header con saludo personalizado */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-text mb-2">
                ¡Bienvenido, {empleadoData?.nombre}! 💰
              </h1>
              <p className="text-lg text-lightText">
                Dashboard de Cajero - {empleadoData?.supermercado_nombre}
              </p>
            </div>
            <div className="hidden md:flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-500 to-green-600 rounded-full text-white text-4xl shadow-lg">
              💰
            </div>
          </div>
        </div>

        {/* Tarjetas de métricas principales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
                📊
              </div>
            </div>
          </Card>

          {/* Ventas Totales */}
          <Card variant="elevated" padding="lg" hover={true}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-lightText mb-1">Total Ventas</p>
                <p className="text-3xl font-bold text-text">{ventasTotales}</p>
                <p className="text-xs text-blue-600 mt-2 font-medium">
                  ${montoTotalHistorico}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white text-2xl">
                💵
              </div>
            </div>
          </Card>

          {/* Ventas Pendientes */}
          <Card variant="elevated" padding="lg" hover={true}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-lightText mb-1">Pendientes</p>
                <p className="text-3xl font-bold text-text">{ventasPendientes}</p>
                <p className="text-xs text-orange-600 mt-2 font-medium">
                  {ventasPendientes > 0 ? 'Requieren atención' : 'Sin pendientes'}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center text-white text-2xl">
                ⏳
              </div>
            </div>
            {ventasPendientes > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-sm text-orange-600 font-medium">
                  ⚠️ {ventasPendientes} venta{ventasPendientes !== 1 ? 's' : ''} sin finalizar
                </p>
              </div>
            )}
          </Card>

          {/* Promedio por Venta */}
          <Card variant="elevated" padding="lg" hover={true}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-lightText mb-1">Promedio/Venta</p>
                <p className="text-3xl font-bold text-text">
                  ${ventasHoy > 0 ? (parseFloat(totalVentasHoy) / ventasHoy).toFixed(2) : '0.00'}
                </p>
                <p className="text-xs text-purple-600 mt-2 font-medium">
                  Hoy
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center text-white text-2xl">
                📈
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => router.push('/ventas')}
                    className="p-4 bg-gradient-to-br from-green-50 to-green-100 hover:from-green-100 hover:to-green-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-green-200"
                  >
                    <div className="text-3xl mb-2">💰</div>
                    <div className="font-semibold text-text group-hover:text-green-600 transition-colors">
                      Nueva Venta
                    </div>
                    <div className="text-xs text-lightText">Procesar transacción</div>
                  </button>

                  <button
                    onClick={() => router.push('/ventas/historial')}
                    className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-blue-200"
                  >
                    <div className="text-3xl mb-2">📋</div>
                    <div className="font-semibold text-text group-hover:text-blue-600 transition-colors">
                      Historial
                    </div>
                    <div className="text-xs text-lightText">Ver todas las ventas</div>
                  </button>
                </div>
              </div>
            </Card>

            {/* Últimas ventas */}
            {ultimasVentas.length > 0 && (
              <Card>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-text mb-4 flex items-center gap-2">
                    <span>🧾</span> Últimas Ventas del Día
                  </h2>
                  <div className="space-y-3">
                    {ultimasVentas.map((venta) => (
                      <div
                        key={venta.id}
                        className="flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center text-white font-bold">
                              #{venta.id}
                            </div>
                            <div>
                              <p className="font-medium text-text">
                                ${parseFloat(venta.total).toFixed(2)}
                              </p>
                              <p className="text-xs text-lightText">
                                {new Date(venta.fecha_creacion).toLocaleTimeString('es-AR', {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })} - {venta.numero_venta}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                            ✓ Completada
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                  {ventasHoy > 5 && (
                    <div className="mt-4 text-center">
                      <Button
                        onClick={() => router.push('/empleado/cajero/historial-ventas')}
                        variant="outline"
                        size="sm"
                      >
                        Ver todas las ventas ({ventasHoy})
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {ultimasVentas.length === 0 && (
              <Card>
                <div className="p-6 text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">📊</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    No hay ventas registradas hoy
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Comienza a procesar ventas y aparecerán aquí
                  </p>
                  <Button onClick={() => router.push('/ventas')}>
                    Realizar Primera Venta
                  </Button>
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
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center mx-auto mb-3 text-white text-3xl">
                    💰
                  </div>
                  <h3 className="font-bold text-text text-lg">
                    {empleadoData?.nombre_completo}
                  </h3>
                  <p className="text-sm text-lightText">{empleadoData?.email}</p>
                  <span className="inline-block mt-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                    Cajero
                  </span>
                </div>
                <div className="border-t border-border pt-4 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-lightText">DNI:</span>
                    <span className="font-medium text-text">{empleadoData?.dni}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-lightText">Supermercado:</span>
                    <span className="font-medium text-text text-right">
                      {empleadoData?.supermercado_nombre}
                    </span>
                  </div>
                  {empleadoData?.deposito_nombre && (
                    <div className="flex justify-between">
                      <span className="text-lightText">Depósito:</span>
                      <span className="font-medium text-text">{empleadoData.deposito_nombre}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-lightText">Desde:</span>
                    <span className="font-medium text-text">
                      {new Date(empleadoData?.fecha_registro || '').toLocaleDateString('es-AR')}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Información sobre tu trabajo */}
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-bold text-text mb-4 flex items-center gap-2">
                  <span>ℹ️</span> Tu Función
                </h3>
                <div className="space-y-4 text-sm text-gray-600">
                  <p>
                    Como <strong className="text-text">cajero</strong>, tu rol principal es procesar 
                    las transacciones de venta de manera eficiente y precisa.
                  </p>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="font-semibold text-green-800 mb-2">Tus responsabilidades:</p>
                    <ul className="space-y-1 text-green-700">
                      <li>✓ Procesar ventas de productos</li>
                      <li>✓ Verificar precios y promociones</li>
                      <li>✓ Gestionar métodos de pago</li>
                      <li>✓ Generar tickets de venta</li>
                      <li>✓ Brindar atención al cliente</li>
                    </ul>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="font-semibold text-blue-800 mb-1">💡 Consejo</p>
                    <p className="text-blue-700 text-xs">
                      Utiliza el sistema de reconocimiento de productos con cámara para 
                      agilizar el proceso de ventas.
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </aside>
        </div>
      </Container>
    </div>
  );
}
