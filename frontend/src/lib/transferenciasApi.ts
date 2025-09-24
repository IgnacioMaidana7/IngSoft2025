import { apiFetch } from './api';
import type { 
  Transferencia, 
  TransferenciaList, 
  TransferenciaForm, 
  HistorialMovimiento, 
  ConfirmarTransferencia, 
  FiltrosHistorial, 
  ApiResponse, 
  ProductoStock,
  PaginatedResponse 
} from '@/types/transferencias';

// ===== TRANSFERENCIAS API =====

export async function obtenerTransferencias(token: string): Promise<TransferenciaList[]> {
  const resp = await apiFetch<PaginatedResponse<TransferenciaList> | TransferenciaList[]>(`/api/inventario/transferencias/`, {
    method: 'GET',
    token
  });
  if (Array.isArray(resp)) return resp;
  return resp.results || [];
}

export async function obtenerTransferencia(id: number, token: string): Promise<Transferencia> {
  return apiFetch<Transferencia>(`/api/inventario/transferencias/${id}/`, {
    method: 'GET',
    token
  });
}

export async function crearTransferencia(data: TransferenciaForm, token: string): Promise<Transferencia> {
  return apiFetch<Transferencia>(`/api/inventario/transferencias/`, {
    method: 'POST',
    body: data,
    token
  });
}

export async function actualizarTransferencia(id: number, data: Partial<TransferenciaForm>, token: string): Promise<Transferencia> {
  return apiFetch<Transferencia>(`/api/inventario/transferencias/${id}/`, {
    method: 'PUT',
    body: data,
    token
  });
}

export async function eliminarTransferencia(id: number, token: string): Promise<void> {
  return apiFetch<void>(`/api/inventario/transferencias/${id}/`, {
    method: 'DELETE',
    token
  });
}

export async function confirmarTransferencia(id: number, data: ConfirmarTransferencia, token: string): Promise<ApiResponse<Transferencia>> {
  return apiFetch<ApiResponse<Transferencia>>(`/api/inventario/transferencias/${id}/confirmar/`, {
    method: 'POST',
    body: data,
    token
  });
}

export async function obtenerHistorialMovimientos(token: string, filtros?: FiltrosHistorial): Promise<HistorialMovimiento[]> {
  let queryParams = '';
  if (filtros) {
    const params = new URLSearchParams();
    if (filtros.deposito) params.append('deposito', filtros.deposito.toString());
    if (filtros.tipo) params.append('tipo', filtros.tipo);
    if (filtros.producto) params.append('producto', filtros.producto.toString());
    if (filtros.fecha_desde) params.append('fecha_desde', filtros.fecha_desde);
    if (filtros.fecha_hasta) params.append('fecha_hasta', filtros.fecha_hasta);
    queryParams = params.toString() ? `?${params.toString()}` : '';
  }
  
  const resp = await apiFetch<PaginatedResponse<HistorialMovimiento> | HistorialMovimiento[]>(`/api/inventario/historial-movimientos/${queryParams}`, {
    method: 'GET',
    token
  });
  if (Array.isArray(resp)) return resp;
  return resp.results || [];
}

export async function descargarRemitoPDF(id: number, token: string): Promise<{ blob: Blob; filename: string }> {
  const response = await apiFetch<{
    success: boolean;
    pdf_data: string;
    filename: string;
  }>(`/api/inventario/transferencias/${id}/remito/`, {
    method: 'GET',
    token
  });

  if (!response.success) {
    throw new Error('Error al generar el remito PDF');
  }

  // Convertir base64 a Blob
  const binaryData = atob(response.pdf_data);
  const bytes = new Uint8Array(binaryData.length);
  for (let i = 0; i < binaryData.length; i++) {
    bytes[i] = binaryData.charCodeAt(i);
  }
  
  const blob = new Blob([bytes], { type: 'application/pdf' });
  
  return {
    blob,
    filename: response.filename
  };
}

export async function obtenerProductosConStock(depositoId: number, token: string): Promise<ProductoStock[]> {
  const resp = await apiFetch<ProductoStock[]>(`/api/inventario/depositos/${depositoId}/productos/`, {
    method: 'GET',
    token
  });
  
  return resp;
}

// Reutilizar funciones existentes del api.ts principal
export { obtenerDepositos, obtenerDepositosDisponibles } from './api';