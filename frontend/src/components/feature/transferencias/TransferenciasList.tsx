"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { obtenerTransferencias, eliminarTransferencia } from '@/lib/transferenciasApi';
import type { TransferenciaList } from '@/types/transferencias';
import Container from '@/components/layout/Container';
import Card from '@/components/layout/Card';
import Button from '@/components/ui/Button';
import { COLORS } from '@/constants/colors';

const ESTADO_COLORS = {
  PENDIENTE: '#FFA726',
  CONFIRMADA: '#66BB6A', 
  CANCELADA: '#EF5350'
};

const ESTADO_LABELS = {
  PENDIENTE: 'Pendiente',
  CONFIRMADA: 'Confirmada',
  CANCELADA: 'Cancelada'
};

export default function TransferenciasListPage() {
  const { token } = useAuth();
  const [transferencias, setTransferencias] = useState<TransferenciaList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargarTransferencias = async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      const data = await obtenerTransferencias(token);
      setTransferencias(data);
    } catch (error) {
      console.error('Error cargando transferencias:', error);
      setError('Error al cargar las transferencias');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      cargarTransferencias();
    }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleEliminar = async (id: number) => {
    if (!token) return;
    
    if (window.confirm('¿Está seguro de que desea eliminar esta transferencia?')) {
      try {
        await eliminarTransferencia(id, token);
        await cargarTransferencias(); // Recargar lista
      } catch (error) {
        console.error('Error eliminando transferencia:', error);
        setError('Error al eliminar la transferencia');
      }
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

  if (loading) {
    return (
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-lightText">Cargando transferencias...</p>
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
            Transferencias de Productos
          </h1>
          <Link href="/inventario/transferencias/nueva">
            <Button>Nueva Transferencia</Button>
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {transferencias.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📦</div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: COLORS.text }}>
              No hay transferencias registradas
            </h3>
            <p className="text-lightText mb-6">
              Comience creando su primera transferencia de productos
            </p>
            <Link href="/inventario/transferir/nueva">
              <Button>Crear Primera Transferencia</Button>
            </Link>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-border">
            <div className="overflow-x-auto">
              <table className="w-full bg-white">
                <thead style={{ backgroundColor: `${COLORS.primary}20` }}>
                  <tr>
                    <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                      ID
                    </th>
                    <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                      Origen
                    </th>
                    <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                      Destino
                    </th>
                    <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                      Fecha
                    </th>
                    <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                      Estado
                    </th>
                    <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                      Productos
                    </th>
                    <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {transferencias.map((transferencia, index) => (
                    <tr 
                      key={transferencia.id} 
                      className={`border-t border-border ${
                        index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                      }`}
                    >
                      <td className="p-4 font-medium" style={{ color: COLORS.text }}>
                        #{transferencia.id}
                      </td>
                      <td className="p-4" style={{ color: COLORS.lightText }}>
                        {transferencia.deposito_origen_nombre}
                      </td>
                      <td className="p-4" style={{ color: COLORS.lightText }}>
                        {transferencia.deposito_destino_nombre}
                      </td>
                      <td className="p-4" style={{ color: COLORS.lightText }}>
                        {formatFecha(transferencia.fecha_transferencia)}
                      </td>
                      <td className="p-4">
                        <span 
                          className="px-3 py-1 rounded-full text-sm font-medium text-white"
                          style={{ 
                            backgroundColor: ESTADO_COLORS[transferencia.estado]
                          }}
                        >
                          {ESTADO_LABELS[transferencia.estado]}
                        </span>
                      </td>
                      <td className="p-4" style={{ color: COLORS.lightText }}>
                        {transferencia.total_productos} producto(s)
                      </td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          <Link href={`/inventario/transferencias/${transferencia.id}`}>
                            <button
                              className="px-3 py-1 text-sm rounded border border-primary text-primary hover:bg-primary hover:text-white transition-colors"
                            >
                              Ver
                            </button>
                          </Link>
                          
                          {transferencia.estado === 'PENDIENTE' && (
                            <>
                              <Link href={`/inventario/transferencias/${transferencia.id}/editar`}>
                                <button
                                  className="px-3 py-1 text-sm rounded border border-blue-500 text-blue-500 hover:bg-blue-500 hover:text-white transition-colors"
                                >
                                  Editar
                                </button>
                              </Link>
                              
                              <button
                                onClick={() => handleEliminar(transferencia.id)}
                                className="px-3 py-1 text-sm rounded border border-red-500 text-red-500 hover:bg-red-500 hover:text-white transition-colors"
                              >
                                Eliminar
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="flex justify-between items-center mt-6">
          <Link href="/inventario">
            <button
              className="px-4 py-2 text-lightText hover:text-text transition-colors"
            >
              ← Volver al Inventario
            </button>
          </Link>
          
          <div className="text-sm text-lightText">
            Total: {transferencias.length} transferencia(s)
          </div>
        </div>
      </Card>
    </Container>
  );
}