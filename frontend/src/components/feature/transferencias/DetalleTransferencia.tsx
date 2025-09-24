"use client";
import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { obtenerTransferencia, confirmarTransferencia, descargarRemitoPDF } from '@/lib/transferenciasApi';
import type { Transferencia, ConfirmarTransferencia } from '@/types/transferencias';
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

export default function DetalleTransferenciaPage() {
  const router = useRouter();
  const params = useParams();
  const { token } = useAuth();
  const transferenciId = Number(params.id);
  
  const [transferencia, setTransferencia] = useState<Transferencia | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirmando, setConfirmando] = useState(false);
  const [descargando, setDescargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [observacionesConfirmacion, setObservacionesConfirmacion] = useState('');

  useEffect(() => {
    if (transferenciId && token) {
      cargarTransferencia();
    }
  }, [transferenciId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  const cargarTransferencia = async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      const data = await obtenerTransferencia(transferenciId, token);
      setTransferencia(data);
    } catch (error) {
      console.error('Error cargando transferencia:', error);
      setError('Error al cargar la transferencia');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmar = async () => {
    if (!token || !transferencia) return;
    
    if (window.confirm('¿Está seguro de que desea confirmar esta transferencia? Esta acción actualizará los inventarios y no se puede deshacer.')) {
      try {
        setConfirmando(true);
        const data: ConfirmarTransferencia = {
          observaciones: observacionesConfirmacion || undefined
        };
        
        const response = await confirmarTransferencia(transferencia.id!, data, token);
        
        if (response.success && response.data) {
          setTransferencia(response.data);
          setError(null);
          // Mostrar mensaje de éxito
          alert('Transferencia confirmada exitosamente');
        } else {
          setError(response.error || 'Error al confirmar la transferencia');
        }
      } catch (error: unknown) {
        console.error('Error confirmando transferencia:', error);
        setError(error instanceof Error ? error.message : 'Error al confirmar la transferencia');
      } finally {
        setConfirmando(false);
      }
    }
  };

  const handleDescargarRemito = async () => {
    if (!token || !transferencia || transferencia.estado !== 'CONFIRMADA') return;
    
    try {
      setDescargando(true);
      const { blob, filename } = await descargarRemitoPDF(transferencia.id!, token);
      
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
      setDescargando(false);
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
            <p className="mt-4 text-lightText">Cargando transferencia...</p>
          </div>
        </Card>
      </Container>
    );
  }

  if (!transferencia) {
    return (
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="text-6xl mb-4">❌</div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: COLORS.text }}>
              Transferencia no encontrada
            </h3>
            <p className="text-lightText mb-6">
              La transferencia solicitada no existe o no tienes permisos para verla
            </p>
            <Button onClick={() => router.push('/inventario/transferencias')}>
              Volver a Transferencias
            </Button>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <Container>
      <Card>
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: COLORS.text }}>
              Transferencia #{transferencia.id}
            </h1>
            <div className="flex items-center gap-3 mt-2">
              <span 
                className="px-3 py-1 rounded-full text-sm font-medium text-white"
                style={{ backgroundColor: ESTADO_COLORS[transferencia.estado] }}
              >
                {ESTADO_LABELS[transferencia.estado]}
              </span>
              <span className="text-lightText">
                {formatFecha(transferencia.fecha_transferencia)}
              </span>
            </div>
          </div>
          
          <div className="flex gap-2">
            {transferencia.estado === 'CONFIRMADA' && (
              <button
                onClick={handleDescargarRemito}
                disabled={descargando}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                style={{ backgroundColor: COLORS.primary }}
              >
                {descargando ? 'Descargando...' : '📄 Descargar Remito'}
              </button>
            )}
            
            <Button onClick={() => router.push('/inventario/transferencias')}>
              Volver a Lista
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Información general */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2" style={{ color: COLORS.text }}>
                Depósito Origen
              </h3>
              <p className="text-lightText">{transferencia.deposito_origen_nombre}</p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-2" style={{ color: COLORS.text }}>
                Depósito Destino
              </h3>
              <p className="text-lightText">{transferencia.deposito_destino_nombre}</p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2" style={{ color: COLORS.text }}>
                Administrador
              </h3>
              <p className="text-lightText">{transferencia.administrador_nombre}</p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-2" style={{ color: COLORS.text }}>
                Fecha de Creación
              </h3>
              <p className="text-lightText">
                {transferencia.fecha_creacion && formatFecha(transferencia.fecha_creacion)}
              </p>
            </div>
          </div>
        </div>

        {/* Observaciones */}
        {transferencia.observaciones && (
          <div className="mb-8">
            <h3 className="font-semibold mb-2" style={{ color: COLORS.text }}>
              Observaciones
            </h3>
            <div className="bg-gray-50 p-4 rounded-xl">
              <p className="text-lightText">{transferencia.observaciones}</p>
            </div>
          </div>
        )}

        {/* Productos */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4" style={{ color: COLORS.text }}>
            Productos a Transferir
          </h3>
          
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full bg-white">
              <thead style={{ backgroundColor: `${COLORS.primary}20` }}>
                <tr>
                  <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                    Producto
                  </th>
                  <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                    Categoría
                  </th>
                  <th className="text-left p-4 font-semibold" style={{ color: COLORS.text }}>
                    Cantidad
                  </th>
                </tr>
              </thead>
              <tbody>
                {transferencia.detalles.map((detalle, index) => (
                  <tr 
                    key={detalle.id || index} 
                    className={`border-t border-border ${
                      index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                    }`}
                  >
                    <td className="p-4" style={{ color: COLORS.text }}>
                      {detalle.producto_nombre}
                    </td>
                    <td className="p-4" style={{ color: COLORS.lightText }}>
                      {detalle.producto_categoria}
                    </td>
                    <td className="p-4 font-medium" style={{ color: COLORS.text }}>
                      {detalle.cantidad}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="mt-4 text-right">
            <span className="text-sm text-lightText">
              Total de productos: {transferencia.detalles.length}
            </span>
          </div>
        </div>

        {/* Acciones para transferencias pendientes */}
        {transferencia.estado === 'PENDIENTE' && (
          <div className="border-t border-border pt-6">
            <h3 className="text-lg font-semibold mb-4" style={{ color: COLORS.text }}>
              Confirmar Transferencia
            </h3>
            <p className="text-lightText mb-4">
              Al confirmar esta transferencia, se actualizarán automáticamente los inventarios 
              de ambos depósitos y se enviarán notificaciones a los reponedores correspondientes.
            </p>
            
            <div className="mb-4">
              <label className="block mb-2 font-medium" style={{ color: COLORS.text }}>
                Observaciones adicionales (opcional)
              </label>
              <textarea
                className="w-full px-4 py-3 border border-border rounded-xl"
                rows={3}
                value={observacionesConfirmacion}
                onChange={(e) => setObservacionesConfirmacion(e.target.value)}
                placeholder="Observaciones sobre la confirmación..."
              />
            </div>
            
            <div className="flex gap-4">
              <button
                onClick={handleConfirmar}
                disabled={confirmando}
                className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
              >
                {confirmando ? 'Confirmando...' : '✓ Confirmar Transferencia'}
              </button>
              
              <button
                onClick={() => router.push(`/inventario/transferencias/${transferencia.id}/editar`)}
                className="px-6 py-3 border border-primary text-primary rounded-lg hover:bg-primary hover:text-white transition-colors"
              >
                ✏️ Editar
              </button>
            </div>
          </div>
        )}
      </Card>
    </Container>
  );
}