"use client";
import React, { useState, useEffect } from "react";
import { COLORS } from "@/constants/colors";
import Button from "@/components/ui/Button";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import { useToast } from "@/components/feedback/ToastProvider";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import {
  obtenerOfertas,
  eliminarOferta,
  toggleActivarOferta,
  obtenerEstadisticasOfertas,
  type OfertaList,
  type EstadisticasOfertas
} from "@/lib/api";

// Mapear estado a color y etiqueta
function getEstadoInfo(estado: 'proxima' | 'activa' | 'expirada') {
  switch (estado) {
    case 'activa':
      return { color: 'text-green-600', bg: 'bg-green-100', label: 'Activa' };
    case 'proxima':
      return { color: 'text-blue-600', bg: 'bg-blue-100', label: 'Próxima' };
    case 'expirada':
      return { color: 'text-red-600', bg: 'bg-red-100', label: 'Expirada' };
    default:
      return { color: 'text-gray-600', bg: 'bg-gray-100', label: 'Desconocido' };
  }
}

// Componente para cada oferta en la lista
function OfertaListItem({ oferta, onEdit, onDelete, onToggleActivo }: {
  oferta: OfertaList;
  onEdit: () => void;
  onDelete: () => void;
  onToggleActivo: () => void;
}) {
  const estadoInfo = getEstadoInfo(oferta.estado);
  
  return (
    <div className="border border-border rounded-xl p-4 bg-white mb-3">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="font-semibold text-text text-lg">{oferta.nombre}</h3>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${estadoInfo.color} ${estadoInfo.bg}`}>
              {estadoInfo.label}
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm text-lightText">
            <div>
              <span className="font-medium">Tipo:</span> {oferta.tipo_descuento_display}
            </div>
            <div>
              <span className="font-medium">Valor:</span> {oferta.tipo_descuento === 'porcentaje' ? `${oferta.valor_descuento}%` : `$${oferta.valor_descuento}`}
            </div>
            <div>
              <span className="font-medium">Inicio:</span> {new Date(oferta.fecha_inicio).toLocaleDateString()}
            </div>
            <div>
              <span className="font-medium">Fin:</span> {new Date(oferta.fecha_fin).toLocaleDateString()}
            </div>
          </div>
        </div>
        
        <div className="flex gap-2 ml-4">
          {oferta.puede_editar && (
            <Button variant="ghost" size="sm" onClick={onEdit}>
              Editar
            </Button>
          )}
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onToggleActivo}
            className={oferta.activo ? "text-orange-600" : "text-green-600"}
          >
            {oferta.activo ? 'Desactivar' : 'Activar'}
          </Button>
          <Button variant="ghost" size="sm" onClick={onDelete} className="text-red-600">
            Eliminar
          </Button>
        </div>
      </div>
    </div>
  );
}

// Componente de filtros
function FiltrosOfertas({ 
  filtroEstado, 
  onFiltroEstadoChange, 
  estadisticas 
}: {
  filtroEstado: string;
  onFiltroEstadoChange: (estado: string) => void;
  estadisticas: EstadisticasOfertas | null;
}) {
  const filtros = [
    { value: '', label: 'Todas', count: estadisticas?.total || 0 },
    { value: 'activa', label: 'Activas', count: estadisticas?.activas || 0 },
    { value: 'proxima', label: 'Próximas', count: estadisticas?.proximas || 0 },
    { value: 'expirada', label: 'Expiradas', count: estadisticas?.expiradas || 0 }
  ];

  return (
    <div className="flex gap-2 mb-4">
      {filtros.map((filtro) => (
        <button
          key={filtro.value}
          onClick={() => onFiltroEstadoChange(filtro.value)}
          className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
            filtroEstado === filtro.value
              ? 'bg-primary text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {filtro.label} ({filtro.count})
        </button>
      ))}
    </div>
  );
}

export default function OfertasPage() {
  const { token } = useAuth();
  const { showToast } = useToast();
  const router = useRouter();
  
  const [ofertas, setOfertas] = useState<OfertaList[]>([]);
  const [estadisticas, setEstadisticas] = useState<EstadisticasOfertas | null>(null);
  const [cargando, setCargando] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState<string>('');

  // Cargar ofertas
  const cargarOfertas = async () => {
    if (!token) return;
    
    try {
      setCargando(true);
      const filtros = filtroEstado ? { estado: filtroEstado as any } : undefined;
      const response = await obtenerOfertas(token, 1, filtros);
      setOfertas(response.results);
    } catch (error) {
      console.error('Error cargando ofertas:', error);
      showToast('Error al cargar ofertas', 'error');
    } finally {
      setCargando(false);
    }
  };

  // Cargar estadísticas
  const cargarEstadisticas = async () => {
    if (!token) return;
    
    try {
      const stats = await obtenerEstadisticasOfertas(token);
      setEstadisticas(stats);
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    }
  };

  // Efectos
  useEffect(() => {
    if (token) {
      cargarEstadisticas();
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      cargarOfertas();
    }
  }, [token, filtroEstado]);

  // Handlers
  const handleEliminar = async (id: number, nombre: string) => {
    if (!token) return;
    
    if (!confirm(`¿Estás seguro de que quieres eliminar la oferta "${nombre}"?`)) {
      return;
    }
    
    try {
      await eliminarOferta(id, token);
      showToast('Oferta eliminada correctamente', 'success');
      cargarOfertas();
      cargarEstadisticas();
    } catch (error) {
      console.error('Error eliminando oferta:', error);
      showToast('Error al eliminar oferta', 'error');
    }
  };

  const handleToggleActivo = async (id: number) => {
    if (!token) return;
    
    try {
      const response = await toggleActivarOferta(id, token);
      showToast(response.message, 'success');
      cargarOfertas();
      cargarEstadisticas();
    } catch (error) {
      console.error('Error cambiando estado de oferta:', error);
      showToast('Error al cambiar estado de la oferta', 'error');
    }
  };

  const handleEditar = (id: number) => {
    router.push(`/ofertas/${id}/editar`);
  };

  // Por ahora simplemente verificamos que tenga token (está autenticado)
  // En una implementación completa, verificaríamos el tipo de usuario

  return (
    <ProtectedRoute>
      <Container>
        <Card>
          <div style={{ paddingBottom: 12, borderBottom: `1px solid ${COLORS.border}`, marginBottom: 12 }}>
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold text-text">Gestión de Ofertas</h1>
              <div className="flex gap-2">
                <Button 
                  variant="secondary"
                  onClick={() => router.push('/ofertas/productos')}
                >
                  Aplicar a Productos
                </Button>
                <Button onClick={() => router.push('/ofertas/nueva')}>
                  + Crear Nueva Oferta
                </Button>
              </div>
            </div>
          </div>

          <FiltrosOfertas
            filtroEstado={filtroEstado}
            onFiltroEstadoChange={setFiltroEstado}
            estadisticas={estadisticas}
          />

          {cargando ? (
            <div className="text-center p-8">
              <p className="text-lightText">Cargando ofertas...</p>
            </div>
          ) : ofertas.length === 0 ? (
            <div className="text-center p-8">
              <p className="text-lightText">
                {filtroEstado ? `No hay ofertas ${filtroEstado}s` : 'No hay ofertas creadas'}
              </p>
              {!filtroEstado && (
                <Button 
                  onClick={() => router.push('/ofertas/nueva')} 
                  className="mt-4"
                >
                  Crear Primera Oferta
                </Button>
              )}
            </div>
          ) : (
            <div>
              {ofertas.map((oferta) => (
                <OfertaListItem
                  key={oferta.id}
                  oferta={oferta}
                  onEdit={() => handleEditar(oferta.id)}
                  onDelete={() => handleEliminar(oferta.id, oferta.nombre)}
                  onToggleActivo={() => handleToggleActivo(oferta.id)}
                />
              ))}
            </div>
          )}
        </Card>
      </Container>
    </ProtectedRoute>
  );
}


