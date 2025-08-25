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
  return apiFetch<AuthResponse>('/api/auth/login/', {
    method: 'POST',
    body: { email: data.email, password: data.password }
  });
}


