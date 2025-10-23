"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/feedback/ToastProvider";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import Button from "@/components/ui/Button";
import { obtenerPerfilEmpleado } from "@/lib/api";

interface EmpleadoData {
  nombre: string;
  nombre_completo: string;
  email: string;
  dni: string;
  puesto: 'REPONEDOR';
  supermercado_nombre: string;
  deposito_nombre: string | null;
  fecha_registro: string;
}

interface DepositoData {
  id: number;
  nombre: string;
  direccion: string;
  activo: boolean;
}

interface ProductoStock {
  id: number;
  producto: {
    id: number;
    nombre: string;
    categoria: {
      id: number;
      nombre: string;
    };
    precio: string;
  };
  cantidad: number;
  stock_minimo: number;
}

interface Transferencia {
  id: number;
  fecha_creacion: string;
  estado: 'PENDIENTE' | 'CONFIRMADA' | 'CANCELADA';
  deposito_origen_nombre: string;
  deposito_destino_nombre: string;
  observaciones: string;
}

export default function ReponedorDashboard() {
  const { token } = useAuth();
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [empleadoData, setEmpleadoData] = useState<EmpleadoData | null>(null);
  const [depositoData, setDepositoData] = useState<DepositoData | null>(null);
  
  // Estadísticas
  const [totalProductos, setTotalProductos] = useState(0);
  const [productosStockBajo, setProductosStockBajo] = useState(0);
  const [transferenciasActivas, setTransferenciasActivas] = useState(0);
  const [productosRecientes, setProductosRecientes] = useState<ProductoStock[]>([]);
  const [ultimasTransferencias, setUltimasTransferencias] = useState<Transferencia[]>([]);

  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    cargarDatosReponedor();
  }, [token, router]);

  const cargarDatosReponedor = async () => {
    if (!token) return;

    try {
      setLoading(true);

      // Verificar que el usuario es reponedor
      const userRole = localStorage.getItem('user_role');
      if (userRole !== 'REPONEDOR') {
        showToast('Acceso no autorizado', 'error');
        router.push('/empleado/dashboard');
        return;
      }

      // Cargar datos del empleado
      const perfil = await obtenerPerfilEmpleado(token);
      
      setEmpleadoData({
        nombre: perfil.nombre || perfil.nombre_completo || 'Reponedor',
        nombre_completo: perfil.nombre_completo,
        email: perfil.email,
        dni: perfil.dni,
        puesto: 'REPONEDOR',
        supermercado_nombre: perfil.supermercado_nombre,
        deposito_nombre: perfil.deposito_nombre,
        fecha_registro: perfil.fecha_registro
      });

      // Cargar datos del depósito asignado
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${API_BASE_URL}/api/inventario/mi-deposito/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const deposito = await response.json();
          setDepositoData(deposito);

          // Cargar productos del depósito
          await cargarProductosDeposito(deposito.id);
        }
      } catch (error) {
        console.log('No se pudo cargar información del depósito');
      }

      // Cargar transferencias
      await cargarTransferencias();

    } catch (error) {
      console.error('Error al cargar datos del reponedor:', error);
      showToast('Error al cargar los datos', 'error');
      
      // Datos de respaldo
      const userRole = localStorage.getItem('user_role');
      if (userRole === 'REPONEDOR') {
        setEmpleadoData({
          nombre: 'Reponedor',
          nombre_completo: 'Reponedor',
          email: 'reponedor@supermercado.com',
          dni: '00000000',
          puesto: 'REPONEDOR',
          supermercado_nombre: 'Supermercado',
          deposito_nombre: null,
          fecha_registro: new Date().toISOString()
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const cargarProductosDeposito = async (depositoId: number) => {
    if (!token) return;
    
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${API_BASE_URL}/api/inventario/depositos/${depositoId}/productos/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const productos = await response.json();
        setTotalProductos(productos.length);
        
        // Filtrar productos con stock bajo
        const stockBajo = productos.filter((p: ProductoStock) => 
          p.cantidad <= p.stock_minimo && p.cantidad > 0
        );
        setProductosStockBajo(stockBajo.length);
        
        // Obtener últimos 5 productos
        setProductosRecientes(productos.slice(0, 5));
      }
    } catch (error) {
      console.log('No se pudieron cargar los productos del depósito');
    }
  };

  const cargarTransferencias = async () => {
    if (!token) return;
    
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${API_BASE_URL}/api/inventario/transferencias/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const transferencias = data.results || data;
        
        // Contar transferencias activas (pendientes)
        const activas = transferencias.filter((t: Transferencia) => t.estado === 'PENDIENTE');
        setTransferenciasActivas(activas.length);
        
        // Últimas 5 transferencias
        setUltimasTransferencias(transferencias.slice(0, 5));
      }
    } catch (error) {
      console.log('No se pudieron cargar las transferencias');
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
                ¡Bienvenido, {empleadoData?.nombre}! 📦
              </h1>
              <p className="text-lg text-lightText">
                Dashboard de Reponedor - {empleadoData?.supermercado_nombre}
              </p>
            </div>
            <div className="hidden md:flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full text-white text-4xl shadow-lg">
              📦
            </div>
          </div>
        </div>

        {/* Tarjetas de métricas principales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Productos */}
          <Card variant="elevated" padding="lg" hover={true}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-lightText mb-1">Total Productos</p>
                <p className="text-3xl font-bold text-text">{totalProductos}</p>
                <p className="text-xs text-blue-600 mt-2 font-medium">
                  En depósito
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white text-2xl">
                📦
              </div>
            </div>
          </Card>

          {/* Stock Bajo */}
          <Card variant="elevated" padding="lg" hover={true}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-lightText mb-1">Stock Bajo</p>
                <p className="text-3xl font-bold text-text">{productosStockBajo}</p>
                <p className="text-xs text-orange-600 mt-2 font-medium">
                  {productosStockBajo > 0 ? 'Requieren atención' : 'Todo bien'}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center text-white text-2xl">
                ⚠️
              </div>
            </div>
            {productosStockBajo > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-sm text-orange-600 font-medium">
                  ⚠️ {productosStockBajo} producto{productosStockBajo !== 1 ? 's' : ''} con stock bajo
                </p>
              </div>
            )}
          </Card>

          {/* Transferencias Activas */}
          <Card variant="elevated" padding="lg" hover={true}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-lightText mb-1">Transferencias</p>
                <p className="text-3xl font-bold text-text">{transferenciasActivas}</p>
                <p className="text-xs text-purple-600 mt-2 font-medium">
                  Pendientes
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center text-white text-2xl">
                🚚
              </div>
            </div>
          </Card>

          {/* Depósito Asignado */}
          <Card variant="elevated" padding="lg" hover={true}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-lightText mb-1">Mi Depósito</p>
                <p className="text-lg font-bold text-text">{depositoData?.nombre || 'N/A'}</p>
                <p className="text-xs text-green-600 mt-2 font-medium">
                  {depositoData?.activo ? '✓ Activo' : '✗ Inactivo'}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center text-white text-2xl">
                🏪
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
                    <div className="text-xs text-lightText">Ver catálogo</div>
                  </button>

                  <button
                    onClick={() => router.push('/inventario')}
                    className="p-4 bg-gradient-to-br from-green-50 to-green-100 hover:from-green-100 hover:to-green-200 rounded-xl text-left transition-all duration-300 hover:scale-105 group border border-green-200"
                  >
                    <div className="text-3xl mb-2">🏪</div>
                    <div className="font-semibold text-text group-hover:text-green-600 transition-colors">
                      Inventario
                    </div>
                    <div className="text-xs text-lightText">Gestionar stock</div>
                  </button>
                </div>
              </div>
            </Card>

            {/* Últimos productos */}
            {productosRecientes.length > 0 && (
              <Card>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-text mb-4 flex items-center gap-2">
                    <span>📋</span> Productos en Depósito
                  </h2>
                  <div className="space-y-3">
                    {productosRecientes.map((prod) => (
                      <div
                        key={prod.id}
                        className="flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                              {prod.producto.categoria.nombre.substring(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-medium text-text">
                                {prod.producto.nombre}
                              </p>
                              <p className="text-xs text-lightText">
                                ${parseFloat(prod.producto.precio).toFixed(2)} - {prod.producto.categoria.nombre}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <p className="font-bold text-text">{prod.cantidad}</p>
                            <p className="text-xs text-lightText">unidades</p>
                          </div>
                          {prod.cantidad <= prod.stock_minimo && (
                            <span className="px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700">
                              ⚠️ Bajo
                            </span>
                          )}
                          {prod.cantidad > prod.stock_minimo && (
                            <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                              ✓ OK
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {totalProductos > 5 && (
                    <div className="mt-4 text-center">
                      <Button
                        onClick={() => router.push('/inventario')}
                        variant="outline"
                        size="sm"
                      >
                        Ver todos los productos ({totalProductos})
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Últimas transferencias */}
            {ultimasTransferencias.length > 0 && (
              <Card>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-text mb-4 flex items-center gap-2">
                    <span>🚚</span> Transferencias Recientes
                  </h2>
                  <div className="space-y-3">
                    {ultimasTransferencias.map((trans) => (
                      <div
                        key={trans.id}
                        className="flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold">
                              #{trans.id}
                            </div>
                            <div>
                              <p className="font-medium text-text">
                                {trans.deposito_origen_nombre} → {trans.deposito_destino_nombre}
                              </p>
                              <p className="text-xs text-lightText">
                                {new Date(trans.fecha_creacion).toLocaleDateString('es-AR')}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            trans.estado === 'PENDIENTE' 
                              ? 'bg-orange-100 text-orange-700'
                              : trans.estado === 'CONFIRMADA'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {trans.estado === 'PENDIENTE' && '⏳ Pendiente'}
                            {trans.estado === 'CONFIRMADA' && '✓ Confirmada'}
                            {trans.estado === 'CANCELADA' && '✗ Cancelada'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 text-center">
                    <Button
                      onClick={() => router.push('/inventario')}
                      variant="outline"
                      size="sm"
                    >
                      Ver todas las transferencias
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {productosRecientes.length === 0 && (
              <Card>
                <div className="p-6 text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">📦</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    No hay productos en el depósito
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Comienza a gestionar el inventario de productos
                  </p>
                  <Button onClick={() => router.push('/inventario')}>
                    Ir a Inventario
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
                <h3 className="text-lg font-bold text-text mb-4 flex items-center gap-2">
                  <span>👤</span> Mi Perfil
                </h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-lightText">Nombre completo</p>
                    <p className="font-medium text-text">{empleadoData?.nombre_completo}</p>
                  </div>
                  <div>
                    <p className="text-sm text-lightText">Email</p>
                    <p className="font-medium text-text break-all">{empleadoData?.email}</p>
                  </div>
                  <div>
                    <p className="text-sm text-lightText">DNI</p>
                    <p className="font-medium text-text">{empleadoData?.dni}</p>
                  </div>
                  <div>
                    <p className="text-sm text-lightText">Puesto</p>
                    <p className="font-medium">
                      <span className="px-3 py-1 rounded-full text-xs bg-blue-100 text-blue-700">
                        {empleadoData?.puesto}
                      </span>
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-lightText">Supermercado</p>
                    <p className="font-medium text-text">{empleadoData?.supermercado_nombre}</p>
                  </div>
                  {depositoData && (
                    <div>
                      <p className="text-sm text-lightText">Depósito asignado</p>
                      <p className="font-medium text-text">{depositoData.nombre}</p>
                      <p className="text-xs text-lightText">{depositoData.direccion}</p>
                    </div>
                  )}
                </div>
              </div>
            </Card>

            {/* Consejos */}
            <Card variant="elevated">
              <div className="p-6">
                <h3 className="text-lg font-bold text-text mb-4 flex items-center gap-2">
                  <span>💡</span> Consejos
                </h3>
                <div className="space-y-3 text-sm text-lightText">
                  <div className="flex items-start gap-2">
                    <span className="text-blue-500">•</span>
                    <p>Revisa el inventario regularmente para mantener el stock actualizado</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-blue-500">•</span>
                    <p>Atiende primero los productos con stock bajo</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-blue-500">•</span>
                    <p>Utiliza las transferencias para optimizar la distribución</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-blue-500">•</span>
                    <p>Verifica las ofertas activas periódicamente</p>
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
