# Sistema de Gestión - AppProductos

Sistema integral para gestión de inventario, productos, ventas y empleados desarrollado con Next.js y TypeScript.

## Características

- 🔐 **Autenticación**: Sistema de login/registro con protección de rutas
- 📦 **Inventario**: Control de stock y gestión de depósitos
- 🏷️ **Productos**: Catálogo completo con precios y categorías
- 🛒 **Ventas**: Procesamiento de ventas con integración WhatsApp
- 🎁 **Ofertas**: Sistema de promociones especiales
- 👥 **Empleados**: Gestión de personal y permisos
- 📸 **Cámara**: Escáner de códigos integrado
- 📱 **PWA**: Funciona offline como aplicación móvil

## Tecnologías

- **Frontend**: Next.js 15, React 19, TypeScript
- **Estilos**: Tailwind CSS
- **Estado**: Context API
- **Autenticación**: JWT (preparado para backend)
- **PWA**: Service Worker integrado

## Instalación

1. Clona el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd Ing_Calidad_SFW
```

2. Instala las dependencias:
```bash
npm install
```

3. Ejecuta el servidor de desarrollo:
```bash
npm run dev
```

4. Abre [http://localhost:3000](http://localhost:3000) en tu navegador.

## Estructura del Proyecto

```
src/
├── app/                    # Rutas de la aplicación (App Router)
│   ├── (auth)/            # Rutas de autenticación
│   ├── ventas/            # Módulo de ventas
│   ├── productos/         # Módulo de productos
│   ├── inventario/        # Módulo de inventario
│   ├── ofertas/           # Módulo de ofertas
│   ├── empleados/         # Módulo de empleados
│   └── camera/            # Módulo de cámara
├── components/            # Componentes reutilizables
│   ├── auth/             # Componentes de autenticación
│   ├── common/           # Componentes comunes
│   ├── feature/          # Componentes específicos
│   ├── feedback/         # Toasts y notificaciones
│   ├── layout/           # Componentes de layout
│   └── ui/               # Componentes de interfaz
├── context/              # Contextos de React
├── lib/                  # Utilidades y API
└── constants/            # Constantes de la aplicación
```

## Autenticación

El sistema incluye:
- Página de login con validación
- Página de registro con datos de ubicación
- Protección automática de rutas
- Persistencia de sesión en localStorage
- Botón de logout en la navegación

## Conexión con Backend (Opcional)

El proyecto está preparado para conectarse a un backend Django:

1. Crea `.env.local` y configura:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

2. Los endpoints esperados son:
   - `POST /auth/login/` - Autenticación
   - `POST /auth/register/` - Registro
   - `POST /api/photos/` - Subida de fotos

## Scripts Disponibles

- `npm run dev` - Servidor de desarrollo
- `npm run build` - Build de producción
- `npm run start` - Servidor de producción
- `npm run lint` - Linter ESLint

## Funcionalidades Principales

### Ventas
- Creación de tickets de venta
- Integración con WhatsApp para envío de comprobantes
- Gestión de productos en el carrito

### Inventario
- Control de stock por depósito
- Transferencias entre depósitos
- Historial de movimientos

### Productos
- Catálogo completo con búsqueda
- Gestión de precios y categorías
- Códigos de barras

### Ofertas
- Creación de promociones
- Descuentos por porcentaje o monto fijo
- Vigencia temporal

### Empleados
- Gestión de personal
- Asignación de permisos
- Control de acceso

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.