"use client";
import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/feedback/ToastProvider";
import { 
  obtenerDepositos, 
  eliminarDeposito,
  Deposito,
  obtenerProductosPorDeposito,
  type ProductosPorDeposito
} from "@/lib/api";

// Wrapper component to satisfy Next.js requirement: useSearchParams must be inside a Suspense boundary
export default function DepositosPage() {
  return (
    <Suspense fallback={
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="text-lg">Cargando depósitos...</div>
          </div>
        </Card>
      </Container>
    }>
      <DepositosPageContent />
    </Suspense>
  );
}

function DepositosPageContent() {
  const { token } = useAuth();
  const { showToast } = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [depositos, setDepositos] = useState<Deposito[]>([]);
  const [loading, setLoading] = useState(true);
  const [busqueda, setBusqueda] = useState<string>('');
  const [stockOpen, setStockOpen] = useState(false);
  const [stockLoading, setStockLoading] = useState(false);
  const [stockData, setStockData] = useState<ProductosPorDeposito | null>(null);
  const [stockError, setStockError] = useState<string | null>(null);

  // Cargar depósitos
  useEffect(() => {
    if (!token) return;
    
    const cargarDepositos = async () => {
      try {
        setLoading(true);
        console.log('Cargando depósitos...');
        const depositosData = await obtenerDepositos(token);
        console.log('Datos recibidos:', depositosData);
        console.log('Depósitos procesados:', depositosData);
        setDepositos(depositosData);
      } catch (error) {
        console.error('Error al cargar depósitos:', error);
        showToast(`Error al cargar depósitos: ${error}`, 'error');
        // En caso de error, establecer array vacío
        setDepositos([]);
      } finally {
        setLoading(false);
      }
    };

    cargarDepositos();
    
    // Limpiar el parámetro created si existe
    if (searchParams.get('created') === 'true') {
      router.replace('/inventario/depositos');
    }
  }, [token, showToast, searchParams, router]);

  const handleEliminarDeposito = async (id: number, nombre: string) => {
    if (!token) return;
    
    if (window.confirm(`¿Estás seguro de que deseas eliminar el depósito "${nombre}"?`)) {
      try {
        await eliminarDeposito(id, token);
        setDepositos(depositos?.filter(d => d.id !== id) || []);
        showToast('Depósito eliminado correctamente', 'success');
      } catch (error) {
        showToast(`Error al eliminar depósito: ${error}`, 'error');
      }
    }
  };

  const handleVerStock = async (deposito: Deposito) => {
    if (!token) return;
    try {
      setStockError(null);
      setStockLoading(true);
      setStockOpen(true);
      const data = await obtenerProductosPorDeposito(deposito.id, token);
      setStockData(data);
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Error al obtener el stock del depósito';
      setStockError(msg);
      showToast(msg, 'error');
    } finally {
      setStockLoading(false);
    }
  };

  const closeStock = () => {
    setStockOpen(false);
    setStockData(null);
    setStockError(null);
  };

  // Filtrar depósitos por búsqueda
  const depositosFiltrados = depositos?.filter(deposito =>
    deposito.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
    deposito.direccion.toLowerCase().includes(busqueda.toLowerCase())
  ) || [];

  if (loading) {
    return (
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="text-lg">Cargando depósitos...</div>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <Container>
      <Card>
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-border">
          <div>
            <h1 className="text-3xl font-bold text-text mb-1">Gestión de Depósitos</h1>
            <p className="text-lightText">Administra las ubicaciones de almacenamiento</p>
          </div>
          <Button 
            onClick={() => router.push('/inventario/depositos/nuevo')}
            className="bg-primary text-white px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors"
          >
            + Nuevo Depósito
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{depositos?.length || 0}</div>
            <div className="text-sm text-blue-700">Total Depósitos</div>
          </div>
          <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {depositos?.filter(d => d.activo).length || 0}
            </div>
            <div className="text-sm text-green-700">Depósitos Activos</div>
          </div>
          <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-4 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {depositos?.filter(d => !d.activo).length || 0}
            </div>
            <div className="text-sm text-orange-700">Inactivos</div>
          </div>
        </div>

        {/* Búsqueda */}
        <div className="mb-6">
          <Input
            label="Buscar depósito"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Nombre o dirección del depósito"
          />
        </div>

        {/* Lista de depósitos */}
        {depositosFiltrados.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-500 mb-4">
              {depositos.length === 0 
                ? 'No hay depósitos registrados' 
                : 'No se encontraron depósitos con esos criterios'
              }
            </div>
            {depositos.length === 0 && (
              <Button onClick={() => router.push('/inventario/depositos/nuevo')}>
                Crear el primer depósito
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {depositosFiltrados.map((deposito) => (
              <div key={deposito.id} className="border border-border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg text-text">{deposito.nombre}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        deposito.activo 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {deposito.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </div>
                    <div className="text-sm text-lightText space-y-1">
                      <div><strong>Dirección:</strong> {deposito.direccion}</div>
                      {deposito.descripcion && (
                        <div><strong>Descripción:</strong> {deposito.descripcion}</div>
                      )}
                      <div><strong>Creado:</strong> {new Date(deposito.fecha_creacion).toLocaleDateString()}</div>
                      <div><strong>Modificado:</strong> {
                        deposito.fecha_modificacion !== deposito.fecha_creacion 
                          ? new Date(deposito.fecha_modificacion).toLocaleDateString()
                          : "Todavía no se ha modificado"
                      }</div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="ghost"
                      onClick={() => handleVerStock(deposito)}
                      className="text-blue-600 hover:text-blue-700 px-3 py-1 border border-blue-600 rounded hover:bg-blue-50 transition-colors"
                    >
                      Ver Stock
                    </Button>
                    <Button 
                      variant="ghost"
                      onClick={() => router.push(`/inventario/depositos/${deposito.id}`)}
                      className="text-primary hover:text-primary/80 px-3 py-1 border border-primary rounded hover:bg-primary/10 transition-colors"
                    >
                      Editar
                    </Button>
                    <button 
                      onClick={() => handleEliminarDeposito(deposito.id, deposito.nombre)}
                      className="text-red-600 hover:text-red-700 px-3 py-1 border border-red-600 rounded hover:bg-red-50 transition-colors"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Modal Ver Stock */}
      {stockOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/30" onClick={closeStock} />
          <div className="relative bg-white rounded-lg shadow-lg w-full max-w-2xl mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Stock por Depósito</h2>
              <button onClick={closeStock} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            {stockLoading ? (
              <div className="py-10 text-center">Cargando stock...</div>
            ) : stockError ? (
              <div className="py-4 text-red-600">{stockError}</div>
            ) : stockData ? (
              <div>
                <div className="mb-4 text-sm text-gray-600">
                  <div><span className="font-medium">Depósito:</span> {stockData.deposito.nombre}</div>
                  <div><span className="font-medium">Dirección:</span> {stockData.deposito.direccion}</div>
                </div>
                {stockData.productos.length === 0 ? (
                  <div className="py-6 text-center text-gray-500">Este depósito no tiene stock registrado.</div>
                ) : (
                  <div className="overflow-x-auto border rounded-md">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Producto</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {stockData.productos.map((p) => (
                          <tr key={p.stock_id} className="hover:bg-gray-50">
                            <td className="px-4 py-2 text-sm text-gray-900">{p.nombre}</td>
                            <td className="px-4 py-2 text-sm text-gray-900">{p.cantidad}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                <div className="mt-4 flex justify-end">
                  <Button onClick={closeStock}>Cerrar</Button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </Container>
  );
}
