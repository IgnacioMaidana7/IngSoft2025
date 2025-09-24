// Tipos para el sistema de transferencias de productos

export interface Deposito {
  id: number;
  nombre: string;
  direccion: string;
  descripcion?: string;
  activo: boolean;
  fecha_creacion: string;
  fecha_modificacion: string;
}

export interface Producto {
  id: number;
  nombre: string;
  categoria: {
    id: number;
    nombre: string;
  };
  precio: string;
  descripcion?: string;
  activo: boolean;
}

export interface ProductoStock {
  id: number;
  producto: Producto;
  deposito: Deposito;
  cantidad: number;
  cantidad_minima: number;
}

export interface DetalleTransferencia {
  id?: number;
  producto: number;
  producto_nombre?: string;
  producto_categoria?: string;
  cantidad: number;
}

export interface Transferencia {
  id?: number;
  deposito_origen: number;
  deposito_origen_nombre?: string;
  deposito_destino: number;
  deposito_destino_nombre?: string;
  administrador?: number;
  administrador_nombre?: string;
  fecha_transferencia: string;
  estado: 'PENDIENTE' | 'CONFIRMADA' | 'CANCELADA';
  observaciones?: string;
  detalles: DetalleTransferencia[];
  fecha_creacion?: string;
  fecha_modificacion?: string;
}

export interface TransferenciaList {
  id: number;
  deposito_origen_nombre: string;
  deposito_destino_nombre: string;
  fecha_transferencia: string;
  estado: 'PENDIENTE' | 'CONFIRMADA' | 'CANCELADA';
  total_productos: number;
}

export interface HistorialMovimiento {
  id: number;
  fecha: string;
  tipo_movimiento: 'TRANSFERENCIA' | 'INGRESO' | 'EGRESO' | 'AJUSTE' | 'VENTA';
  tipo_movimiento_display: string;
  producto: number;
  producto_nombre: string;
  producto_categoria: string;
  deposito_origen?: number;
  deposito_origen_nombre?: string;
  deposito_destino?: number;
  deposito_destino_nombre?: string;
  cantidad: number;
  transferencia?: number;
  detalle_transferencia?: number;
  administrador_nombre: string;
  observaciones?: string;
  fecha_creacion: string;
}

export interface ConfirmarTransferencia {
  observaciones?: string;
}

// Tipos para formularios
export interface TransferenciaForm {
  deposito_origen: number | '';
  deposito_destino: number | '';
  fecha_transferencia: string;
  observaciones?: string;
  detalles: DetalleTransferenciaForm[];
}

export interface DetalleTransferenciaForm {
  producto: number | '';
  cantidad: number | '';
  producto_nombre?: string;
  stock_disponible?: number;
}

// Tipos para filtros
export interface FiltrosHistorial {
  deposito?: number;
  tipo?: string;
  producto?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
}

// Tipos para respuestas de API
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  errors?: Record<string, string[]>;
  message?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// Estados para formularios
export interface TransferenciaFormErrors {
  deposito_origen?: string[];
  deposito_destino?: string[];
  fecha_transferencia?: string[];
  observaciones?: string[];
  detalles?: Record<number, {
    producto?: string[];
    cantidad?: string[];
  }>;
  non_field_errors?: string[];
}

export interface DepositoOption {
  value: number;
  label: string;
  direccion?: string;
}

export interface ProductoOption {
  value: number;
  label: string;
  categoria: string;
  stock_disponible?: number;
}