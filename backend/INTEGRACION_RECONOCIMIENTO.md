# 🔧 Backend Django - Integración con Reconocimiento de Productos

Guía completa para configurar y mantener el backend de Django con el sistema de reconocimiento de productos.

---

## 📋 Tabla de Contenidos

1. [Setup Inicial](#-setup-inicial)
2. [Configuración del Reconocimiento](#-configuración-del-reconocimiento)
3. [Endpoints Implementados](#-endpoints-implementados)
4. [Agregar Nuevos Productos](#-agregar-nuevos-productos)
5. [Testing](#-testing)
6. [Troubleshooting](#-troubleshooting)

---

## 🚀 Setup Inicial

### Requisitos

- **Python**: 3.11 - 3.13
- **PostgreSQL**: 14+
- **Sistema de Reconocimiento**: Corriendo en puerto 8080

### 1. Crear Entorno Virtual

```powershell
# Navegar a la carpeta del backend
cd "C:\Users\Usuario\Documents\GitHub\IngSoft2025\IngSoft2025\backend"

# Crear entorno virtual (solo primera vez)
python -m venv backend_env

# Activar entorno virtual
.\backend_env\Scripts\Activate.ps1

# Si hay error de permisos:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\backend_env\Scripts\Activate.ps1
```

### 2. Instalar Dependencias

```powershell
# Actualizar pip
python -m pip install --upgrade pip setuptools wheel

# Instalar requirements
pip install -r requirements.txt
```

**Dependencias principales**:
- Django 4.2.7
- Django REST Framework 3.14.0
- psycopg2-binary (PostgreSQL)
- Pillow (imágenes)
- djangorestframework-simplejwt (JWT)
- django-cors-headers
- requests (para llamar API reconocimiento)

### 3. Configurar Base de Datos

**Crear archivo `.env` en `backend/`**:

```bash
# Base de datos PostgreSQL
DB_NAME=ingsoft2025_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=tu-secret-key-super-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# API de Reconocimiento
RECOGNITION_API_URL=http://localhost:8080
```

### 4. Ejecutar Migraciones

```powershell
# Verificar configuración
python manage.py check

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

### 5. Crear Superusuario

```powershell
python manage.py createsuperuser
```

### 6. Cargar Productos Iniciales

```powershell
# Comando personalizado para crear productos del reconocimiento
python manage.py crear_productos_reconocimiento
```

**Este comando**:
- Crea los productos en Django
- Actualiza `product_mapping.json` automáticamente
- Vincula shelf IDs con Django IDs

### 7. Iniciar Servidor

```powershell
python manage.py runserver
```

**Verificar**:
```
http://localhost:8000/admin/
http://localhost:8000/api/productos/
```

---

## 🎯 Configuración del Reconocimiento

### Estructura de Archivos

```
backend/
├── manage.py
├── requirements.txt
├── .env
│
├── appproductos/
│   ├── settings.py              # Configuración principal
│   └── urls.py                  # URLs principales
│
├── productos/
│   ├── models.py                # Modelo Producto
│   ├── views.py                 # Views REST
│   ├── serializers.py           # Serializers
│   ├── urls.py                  # URLs de productos
│   ├── recognition_views.py     # ← Vista de reconocimiento
│   │
│   └── management/commands/
│       └── crear_productos_reconocimiento.py  # Comando custom
│
└── authentication/
    └── ...                      # Sistema de auth JWT
```

### Configuración en `settings.py`

```python
# appproductos/settings.py

INSTALLED_APPS = [
    # ...
    'rest_framework',
    'corsheaders',
    'productos',
    'authentication',
    # ...
]

# CORS (para que el frontend pueda llamar al backend)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Frontend Next.js
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Logging (para debugging)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'productos': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

---

## 🌐 Endpoints Implementados

### 1. Reconocer Productos desde Imagen

**Endpoint**: `POST /api/productos/reconocer-imagen/`

**Headers**:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data
```

**Body** (Opción 1 - Multipart):
```
image: [archivo de imagen]
deposito_id: 1
```

**Body** (Opción 2 - JSON):
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
  "deposito_id": 1
}
```

**Response**:
```json
{
  "success": true,
  "total_products": 2,
  "products": [
    {
      "recognition_product_id": 6,
      "ingsoft_product_id": 4,
      "is_mapped_to_ingsoft": true,
      "nombre": "Raid Insecticida",
      "categoria": "Limpieza",
      "marca": "Raid",
      "precio": 1450.0,
      "detection_confidence": 0.89,
      "classification_confidence": 0.85,
      "bbox": { "x1": 120, "y1": 80, "x2": 340, "y2": 450 }
    }
  ]
}
```

**Implementación** (`productos/recognition_views.py`):
```python
import base64
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

RECOGNITION_API_URL = getattr(
    settings, 
    'RECOGNITION_API_URL', 
    'http://localhost:8080/api/recognize-ingsoft'
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reconocer_productos_imagen(request):
    """
    Reconoce productos en una imagen usando la API de reconocimiento.
    """
    try:
        # Obtener imagen
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            image_bytes = image_file.read()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            logger.info(f"📸 Imagen recibida: {image_file.name} ({len(image_bytes)} bytes)")
        elif 'image_base64' in request.data:
            image_b64 = request.data['image_base64']
            if 'base64,' in image_b64:
                image_b64 = image_b64.split('base64,')[1]
            logger.info(f"📸 Imagen base64 recibida ({len(image_b64)} chars)")
        else:
            logger.warning("⚠️ No se recibió imagen")
            return Response(
                {'error': 'Debe enviar una imagen (image o image_base64)'},
                status=400
            )
        
        # Preparar payload
        payload = {
            'image_base64': image_b64,
            'deposito_id': request.data.get('deposito_id', 1),
            'format_for_frontend': True,
            'include_stock_suggestions': False
        }
        
        # Llamar a API de reconocimiento
        logger.info(f"🔍 Enviando a API de reconocimiento: {RECOGNITION_API_URL}")
        response = requests.post(
            RECOGNITION_API_URL,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            total = result.get('total_products', 0)
            logger.info(f"✅ Reconocimiento exitoso: {total} productos detectados")
            
            # Log de cada producto
            for prod in result.get('products', []):
                logger.debug(
                    f"  - {prod.get('nombre')} "
                    f"(ID: {prod.get('ingsoft_product_id')}, "
                    f"Conf: {prod.get('detection_confidence', 0):.2f})"
                )
            
            return Response(result, status=200)
        else:
            logger.error(
                f"❌ Error en API de reconocimiento: "
                f"{response.status_code} - {response.text}"
            )
            return Response(
                {
                    'error': 'Error en el servicio de reconocimiento',
                    'details': response.text
                },
                status=response.status_code
            )
    
    except requests.exceptions.Timeout:
        logger.error("⏱️ Timeout al conectar con API de reconocimiento")
        return Response(
            {'error': 'Timeout al procesar la imagen (>60s)'},
            status=504
        )
    
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 No se pudo conectar con {RECOGNITION_API_URL}")
        return Response(
            {
                'error': 'Servicio de reconocimiento no disponible',
                'details': 'Verificar que el servidor esté corriendo en puerto 8080'
            },
            status=503
        )
    
    except Exception as e:
        logger.exception(f"💥 Error inesperado en reconocimiento")
        return Response(
            {'error': f'Error interno: {str(e)}'},
            status=500
        )
```

**URLs** (`productos/urls.py`):
```python
from django.urls import path
from . import views, recognition_views

urlpatterns = [
    # Productos CRUD
    path('', views.ProductoListCreate.as_view(), name='producto-list'),
    path('<int:pk>/', views.ProductoDetail.as_view(), name='producto-detail'),
    
    # Reconocimiento
    path('reconocer-imagen/', 
         recognition_views.reconocer_productos_imagen, 
         name='reconocer-productos'),
]
```

---

## ➕ Agregar Nuevos Productos

### Método 1: Comando de Management (Recomendado)

**1. Editar el comando** (`productos/management/commands/crear_productos_reconocimiento.py`):

```python
productos_config = [
    # ... productos existentes ...
    {
        'api_id': 7,  # ID en el sistema de reconocimiento
        'nombre': 'Nuevo Producto 500g',
        'descripcion': 'Descripción del producto - SKU: PROD-SKU-001',
        'precio': 1500.00,
        'stock': 30,
        'categoria_nombre': 'Categoría',
        'api_name': 'nuevo_producto',  # Nombre en product_catalog.json
        'sku': 'PROD-SKU-001'
    }
]
```

**2. Ejecutar comando**:

```powershell
python manage.py crear_productos_reconocimiento
```

**Esto hará**:
- Crear el producto en Django
- Asignar un ID automático
- Actualizar `product_mapping.json` en el proyecto de reconocimiento
- Mostrar resumen de cambios

### Método 2: Admin de Django

**1. Ir al admin**:
```
http://localhost:8000/admin/productos/producto/add/
```

**2. Llenar formulario**:
- Nombre: "Nuevo Producto 500g"
- Categoría: Seleccionar o crear
- Precio: 1500.00
- Descripción: "..."
- Activo: Sí

**3. Actualizar mapping manualmente**:

Editar `Reconocimiento-Productos/product_mapping.json`:

```json
{
  "ingsoft_mapping": {
    "7": {
      "ingsoft_id": <ID_DJANGO_ASIGNADO>,
      "name": "nuevo_producto",
      "status": "mapped",
      "notes": "Mapeado manualmente"
    }
  }
}
```

### Método 3: API REST

**POST** `http://localhost:8000/api/productos/`

```json
{
  "nombre": "Nuevo Producto 500g",
  "categoria": 1,
  "precio": 1500.00,
  "descripcion": "Descripción del producto",
  "activo": true
}
```

---

## 🧪 Testing

### Test Manual con cURL

```powershell
# 1. Obtener token JWT
$body = @{
    username = "admin"
    password = "tu_password"
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/auth/login/" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"

$token = $response.access

# 2. Probar reconocimiento
$image_b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\ruta\a\imagen.jpg"))

$body = @{
    image_base64 = $image_b64
    deposito_id = 1
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/productos/reconocer-imagen/" `
    -Method Post `
    -Headers @{ Authorization = "Bearer $token" } `
    -Body $body `
    -ContentType "application/json"
```

### Test con Python

```python
# test_recognition_endpoint.py
import requests
import base64

# Login
login_response = requests.post(
    'http://localhost:8000/api/auth/login/',
    json={'username': 'admin', 'password': 'tu_password'}
)
token = login_response.json()['access']

# Leer imagen
with open('test_image.jpg', 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode()

# Reconocer
response = requests.post(
    'http://localhost:8000/api/productos/reconocer-imagen/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'image_base64': image_b64,
        'deposito_id': 1
    }
)

print(response.json())
```

### Tests Automatizados

```python
# backend/productos/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Producto, Categoria

class RecognitionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear categoría y producto de prueba
        self.categoria = Categoria.objects.create(nombre='Test')
        self.producto = Producto.objects.create(
            nombre='Producto Test',
            categoria=self.categoria,
            precio=100.00
        )
    
    def test_reconocer_sin_imagen(self):
        """Test endpoint sin enviar imagen"""
        response = self.client.post('/api/productos/reconocer-imagen/')
        self.assertEqual(response.status_code, 400)
    
    def test_reconocer_sin_autenticacion(self):
        """Test endpoint sin autenticación"""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/productos/reconocer-imagen/')
        self.assertEqual(response.status_code, 401)
```

**Ejecutar tests**:
```powershell
python manage.py test productos
```

---

## 🐛 Troubleshooting

### Error: "Servicio de reconocimiento no disponible"

**Causa**: El servidor de reconocimiento no está corriendo.

**Solución**:
```powershell
# Verificar que el servidor esté corriendo
curl http://localhost:8080/health

# Si no responde, iniciar el servidor
cd C:\Users\Usuario\Documents\GitHub\IngSoft2025\Reconocimiento-Productos
.\.venv\Scripts\Activate.ps1
python server.py
```

### Error: "Timeout al procesar la imagen"

**Causas posibles**:
1. Imagen muy grande (>10MB)
2. Servidor de reconocimiento sobrecargado
3. Timeout muy corto

**Soluciones**:
```python
# 1. Aumentar timeout
response = requests.post(..., timeout=90)  # 90 segundos

# 2. Comprimir imagen antes de enviar
from PIL import Image
import io

img = Image.open('foto.jpg')
img.thumbnail((1920, 1080))  # Redimensionar
buffer = io.BytesIO()
img.save(buffer, format='JPEG', quality=85)
image_bytes = buffer.getvalue()
```

### Error: "cannot identify image file"

**Causa**: Archivo no es una imagen válida o está corrupto.

**Solución**:
```python
# Validar imagen antes de enviar
from PIL import Image

try:
    img = Image.open(image_file)
    img.verify()  # Verificar que es válida
except Exception as e:
    return Response({'error': 'Imagen inválida'}, status=400)
```

### Error: JWT token expirado

**Causa**: Los tokens JWT expiran después de cierto tiempo.

**Solución**:
```python
# En el frontend, refrescar token automáticamente
import { refreshToken } from '@/lib/auth';

async function apiCall() {
    try {
        // Intentar llamada
        return await fetch(...);
    } catch (error) {
        if (error.status === 401) {
            // Refrescar token y reintentar
            await refreshToken();
            return await fetch(...);
        }
        throw error;
    }
}
```

### Productos no se mapean correctamente

**Verificar**:

1. **IDs en product_mapping.json**:
```powershell
cd C:\Users\Usuario\Documents\GitHub\IngSoft2025\Reconocimiento-Productos
python -c "import json; print(json.load(open('product_mapping.json'))['ingsoft_mapping'])"
```

2. **IDs en Django**:
```powershell
python manage.py shell -c "from productos.models import Producto; [print(f'{p.id}: {p.nombre}') for p in Producto.objects.all()]"
```

3. **Sincronizar manualmente**:
```powershell
python manage.py crear_productos_reconocimiento
```

---

## 📊 Logs y Debugging

### Ver logs en tiempo real

```powershell
# Django (en la terminal donde corre el servidor)
# Los logs aparecen automáticamente

# Para logging más detallado, en settings.py:
LOGGING = {
    # ...
    'loggers': {
        'productos': {
            'handlers': ['console'],
            'level': 'DEBUG',  # ← Cambiar a DEBUG
            'propagate': False,
        },
    },
}
```

### Logs importantes

```python
# En recognition_views.py
logger.info(f"📸 Imagen recibida: {len(image_bytes)} bytes")
logger.info(f"🔍 Enviando a API de reconocimiento")
logger.info(f"✅ Productos detectados: {total}")
logger.error(f"❌ Error en API: {response.status_code}")
```

### Verificar conexión con API

```python
# Test rápido
import requests

try:
    response = requests.get('http://localhost:8080/health', timeout=5)
    print("✅ API de reconocimiento OK:", response.json())
except Exception as e:
    print("❌ Error:", e)
```

---

## 📚 Comandos Útiles

```powershell
# Backend
python manage.py runserver                # Iniciar servidor
python manage.py makemigrations           # Crear migraciones
python manage.py migrate                  # Aplicar migraciones
python manage.py createsuperuser          # Crear superusuario
python manage.py shell                    # Shell interactivo
python manage.py test                     # Ejecutar tests

# Productos
python manage.py crear_productos_reconocimiento  # Cargar productos

# Base de datos
python manage.py dbshell                  # Shell de PostgreSQL
python manage.py dumpdata productos > backup.json  # Backup

# Debugging
python manage.py check                    # Verificar configuración
python manage.py showmigrations           # Ver migraciones
python manage.py sqlmigrate productos 0001  # Ver SQL de migración
```

---

## 🔗 Referencias

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)
- [PostgreSQL + Django](https://docs.djangoproject.com/en/4.2/ref/databases/#postgresql-notes)

---

**Última actualización**: 6 de octubre, 2025  
**Mantenido por**: Equipo IngSoft2025
