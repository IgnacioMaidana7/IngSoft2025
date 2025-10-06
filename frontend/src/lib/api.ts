export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export async function apiFetch<TResponse>(
  path: string,
  options: {
    method?: HttpMethod;
    body?: unknown;
    token?: string | null;
    headers?: Record<string, string>;
    isMultipart?: boolean;
  } = {}
): Promise<TResponse> {
  const { method = "GET", body, token, headers = {}, isMultipart = false } = options;

  const finalHeaders: Record<string, string> = {
    ...(isMultipart ? {} : { "Content-Type": "application/json" }),
    ...headers,
  };

  if (token) finalHeaders["Authorization"] = `Bearer ${token}`;

  if (!API_BASE_URL) {
    throw new Error("Backend no configurado. Define NEXT_PUBLIC_API_BASE_URL para habilitar la conexión.");
  }

  const response = await fetch(`${API_BASE_URL}${path}`,
    {
      method,
      headers: finalHeaders,
      body: ((): BodyInit | undefined => {
        if (body == null) return undefined;
        return isMultipart ? (body as BodyInit) : (JSON.stringify(body) as BodyInit);
      })(),
      credentials: "include",
    }
  );

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    
    try {
      const errorData = await response.json();
      
      // Si es un error de validación de Django (400), extraer los mensajes
      if (response.status === 400 && errorData) {
        const errorMessages = [];
        
        // Manejar errores de campo específicos
        for (const [field, messages] of Object.entries(errorData)) {
          if (Array.isArray(messages)) {
            errorMessages.push(`${field}: ${messages.join(', ')}`);
          } else if (typeof messages === 'string') {
            errorMessages.push(`${field}: ${messages}`);
          }
        }
        
        if (errorMessages.length > 0) {
          errorMessage = errorMessages.join('\n');
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // Si no se puede parsear JSON, usar el status por defecto
    }
    
    throw new Error(errorMessage);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as TResponse;
  }
  return (await response.text()) as unknown as TResponse;
}

export async function downloadFile(
  path: string,
  options: {
    token?: string | null;
    headers?: Record<string, string>;
  } = {}
): Promise<Blob> {
  const { token, headers = {} } = options;

  const finalHeaders: Record<string, string> = {
    ...headers,
  };

  if (token) finalHeaders["Authorization"] = `Bearer ${token}`;

  if (!API_BASE_URL) {
    throw new Error("Backend no configurado. Define NEXT_PUBLIC_API_BASE_URL para habilitar la conexión.");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'GET',
    headers: finalHeaders,
    credentials: "include",
  });

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    
    try {
      const errorData = await response.json();
      
      // Si es un error de validación de Django (400), extraer los mensajes
      if (response.status === 400 && errorData) {
        const errorMessages: string[] = [];
        
        // Manejar errores de campo específicos
        if (typeof errorData === 'object') {
          Object.entries(errorData).forEach(([field, messages]) => {
            if (Array.isArray(messages)) {
              errorMessages.push(`${field}: ${messages.join(', ')}`);
            } else {
              errorMessages.push(`${field}: ${messages}`);
            }
          });
        }
        
        if (errorMessages.length > 0) {
          errorMessage = errorMessages.join('; ');
        }
      } else if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // Si no se puede parsear como JSON, usar el status por defecto
    }
    
    throw new Error(`Error descargando archivo: ${errorMessage}`);
  }

  return response.blob();
}

export async function uploadPhoto(
  file: File,
  token?: string | null
): Promise<{ id: string; url: string }>
{
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch("/api/photos/", { method: "POST", body: formData, token: token ?? null, isMultipart: true });
}

// Funciones de autenticación para supermercados
export interface RegisterSupermercadoData {
  username: string;
  password: string;
  nombre_supermercado: string;
  cuil: string;
  email: string;
  provincia: string;
  localidad: string;
  logo?: File;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    username: string;
    email: string;
    nombre_supermercado: string;
    cuil: string;
    provincia: string;
    localidad: string;
    logo?: string;
  };
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function registerSupermercado(data: RegisterSupermercadoData): Promise<AuthResponse> {
  const formData = new FormData();
  
  // Agregar datos del formulario
  formData.append('username', data.username);
  formData.append('password', data.password);
  formData.append('password_confirm', data.password); // Agregar confirmación de contraseña
  formData.append('nombre_supermercado', data.nombre_supermercado);
  formData.append('cuil', data.cuil);
  formData.append('email', data.email);
  formData.append('provincia', data.provincia);
  formData.append('localidad', data.localidad);
  
  // Agregar logo si existe
  if (data.logo) {
    formData.append('logo', data.logo);
  }

  return apiFetch<AuthResponse>('/api/auth/register/', {
    method: 'POST',
    body: formData,
    isMultipart: true
  });
}

export async function loginSupermercado(data: LoginData): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/api/auth/supermercado/login/', {
    method: 'POST',
    body: { email: data.email, password: data.password }
  });
}

// Función de login para empleados
export interface EmpleadoLoginData {
  email: string;
  dni: string;
}

export interface EmpleadoAuthResponse {
  message: string;
  refresh: string;
  access: string;
  user: {
    id: number;
    email: string;
    nombre: string;
    apellido: string;
    nombre_completo: string;
    dni: string;
    puesto: 'CAJERO' | 'REPONEDOR';
    supermercado_nombre: string;
    fecha_registro: string;
    is_active: boolean;
  };
  user_type: 'empleado';
}

export async function loginEmpleado(data: EmpleadoLoginData): Promise<EmpleadoAuthResponse> {
  return apiFetch<EmpleadoAuthResponse>('/api/auth/empleado/login/', {
    method: 'POST',
    body: { email: data.email, dni: data.dni }
  });
}

// Obtener perfil del empleado logueado
export async function obtenerPerfilEmpleado(token: string): Promise<EmpleadoAuthResponse['user']> {
  return apiFetch<EmpleadoAuthResponse['user']>('/api/auth/empleado/profile/', {
    method: 'GET',
    token
  });
}

// Interfaces para empleados y depósitos
export interface Deposito {
  id: number;
  nombre: string;
  direccion: string;
  descripcion?: string;
  activo: boolean;
  fecha_creacion: string;
  fecha_modificacion: string;
}

export interface DepositoCreate {
  nombre: string;
  direccion: string;
  descripcion?: string;
}

export interface Empleado {
  id: number;
  nombre: string;
  apellido: string;
  email: string;
  dni: string;
  puesto: 'CAJERO' | 'REPONEDOR';
  deposito: number;
  deposito_nombre: string;
  nombre_completo: string;
  activo: boolean;
  fecha_ingreso: string;
  fecha_modificacion: string;
}

export interface EmpleadoCreate {
  nombre: string;
  apellido: string;
  email: string;
  dni: string;
  puesto: 'CAJERO' | 'REPONEDOR';
  deposito: number;
  password?: string;
}

export interface Role {
  value: string;
  label: string;
}

export interface EstadisticasEmpleados {
  total_empleados: number;
  empleados_por_puesto: Record<string, number>;
  empleados_por_deposito: Record<string, number>;
}

// Funciones para gestión de depósitos
export async function obtenerDepositos(token: string): Promise<Deposito[]> {
  console.log('obtenerDepositos - Iniciando solicitud a API');
  try {
    const result = await apiFetch<{count: number, results: Deposito[]}>('/api/inventario/depositos/', {
      method: 'GET',
      token
    });
    console.log('obtenerDepositos - Respuesta de API:', result);
    console.log('obtenerDepositos - Results extraídos:', result.results);
    return result.results || [];
  } catch (error) {
    console.error('obtenerDepositos - Error:', error);
    throw error;
  }
}

export async function crearDeposito(data: DepositoCreate, token: string): Promise<Deposito> {
  return apiFetch<Deposito>('/api/inventario/depositos/', {
    method: 'POST',
    body: data,
    token
  });
}

export async function actualizarDeposito(id: number, data: Partial<DepositoCreate>, token: string): Promise<Deposito> {
  return apiFetch<Deposito>(`/api/inventario/depositos/${id}/`, {
    method: 'PUT',
    body: data,
    token
  });
}

export async function eliminarDeposito(id: number, token: string): Promise<void> {
  return apiFetch<void>(`/api/inventario/depositos/${id}/`, {
    method: 'DELETE',
    token
  });
}

export async function obtenerDeposito(id: number, token: string): Promise<Deposito> {
  return apiFetch<Deposito>(`/api/inventario/depositos/${id}/`, {
    method: 'GET',
    token
  });
}

export async function obtenerDepositosDisponibles(token: string): Promise<{ success: boolean; data: Deposito[] }> {
  return apiFetch<{ success: boolean; data: Deposito[] }>('/api/inventario/depositos/disponibles/', {
    method: 'GET',
    token
  });
}

// Obtener el depósito asignado al reponedor actual
export async function obtenerMiDeposito(token: string): Promise<Deposito> {
  return apiFetch<Deposito>('/api/inventario/mi-deposito/', {
    method: 'GET',
    token
  });
}

// Funciones para gestión de empleados
export async function obtenerEmpleados(token: string, filtros?: {
  puesto?: string;
  deposito?: number;
  search?: string;
}): Promise<Empleado[]> {
  const params = new URLSearchParams();
  if (filtros?.puesto) params.append('puesto', filtros.puesto);
  if (filtros?.deposito) params.append('deposito', filtros.deposito.toString());
  if (filtros?.search) params.append('search', filtros.search);
  
  const queryString = params.toString();
  const path = queryString ? `/api/empleados/?${queryString}` : '/api/empleados/';
  
  const result = await apiFetch<{count: number, results: Empleado[]}>(path, {
    method: 'GET',
    token
  });
  
  return result.results || [];
}

export async function obtenerEmpleado(id: number, token: string): Promise<Empleado> {
  return apiFetch<Empleado>(`/api/empleados/${id}/`, {
    method: 'GET',
    token
  });
}

export async function crearEmpleado(data: EmpleadoCreate, token: string): Promise<Empleado> {
  return apiFetch<Empleado>('/api/empleados/', {
    method: 'POST',
    body: data,
    token
  });
}

export async function actualizarEmpleado(id: number, data: Partial<EmpleadoCreate>, token: string): Promise<Empleado> {
  return apiFetch<Empleado>(`/api/empleados/${id}/`, {
    method: 'PUT',
    body: data,
    token
  });
}

export async function eliminarEmpleado(id: number, token: string): Promise<void> {
  return apiFetch<void>(`/api/empleados/${id}/`, {
    method: 'DELETE',
    token
  });
}

export async function obtenerRolesDisponibles(token: string): Promise<{ roles: Role[] }> {
  return apiFetch<{ success: boolean; roles: Role[] }>('/api/empleados/roles/', {
    method: 'GET',
    token
  });
}

export async function obtenerEstadisticasEmpleados(token: string): Promise<EstadisticasEmpleados> {
  return apiFetch<EstadisticasEmpleados>('/api/empleados/estadisticas/', {
    method: 'GET',
    token
  });
}

// === INTERFACES PARA PRODUCTOS ===

export interface Categoria {
  id: number;
  nombre: string;
  descripcion?: string;
  activo: boolean;
  fecha_creacion: string;
}

export interface CategoriaSimple {
  id: number;
  nombre: string;
}

export interface ProductoStock {
  id: number;
  deposito: number;
  deposito_nombre: string;
  deposito_direccion: string;
  cantidad: number;
  cantidad_minima: number;
  tiene_stock: boolean;
  stock_bajo: boolean;
  fecha_creacion: string;
  fecha_modificacion: string;
}

export interface Producto {
  id: number;
  nombre: string;
  categoria: number;
  categoria_nombre: string;
  precio: string;
  descripcion?: string;
  activo: boolean;
  stocks: ProductoStock[];
  stock_total: number;
  fecha_creacion: string;
  fecha_modificacion: string;
}

export interface ProductoList {
  id: number;
  nombre: string;
  categoria_nombre: string;
  precio: string;
  activo: boolean;
  stock_total: number;
  depositos_count: number;
  stock_nivel: 'sin-stock' | 'bajo' | 'normal';
  fecha_modificacion: string;
}

export interface ProductoCreate {
  nombre: string;
  categoria: number;
  precio: string;
  descripcion?: string;
  activo?: boolean;
  deposito_id?: number;
  cantidad_inicial?: number;
  cantidad_minima?: number;
}

export interface ProductoDeposito {
  id: number;
  nombre: string;
  categoria: string;
  precio: string;
  cantidad: number;
  cantidad_minima: number;
  tiene_stock: boolean;
  stock_bajo: boolean;
  stock_id: number;
}

export interface ProductosPorDeposito {
  deposito: {
    id: number;
    nombre: string;
    direccion: string;
  };
  productos: ProductoDeposito[];
}

export interface EstadisticasProductos {
  total_productos: number;
  total_categorias: number;
  productos_sin_stock: number;
  stock_por_categoria: Array<{
    categoria: string;
    stock_total: number;
    productos_count: number;
  }>;
}

// === FUNCIONES PARA CATEGORÍAS ===

export async function obtenerCategorias(token: string, page?: number): Promise<PaginatedResponse<Categoria>> {
  const url = page ? `/api/productos/categorias/?page=${page}` : '/api/productos/categorias/';
  const response = await apiFetch<PaginatedResponse<Categoria>>(url, {
    method: 'GET',
    token
  });
  
  return {
    ...response,
    results: response.results || (response as unknown as Categoria[])
  };
}

export async function obtenerCategoriasDisponibles(token: string): Promise<CategoriaSimple[]> {
  return apiFetch<CategoriaSimple[]>('/api/productos/categorias/disponibles/', {
    method: 'GET',
    token
  });
}

export async function crearCategoria(data: Omit<Categoria, 'id' | 'fecha_creacion'>, token: string): Promise<Categoria> {
  return apiFetch<Categoria>('/api/productos/categorias/', {
    method: 'POST',
    body: data,
    token
  });
}

export async function actualizarCategoria(id: number, data: Partial<Categoria>, token: string): Promise<Categoria> {
  return apiFetch<Categoria>(`/api/productos/categorias/${id}/`, {
    method: 'PUT',
    body: data,
    token
  });
}

export async function eliminarCategoria(id: number, token: string): Promise<void> {
  return apiFetch<void>(`/api/productos/categorias/${id}/`, {
    method: 'DELETE',
    token
  });
}

// === FUNCIONES PARA PRODUCTOS ===

export async function obtenerProductos(
  token: string, 
  page?: number, 
  filters?: {
    categoria?: number;
    deposito?: number;
    activo?: boolean;
    search?: string;
    stock?: string; // formato: 'sin-stock', 'bajo', 'normal'
  }
): Promise<PaginatedResponse<ProductoList>> {
  let url = '/api/productos/';
  const params = new URLSearchParams();
  
  if (page) params.append('page', page.toString());
  if (filters?.categoria) params.append('categoria', filters.categoria.toString());
  if (filters?.deposito) params.append('deposito', filters.deposito.toString());
  if (filters?.activo !== undefined) params.append('activo', filters.activo.toString());
  if (filters?.search) params.append('search', filters.search);
  if (filters?.stock) params.append('stock', filters.stock);
  
  if (params.toString()) {
    url += `?${params.toString()}`;
  }
  
  const response = await apiFetch<PaginatedResponse<ProductoList>>(url, {
    method: 'GET',
    token
  });
  
  return {
    ...response,
    results: response.results || (response as unknown as ProductoList[])
  };
}

export async function obtenerProducto(id: number, token: string): Promise<Producto> {
  return apiFetch<Producto>(`/api/productos/${id}/`, {
    method: 'GET',
    token
  });
}

export async function crearProducto(data: ProductoCreate, token: string): Promise<Producto> {
  return apiFetch<Producto>('/api/productos/', {
    method: 'POST',
    body: data,
    token
  });
}

export async function actualizarProducto(id: number, data: Partial<ProductoCreate>, token: string): Promise<Producto> {
  return apiFetch<Producto>(`/api/productos/${id}/`, {
    method: 'PATCH',
    body: data,
    token
  });
}

export async function eliminarProducto(id: number, token: string): Promise<void> {
  return apiFetch<void>(`/api/productos/${id}/`, {
    method: 'DELETE',
    token
  });
}

export async function obtenerProductosPorDeposito(depositoId: number, token: string): Promise<ProductosPorDeposito> {
  return apiFetch<ProductosPorDeposito>(`/api/productos/deposito/${depositoId}/`, {
    method: 'GET',
    token
  });
}

export async function obtenerEstadisticasProductos(token: string): Promise<EstadisticasProductos> {
  return apiFetch<EstadisticasProductos>('/api/productos/estadisticas/', {
    method: 'GET',
    token
  });
}

export async function gestionarStockProducto(
  productoId: number, 
  data: { deposito: number; cantidad: number; cantidad_minima?: number }, 
  token: string
): Promise<ProductoStock> {
  return apiFetch<ProductoStock>(`/api/productos/${productoId}/stock/`, {
    method: 'POST',
    body: data,
    token
  });
}

export async function actualizarStockProducto(
  stockId: number, 
  data: { cantidad?: number; cantidad_minima?: number }, 
  token: string
): Promise<ProductoStock> {
  return apiFetch<ProductoStock>(`/api/productos/stock/${stockId}/`, {
    method: 'PUT',
    body: data,
    token
  });
}

export interface StockCompleto {
  deposito_id: number;
  deposito_nombre: string;
  deposito_direccion: string;
  cantidad: number;
  cantidad_minima: number;
  stock_id: number | null;
  tiene_stock: boolean;
  stock_bajo: boolean;
  fecha_modificacion: string | null;
}

export interface StockCompletoResponse {
  producto: {
    id: number;
    nombre: string;
  };
  stocks: StockCompleto[];
}

export async function obtenerStockCompletoProducto(
  productoId: number,
  token: string
): Promise<StockCompletoResponse> {
  return apiFetch<StockCompletoResponse>(`/api/productos/${productoId}/stock-completo/`, {
    method: 'GET',
    token
  });
}

export interface ResultadoActualizacion {
  deposito_id: number;
  deposito_nombre?: string;
  cantidad?: number;
  cantidad_minima?: number;
  actualizado: boolean;
  error?: string;
}

export async function actualizarStockCompletoProducto(
  productoId: number,
  stocks: Array<{
    deposito_id: number;
    cantidad: number;
    cantidad_minima: number;
  }>,
  token: string
): Promise<{mensaje: string; resultados: ResultadoActualizacion[]}> {
  return apiFetch<{mensaje: string; resultados: ResultadoActualizacion[]}>(`/api/productos/${productoId}/actualizar-stock/`, {
    method: 'POST',
    body: { stocks },
    token
  });
}

// === NOTIFICACIONES ===
export interface Notificacion {
  id: number;
  titulo: string;
  mensaje: string;
  tipo: 'STOCK_MINIMO' | 'INFO' | 'ALERTA';
  leida: boolean;
  creada_en: string;
  destinatario?: { tipo: 'empleado' | 'admin'; nombre: string; email: string } | null;
}

export async function obtenerMisNotificaciones(token: string): Promise<Notificacion[]> {
  const resp = await apiFetch<PaginatedResponse<Notificacion> | Notificacion[]>(`/api/notificaciones/`, {
    method: 'GET',
    token
  });
  // backend ListAPIView con paginación global -> normalizar
  if (Array.isArray(resp)) return resp;
  return resp.results || [];
}

export async function marcarNotificacionLeida(id: number, token: string): Promise<Notificacion> {
  return apiFetch<Notificacion>(`/api/notificaciones/${id}/leida/`, {
    method: 'PUT',
    token
  });
}

// === VENTAS ===
export interface Venta {
  id: number;
  numero_venta: string;
  cajero: number;
  cajero_nombre: string;
  cliente_telefono?: string;
  subtotal: string;
  descuento: string;
  total: string;
  estado: 'PENDIENTE' | 'PROCESANDO' | 'COMPLETADA' | 'CANCELADA';
  fecha_creacion: string;
  fecha_completada?: string;
  observaciones?: string;
  ticket_pdf_generado: boolean;
  enviado_whatsapp: boolean;
  items: ItemVenta[];
  numero_items: number;
}

export interface ItemVenta {
  id: number;
  producto: number;
  producto_nombre: string;
  cantidad: number;
  precio_unitario: string;
  subtotal: string;
  fecha_agregado: string;
}

export interface ProductoDisponible {
  id: number;
  nombre: string;
  categoria: string;
  precio: string;
  descripcion?: string;
  stock_disponible: number;
}

export interface CrearVentaRequest {
  cliente_telefono?: string;
  observaciones?: string;
}

export interface AgregarProductoRequest {
  producto_id: number;
  cantidad: number;
}

export interface ActualizarItemRequest {
  item_id: number;
  cantidad: number;
}

export interface FinalizarVentaRequest {
  cliente_telefono?: string;
  observaciones?: string;
  enviar_whatsapp?: boolean;
}

// === HISTORIAL DE VENTAS ===
export interface HistorialVenta {
  id: number;
  numero_venta: string;
  cajero_nombre: string;
  empleado_cajero_nombre?: string;
  cliente_telefono?: string;
  fecha_creacion: string;
  fecha_formateada: string;
  total: string;
  total_formateado: string;
  estado: 'PENDIENTE' | 'PROCESANDO' | 'COMPLETADA' | 'CANCELADA';
  ticket_pdf_generado: boolean;
}

export interface HistorialVentasResponse {
  count: number;
  num_pages: number;
  current_page: number;
  has_next: boolean;
  has_previous: boolean;
  results: HistorialVenta[];
}

export interface HistorialVentasFiltros {
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  cajero?: string;
  page?: number;
  page_size?: number;
}

// Crear nueva venta
export async function crearVenta(data: CrearVentaRequest, token: string): Promise<Venta> {
  return apiFetch<Venta>('/api/ventas/ventas/', {
    method: 'POST',
    body: data,
    token
  });
}

// Obtener ventas del cajero
export async function obtenerVentas(token: string): Promise<Venta[]> {
  const resp = await apiFetch<PaginatedResponse<Venta> | Venta[]>('/api/ventas/ventas/', {
    method: 'GET',
    token
  });
  if (Array.isArray(resp)) return resp;
  return resp.results || [];
}

// Obtener una venta específica
export async function obtenerVenta(id: number, token: string): Promise<Venta> {
  return apiFetch<Venta>(`/api/ventas/ventas/${id}/`, {
    method: 'GET',
    token
  });
}

// Agregar producto a una venta
export async function agregarProductoAVenta(ventaId: number, data: AgregarProductoRequest, token: string): Promise<{ message: string; item: ItemVenta; venta: Venta }> {
  return apiFetch<{ message: string; item: ItemVenta; venta: Venta }>(`/api/ventas/ventas/${ventaId}/agregar_producto/`, {
    method: 'POST',
    body: data,
    token
  });
}

// Actualizar cantidad de un item en la venta
export async function actualizarItemVenta(ventaId: number, data: ActualizarItemRequest, token: string): Promise<{ message: string; item: ItemVenta; venta: Venta }> {
  return apiFetch<{ message: string; item: ItemVenta; venta: Venta }>(`/api/ventas/ventas/${ventaId}/actualizar_item/`, {
    method: 'PATCH',
    body: data,
    token
  });
}

// Eliminar item de la venta
export async function eliminarItemVenta(ventaId: number, itemId: number, token: string): Promise<{ message: string; venta: Venta }> {
  return apiFetch<{ message: string; venta: Venta }>(`/api/ventas/ventas/${ventaId}/eliminar_item/`, {
    method: 'DELETE',
    body: { item_id: itemId },
    token
  });
}

// Finalizar venta
export async function finalizarVenta(ventaId: number, data: FinalizarVentaRequest, token: string): Promise<{ message: string; venta: Venta }> {
  return apiFetch<{ message: string; venta: Venta }>(`/api/ventas/ventas/${ventaId}/finalizar/`, {
    method: 'POST',
    body: data,
    token
  });
}

// Cancelar venta
export async function cancelarVenta(ventaId: number, token: string): Promise<{ message: string; venta: Venta }> {
  return apiFetch<{ message: string; venta: Venta }>(`/api/ventas/ventas/${ventaId}/cancelar/`, {
    method: 'POST',
    token
  });
}

// Obtener productos disponibles para venta
export async function obtenerProductosDisponibles(token: string): Promise<ProductoDisponible[]> {
  return apiFetch<ProductoDisponible[]>('/api/ventas/productos-disponibles/', {
    method: 'GET',
    token
  });
}

// Buscar productos
export async function buscarProductos(query: string, token: string): Promise<ProductoDisponible[]> {
  return apiFetch<ProductoDisponible[]>(`/api/ventas/buscar-productos/?q=${encodeURIComponent(query)}`, {
    method: 'GET',
    token
  });
}

// Descargar ticket PDF (método existente)
export async function descargarTicketPDF(ventaId: number, token: string): Promise<void> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'}/api/ventas/ventas/${ventaId}/descargar_ticket/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`Error al descargar PDF: ${response.status}`);
    }

    // Crear blob y descargar archivo
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ticket_venta_${ventaId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error descargando PDF:', error);
    throw error;
  }
}

// === FUNCIONES PARA HISTORIAL DE VENTAS ===

// Obtener historial de ventas (solo para administradores)
export async function obtenerHistorialVentas(
  filtros: HistorialVentasFiltros = {},
  token: string
): Promise<HistorialVentasResponse> {
  // Construir parámetros de consulta
  const params = new URLSearchParams();
  
  if (filtros.estado) params.append('estado', filtros.estado);
  if (filtros.fecha_desde) params.append('fecha_desde', filtros.fecha_desde);
  if (filtros.fecha_hasta) params.append('fecha_hasta', filtros.fecha_hasta);
  if (filtros.cajero) params.append('cajero', filtros.cajero);
  if (filtros.page) params.append('page', filtros.page.toString());
  if (filtros.page_size) params.append('page_size', filtros.page_size.toString());

  const queryString = params.toString();
  const url = `/api/ventas/historial/${queryString ? `?${queryString}` : ''}`;

  return apiFetch<HistorialVentasResponse>(url, {
    method: 'GET',
    token
  });
}

// Descargar ticket PDF específico del historial (solo para administradores)
export async function descargarTicketHistorial(ventaId: number, token: string): Promise<void> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'}/api/ventas/ticket/${ventaId}/pdf/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Error al descargar PDF: ${response.status}`);
    }

    // Crear blob y descargar archivo
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ticket_${ventaId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error descargando PDF del historial:', error);
    throw error;
  }
}

// === RECONOCIMIENTO DE PRODUCTOS ===
export interface ProductoReconocido {
  product_id: number;
  ingsoft_product_id: number | null;
  name: string;
  display_name: string;
  category: string;
  brand: string;
  detection_confidence: number;
  classification_confidence: number;
  bbox: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    width: number;
    height: number;
  };
  // Información enriquecida desde la BD
  nombre_db?: string;
  categoria_db?: string;
  precio_db?: string;
  existe_en_bd?: boolean;
  stock_disponible?: number;
  stock_minimo?: number;
  stock_bajo?: boolean;
  mensaje?: string;
}

export interface RecognitionResponse {
  success: boolean;
  total_productos: number;
  productos: ProductoReconocido[];
  processing_time_ms: number;
  deposito_id?: number;
  error?: string;
  stock_suggestions?: any[];
}

// Reconocer productos desde una imagen
export async function reconocerProductosImagen(
  imageFile: File,
  token: string
): Promise<RecognitionResponse> {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  return apiFetch<RecognitionResponse>('/api/productos/reconocer-imagen/', {
    method: 'POST',
    body: formData,
    token,
    isMultipart: true
  });
}

// Verificar estado de la API de reconocimiento
export async function verificarApiReconocimiento(token: string): Promise<{ success: boolean; status: string; details?: any; error?: string }> {
  return apiFetch<{ success: boolean; status: string; details?: any; error?: string }>('/api/productos/verificar-api-reconocimiento/', {
    method: 'GET',
    token
  });
}

// Obtener catálogo de productos reconocibles
export async function obtenerCatalogoReconocimiento(token: string): Promise<any> {
  return apiFetch<any>('/api/productos/catalogo-reconocimiento/', {
    method: 'GET',
    token
  });
}
