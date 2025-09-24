"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { obtenerHistorialMovimientos, obtenerDepositosDisponibles, descargarRemitoPDF } from '@/lib/transferenciasApi';
import type { HistorialMovimiento, FiltrosHistorial } from '@/types/transferencias';
import Container from '@/components/layout/Container';
import Card from '@/components/layout/Card';
import { COLORS } from '@/constants/colors';

const TIPO_COLORS = {
  TRANSFERENCIA: '#2196F3',
  INGRESO: '#4CAF50',
  EGRESO: '#FF9800',
  AJUSTE: '#9C27B0',
  VENTA: '#F44336'
};

export default function MovimientosPage() {
  const { token } = useAuth();
  const [movimientos, setMovimientos] = useState<HistorialMovimiento[]>([]);
  const [depositos, setDepositos] = useState<Array<{id: number, nombre: string}>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtros, setFiltros] = useState<FiltrosHistorial>({});
  const [descargandoRemito, setDescargandoRemito] = useState<number | null>(null);

  useEffect(() => {
    if (token) {
      cargarDatos();
    }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const cargarDatos = async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      
      // Cargar movimientos y depósitos en paralelo
      const [movimientosData, depositosResponse] = await Promise.all([
        obtenerHistorialMovimientos(token, filtros),
        obtenerDepositosDisponibles(token)
      ]);
      
      setMovimientos(movimientosData);
      
      if (depositosResponse.success && depositosResponse.data) {
        setDepositos(depositosResponse.data.map(d => ({ id: d.id, nombre: d.nombre })));
      }
      
    } catch (error) {
      console.error('Error cargando datos:', error);
      setError('Error al cargar el historial de movimientos');
    } finally {
      setLoading(false);
    }
  };

  const aplicarFiltros = async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      const data = await obtenerHistorialMovimientos(token, filtros);
      setMovimientos(data);
    } catch (error) {
      console.error('Error aplicando filtros:', error);
      setError('Error al aplicar los filtros');
    } finally {
      setLoading(false);
    }
  };

  const limpiarFiltros = () => {
    setFiltros({});
    // Recargar sin filtros
    if (token) {
      obtenerHistorialMovimientos(token).then(setMovimientos);
    }
  };

  const handleDescargarRemito = async (transferenciaId: number) => {
    if (!token) return;
    
    try {
      setDescargandoRemito(transferenciaId);
      const { blob, filename } = await descargarRemitoPDF(transferenciaId, token);
      
      // Crear enlace de descarga
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Error descargando remito:', error);
      setError('Error al descargar el remito');
    } finally {
      setDescargandoRemito(null);
    }
  };

  const formatFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCantidad = (cantidad: number) => {
    return cantidad > 0 ? `+${cantidad}` : cantidad.toString();
  };

  if (loading && movimientos.length === 0) {
    return (
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-lightText">Cargando historial...</p>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <Container>
      <Card>
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold" style={{ color: COLORS.text }}>
            Historial de Movimientos
          </h1>
          <Link href="/inventario/transferencias">
            <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
              Ver Transferencias
            </button>
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Filtros */}
        <div className="bg-gray-50 p-4 rounded-xl mb-6">
          <h3 className="font-semibold mb-3" style={{ color: COLORS.text }}>Filtros</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: COLORS.text }}>
                Depósito
              </label>
              <select
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                value={filtros.deposito || ''}
                onChange={(e) => setFiltros(prev => ({ 
                  ...prev, 
                  deposito: e.target.value ? Number(e.target.value) : undefined 
                }))}
              >
                <option value="">Todos los depósitos</option>
                {depositos.map(deposito => (
                  <option key={deposito.id} value={deposito.id}>
                    {deposito.nombre}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: COLORS.text }}>
                Tipo de Movimiento
              </label>
              <select
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                value={filtros.tipo || ''}
                onChange={(e) => setFiltros(prev => ({ 
                  ...prev, 
                  tipo: e.target.value || undefined 
                }))}
              >
                <option value="">Todos los tipos</option>
                <option value="TRANSFERENCIA">Transferencia</option>
                <option value="INGRESO">Ingreso</option>
                <option value="EGRESO">Egreso</option>
                <option value="AJUSTE">Ajuste</option>
                <option value="VENTA">Venta</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: COLORS.text }}>
                Desde
              </label>
              <input
                type="date"
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                value={filtros.fecha_desde || ''}
                onChange={(e) => setFiltros(prev => ({ 
                  ...prev, 
                  fecha_desde: e.target.value || undefined 
                }))}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: COLORS.text }}>
                Hasta
              </label>
              <input
                type="date"
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                value={filtros.fecha_hasta || ''}
                onChange={(e) => setFiltros(prev => ({ 
                  ...prev, 
                  fecha_hasta: e.target.value || undefined 
                }))}
              />
            </div>
          </div>
          
          <div className="flex gap-2 mt-4">
            <button
              onClick={aplicarFiltros}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-sm"
            >
              Aplicar Filtros
            </button>
            <button
              onClick={limpiarFiltros}
              className="px-4 py-2 border border-primary text-primary rounded-lg hover:bg-primary hover:text-white transition-colors text-sm"
            >
              Limpiar
            </button>
          </div>
        </div>

        {/* Tabla de movimientos */}
        {movimientos.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: COLORS.text }}>
              No hay movimientos registrados
            </h3>
            <p className="text-lightText">
              {Object.keys(filtros).length > 0 
                ? 'No se encontraron movimientos con los filtros aplicados'
                : 'Los movimientos aparecerán aquí cuando se realicen transferencias u otras operaciones'
              }
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-hidden rounded-xl border border-border">
              <div className="overflow-x-auto">
                <table className="w-full bg-white">
                  <thead style={{ backgroundColor: `${COLORS.primary}20` }}>
                    <tr>
                      <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                        Fecha
                      </th>
                      <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                        Tipo
                      </th>
                      <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                        Producto
                      </th>
                      <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                        Origen
                      </th>
                      <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                        Destino
                      </th>
                      <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                        Cantidad
                      </th>
                      <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {movimientos.map((movimiento, index) => (
                      <tr 
                        key={movimiento.id} 
                        className={`border-t border-border ${
                          index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                        }`}
                      >
                        <td className="p-4 text-sm" style={{ color: COLORS.lightText }}>
                          {formatFecha(movimiento.fecha)}
                        </td>
                        <td className="p-4">
                          <span 
                            className="px-2 py-1 rounded-full text-xs font-medium text-white"
                            style={{ 
                              backgroundColor: TIPO_COLORS[movimiento.tipo_movimiento] || '#6B7280'
                            }}
                          >
                            {movimiento.tipo_movimiento_display}
                          </span>
                        </td>
                        <td className="p-4">
                          <div>
                            <p className="font-medium" style={{ color: COLORS.text }}>
                              {movimiento.producto_nombre}
                            </p>
                            <p className="text-xs" style={{ color: COLORS.lightText }}>
                              {movimiento.producto_categoria}
                            </p>
                          </div>
                        </td>
                        <td className="p-4 text-sm" style={{ color: COLORS.lightText }}>
                          {movimiento.deposito_origen_nombre || '-'}
                        </td>
                        <td className="p-4 text-sm" style={{ color: COLORS.lightText }}>
                          {movimiento.deposito_destino_nombre || '-'}
                        </td>
                        <td className="p-4">
                          <span 
                            className={`font-medium ${
                              movimiento.cantidad > 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {formatCantidad(movimiento.cantidad)}
                          </span>
                        </td>
                        <td className="p-4">
                          {movimiento.transferencia && (
                            <div className="flex gap-2">
                              <Link href={`/inventario/transferencias/${movimiento.transferencia}`}>
                                <button className="px-2 py-1 text-xs border border-primary text-primary rounded hover:bg-primary hover:text-white transition-colors">
                                  Ver Transferencia
                                </button>
                              </Link>
                              <button
                                onClick={() => handleDescargarRemito(movimiento.transferencia!)}
                                disabled={descargandoRemito === movimiento.transferencia}
                                className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors disabled:opacity-50"
                                style={{ backgroundColor: COLORS.primary }}
                              >
                                {descargandoRemito === movimiento.transferencia 
                                  ? 'Descargando...' 
                                  : '📄 Remito'
                                }
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            <div className="flex justify-between items-center mt-6">
              <Link href="/inventario">
                <button className="px-4 py-2 text-lightText hover:text-text transition-colors">
                  ← Volver al Inventario
                </button>
              </Link>
              
              <div className="text-sm text-lightText">
                Total: {movimientos.length} movimiento(s)
              </div>
            </div>
          </>
        )}
      </Card>
    </Container>
  );
}


