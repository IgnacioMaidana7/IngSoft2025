"use client";
import React, { useState, useEffect } from "react";
import { COLORS } from "@/constants/colors";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/feedback/ToastProvider";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { useAuth } from "@/context/AuthContext";
import {
  obtenerHistorialVentas,
  descargarTicketHistorial,
  type HistorialVenta,
  type HistorialVentasResponse,
  type HistorialVentasFiltros
} from "@/lib/api";

interface FiltrosFormData {
  estado: string;
  fecha_desde: string;
  fecha_hasta: string;
  cajero: string;
}

export default function HistorialVentas() {
  const [historial, setHistorial] = useState<HistorialVentasResponse | null>(null);
  const [cargando, setCargando] = useState(false);
  const [descargando, setDescargando] = useState<number | null>(null);
  const [filtros, setFiltros] = useState<FiltrosFormData>({
    estado: "",
    fecha_desde: "",
    fecha_hasta: "",
    cajero: ""
  });
  const [paginaActual, setPaginaActual] = useState(1);
  const [tamañoPagina] = useState(20);

  const { showToast } = useToast();
  const { token } = useAuth();

  // Cargar historial inicial
  useEffect(() => {
    if (token) {
      cargarHistorial();
    }
  }, [token, paginaActual]);

  const cargarHistorial = async (nuevosFiltros?: Partial<HistorialVentasFiltros>) => {
    if (!token) return;

    try {
      setCargando(true);
      
      const filtrosApi: HistorialVentasFiltros = {
        ...nuevosFiltros,
        page: nuevosFiltros?.page || paginaActual,
        page_size: tamañoPagina
      };

      // Solo agregar filtros que tengan valor
      if (filtros.estado) filtrosApi.estado = filtros.estado;
      if (filtros.fecha_desde) filtrosApi.fecha_desde = filtros.fecha_desde;
      if (filtros.fecha_hasta) filtrosApi.fecha_hasta = filtros.fecha_hasta;
      if (filtros.cajero) filtrosApi.cajero = filtros.cajero;

      const resultado = await obtenerHistorialVentas(filtrosApi, token);
      setHistorial(resultado);
    } catch (error) {
      console.error("Error cargando historial:", error);
      showToast("Error al cargar el historial de ventas", "error");
    } finally {
      setCargando(false);
    }
  };

  const handleFiltroChange = (campo: keyof FiltrosFormData, valor: string) => {
    setFiltros(prev => ({ ...prev, [campo]: valor }));
  };

  const aplicarFiltros = () => {
    setPaginaActual(1);
    cargarHistorial({ page: 1 });
  };

  const limpiarFiltros = () => {
    setFiltros({
      estado: "",
      fecha_desde: "",
      fecha_hasta: "",
      cajero: ""
    });
    setPaginaActual(1);
    cargarHistorial({ 
      page: 1,
      estado: undefined,
      fecha_desde: undefined,
      fecha_hasta: undefined,
      cajero: undefined
    });
  };

  const cambiarPagina = (nuevaPagina: number) => {
    setPaginaActual(nuevaPagina);
  };

  const descargarPDF = async (ventaId: number) => {
    if (!token) return;

    try {
      setDescargando(ventaId);
      await descargarTicketHistorial(ventaId, token);
      showToast("Ticket descargado exitosamente", "success");
    } catch (error) {
      console.error("Error descargando PDF:", error);
      showToast("Error al descargar el ticket", "error");
    } finally {
      setDescargando(null);
    }
  };

  const formatearEstado = (estado: string) => {
    const estados = {
      'PENDIENTE': { texto: 'Pendiente', color: 'text-yellow-600 bg-yellow-100' },
      'PROCESANDO': { texto: 'Procesando', color: 'text-blue-600 bg-blue-100' },
      'COMPLETADA': { texto: 'Completada', color: 'text-green-600 bg-green-100' },
      'CANCELADA': { texto: 'Cancelada', color: 'text-red-600 bg-red-100' },
    };
    return estados[estado as keyof typeof estados] || { texto: estado, color: 'text-gray-600 bg-gray-100' };
  };

  return (
    <Container>
      <div className="space-y-6">
        {/* Encabezado */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Historial de Ventas</h1>
            <p className="text-gray-600 mt-1">
              Gestiona y descarga el historial completo de ventas del supermercado
            </p>
          </div>
        </div>

        {/* Filtros */}
        <Card>
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Filtros de búsqueda</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Filtro por estado */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Estado
                </label>
                <select
                  value={filtros.estado}
                  onChange={(e) => handleFiltroChange('estado', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value="">Todos los estados</option>
                  <option value="PENDIENTE">Pendiente</option>
                  <option value="PROCESANDO">Procesando</option>
                  <option value="COMPLETADA">Completada</option>
                  <option value="CANCELADA">Cancelada</option>
                </select>
              </div>

              {/* Fecha desde */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Desde
                </label>
                <input
                  type="date"
                  value={filtros.fecha_desde}
                  onChange={(e) => handleFiltroChange('fecha_desde', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              {/* Fecha hasta */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hasta
                </label>
                <input
                  type="date"
                  value={filtros.fecha_hasta}
                  onChange={(e) => handleFiltroChange('fecha_hasta', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              {/* Cajero */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cajero
                </label>
                <input
                  type="text"
                  placeholder="Nombre del cajero..."
                  value={filtros.cajero}
                  onChange={(e) => handleFiltroChange('cajero', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
            </div>

            {/* Botones de filtros */}
            <div className="flex gap-3 mt-4">
              <Button onClick={aplicarFiltros} disabled={cargando}>
                {cargando ? "Buscando..." : "Aplicar Filtros"}
              </Button>
              <Button variant="secondary" onClick={limpiarFiltros}>
                Limpiar
              </Button>
            </div>
          </div>
        </Card>

        {/* Lista de ventas */}
        <Card>
          <div className="p-6">
            {/* Información de paginación */}
            {historial && (
              <div className="flex justify-between items-center mb-4">
                <p className="text-sm text-gray-600">
                  Mostrando {historial.results.length} de {historial.count} ventas
                </p>
                <p className="text-sm text-gray-600">
                  Página {historial.current_page} de {historial.num_pages}
                </p>
              </div>
            )}

            {/* Tabla de ventas */}
            {cargando ? (
              <div className="text-center py-12">
                <div className="inline-flex items-center gap-2 text-gray-600">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Cargando historial...
                </div>
              </div>
            ) : !historial || historial.results.length === 0 ? (
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-gray-600 text-lg">No hay ventas que mostrar</p>
                <p className="text-gray-500 mt-1">Intenta ajustar los filtros de búsqueda</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        N° Venta
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cajero
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cliente
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Fecha
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {historial.results.map((venta) => {
                      const estadoInfo = formatearEstado(venta.estado);
                      return (
                        <tr key={venta.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {venta.numero_venta}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {venta.cajero_nombre}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {venta.cliente_telefono || "-"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {venta.fecha_formateada}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {venta.total_formateado}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${estadoInfo.color}`}>
                              {estadoInfo.texto}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            {venta.ticket_pdf_generado && venta.estado === 'COMPLETADA' ? (
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => descargarPDF(venta.id)}
                                disabled={descargando === venta.id}
                                icon={descargando === venta.id ? (
                                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                    <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                  </svg>
                                ) : (
                                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                                  </svg>
                                )}
                              >
                                {descargando === venta.id ? "Descargando..." : "PDF"}
                              </Button>
                            ) : (
                              <span className="text-gray-400 text-sm">-</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Paginación */}
            {historial && historial.num_pages > 1 && (
              <div className="flex items-center justify-between mt-6">
                <div className="flex justify-between flex-1 sm:hidden">
                  <Button
                    variant="secondary"
                    disabled={!historial.has_previous}
                    onClick={() => cambiarPagina(paginaActual - 1)}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="secondary"
                    disabled={!historial.has_next}
                    onClick={() => cambiarPagina(paginaActual + 1)}
                  >
                    Siguiente
                  </Button>
                </div>
                
                <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Mostrando página{" "}
                      <span className="font-medium">{historial.current_page}</span> de{" "}
                      <span className="font-medium">{historial.num_pages}</span>
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      disabled={!historial.has_previous}
                      onClick={() => cambiarPagina(paginaActual - 1)}
                    >
                      Anterior
                    </Button>
                    
                    {/* Números de página */}
                    <div className="flex gap-1">
                      {Array.from({ length: Math.min(5, historial.num_pages) }, (_, i) => {
                        const pageNum = Math.max(1, Math.min(
                          historial.num_pages - 4,
                          Math.max(1, paginaActual - 2)
                        )) + i;
                        
                        if (pageNum > historial.num_pages) return null;
                        
                        return (
                          <button
                            key={pageNum}
                            onClick={() => cambiarPagina(pageNum)}
                            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                              pageNum === paginaActual
                                ? 'bg-primary text-white'
                                : 'text-gray-700 hover:bg-gray-100'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                    </div>
                    
                    <Button
                      variant="secondary"
                      disabled={!historial.has_next}
                      onClick={() => cambiarPagina(paginaActual + 1)}
                    >
                      Siguiente
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </Container>
  );
}