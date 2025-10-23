# Integración con API de Reconocimiento de Productos

## Descripción

Este módulo permite al backend de Django recibir imágenes del frontend y comunicarse con la API de reconocimiento de productos para identificar productos en estanterías.

## Archivos Creados/Modificados

### Backend Django

1. **`productos/recognition_views.py`** (NUEVO)
   - Endpoint para recibir imágenes y enviarlas a la API de reconocimiento
   - Endpoint para verificar estado de la API
   - Endpoint para obtener catálogo de productos reconocibles

2. **`productos/urls.py`** (MODIFICADO)
   - Agregadas 3 nuevas rutas para reconocimiento de productos

3. **`appproductos/settings.py`** (MODIFICADO)
   - Agregada configuración `RECOGNITION_API_URL`

4. **`requirements.txt`** (MODIFICADO)
   - Agregada librería `requests>=2.31.0`

5. **`.env`** (MODIFICADO)
   - Agregada variable `RECOGNITION_API_URL=http://localhost:8080`

### Frontend

6. **`src/lib/api.ts`** (MODIFICADO)
   - Agregadas interfaces TypeScript para productos reconocidos
   - Agregadas funciones para llamar a los endpoints de reconocimiento

## Endpoints Disponibles

### 1. Reconocer Productos desde Imagen
```
POST /api/productos/reconocer-imagen/
```

**Request:**
- `Content-Type: multipart/form-data`
- `image`: archivo de imagen (File)

**Response:**
```json
{
  "success": true,
  "total_productos": 2,
  "productos": [
    {
      "product_id": 1,
      "ingsoft_product_id": 5,
      "name": "Coca Cola 2.25L",
      "display_name": "Coca Cola 2.25L",
      "category": "Bebidas",
      "brand": "Coca Cola",
      "detection_confidence": 0.95,
      "classification_confidence": 0.92,
      "bbox": {
        "x1": 100,
        "y1": 150,
        "x2": 300,
        "y2": 450,
        "width": 200,
        "height": 300
      },
      "nombre_db": "Coca Cola 2.25L",
      "categoria_db": "Bebidas",
      "precio_db": "250.00",
      "existe_en_bd": true,
      "stock_disponible": 50,
      "stock_minimo": 10,
      "stock_bajo": false
    }
  ],
  "processing_time_ms": 1250,
  "deposito_id": 1
}
```

### 2. Verificar Estado de la API
```
GET /api/productos/verificar-api-reconocimiento/
```

**Response:**
```json
{
  "success": true,
  "status": "API de reconocimiento disponible",
  "details": {
    "status": "healthy",
    "version": "1.0.0"
  }
}
```

### 3. Obtener Catálogo de Productos Reconocibles
```
GET /api/productos/catalogo-reconocimiento/
```

**Response:**
```json
{
  "total_products": 10,
  "products": [
    {
      "id": 1,
      "name": "Coca Cola 2.25L",
      "category": "Bebidas",
      "ingsoft_id": 5
    }
  ]
}
```

## Uso desde el Frontend

### 1. Importar las funciones

```typescript
import { 
  reconocerProductosImagen, 
  verificarApiReconocimiento,
  type ProductoReconocido 
} from '@/lib/api';
```

### 2. Verificar que la API esté disponible

```typescript
const verificarAPI = async () => {
  try {
    const resultado = await verificarApiReconocimiento(token);
    if (resultado.success) {
      console.log('API disponible:', resultado.status);
    }
  } catch (error) {
    console.error('API no disponible:', error);
  }
};
```

### 3. Reconocer productos desde una imagen

```typescript
const reconocerProductos = async (imageFile: File) => {
  try {
    const resultado = await reconocerProductosImagen(imageFile, token);
    
    if (resultado.success) {
      console.log(`Detectados ${resultado.total_productos} productos`);
      
      resultado.productos.forEach((producto) => {
        if (producto.existe_en_bd) {
          console.log(`Producto: ${producto.nombre_db}`);
          console.log(`Precio: $${producto.precio_db}`);
          console.log(`Stock: ${producto.stock_disponible}`);
        } else {
          console.log(`Producto no mapeado: ${producto.display_name}`);
        }
      });
    }
  } catch (error) {
    console.error('Error reconociendo productos:', error);
  }
};
```

### 4. Ejemplo completo con captura de foto

```typescript
const handlePhotoUploaded = async (result: { id: string; url: string }) => {
  if (!token) return;
  
  try {
    setReconociendo(true);
    
    // Obtener el archivo de la foto capturada
    const response = await fetch(result.url);
    const blob = await response.blob();
    const file = new File([blob], 'captura.jpg', { type: 'image/jpeg' });
    
    // Enviar a la API de reconocimiento
    const resultadoReconocimiento = await reconocerProductosImagen(file, token);
    
    if (resultadoReconocimiento.success) {
      // Procesar productos detectados
      for (const productoRec of resultadoReconocimiento.productos) {
        if (productoRec.existe_en_bd && productoRec.ingsoft_product_id) {
          // Agregar producto a la venta
          await agregarProductoAVenta(productoRec.ingsoft_product_id);
        }
      }
    }
  } catch (error) {
    console.error('Error:', error);
  } finally {
    setReconociendo(false);
  }
};
```

## Configuración

### Variables de Entorno

En el archivo `.env` del backend:

```bash
# Product Recognition API
RECOGNITION_API_URL=http://localhost:8080
```

**Nota:** Cambiar `http://localhost:8080` por la URL donde esté corriendo la API de reconocimiento.

### Iniciar la API de Reconocimiento

Antes de usar los endpoints de reconocimiento, asegúrate de que la API esté corriendo:

```bash
cd c:\Users\osval\Documents\GitHub\shelf-product-identifier
python server.py
```

La API debería estar disponible en `http://localhost:8080`

## Flujo de Datos

```
1. Frontend captura foto → 
2. Frontend envía imagen al Backend Django → 
3. Backend Django convierte imagen a base64 → 
4. Backend Django envía a API de reconocimiento → 
5. API de reconocimiento detecta y clasifica productos → 
6. API devuelve productos con IDs de IngSoft2025 → 
7. Backend Django enriquece con datos de BD (precio, stock) → 
8. Backend Django devuelve al Frontend → 
9. Frontend muestra productos y los agrega a la venta
```

## Permisos

Los endpoints de reconocimiento requieren autenticación y permisos de **Cajero** o **Administrador**.

## Manejo de Errores

La API maneja diferentes tipos de errores:

- **400 Bad Request**: No se recibió imagen
- **500 Internal Server Error**: Error en la API de reconocimiento
- **503 Service Unavailable**: API de reconocimiento no disponible
- **504 Gateway Timeout**: Timeout al conectar con la API

## Testing

Para probar los endpoints puedes usar herramientas como:

### cURL

```bash
curl -X POST http://localhost:8000/api/productos/reconocer-imagen/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@path/to/image.jpg"
```

### Python requests

```python
import requests

url = "http://localhost:8000/api/productos/reconocer-imagen/"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
files = {"image": open("path/to/image.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

## Troubleshooting

### Error: "API de reconocimiento no disponible"

**Solución:** Verificar que la API de reconocimiento esté corriendo en el puerto 8080

```bash
cd shelf-product-identifier
python server.py
```

### Error: "Timeout al conectar con la API de reconocimiento"

**Solución:** La API está tardando más de 30 segundos. Verificar:
- Que el modelo esté cargado correctamente
- Que la imagen no sea demasiado grande
- Que haya suficiente memoria disponible

### Error: "Producto no mapeado en el sistema"

**Solución:** El producto fue detectado pero no tiene un `ingsoft_product_id` asignado. Verificar el archivo `product_mapping.json` en la API de reconocimiento.

## Próximos Pasos

1. Implementar caché de resultados para imágenes similares
2. Agregar batch processing para múltiples imágenes
3. Implementar feedback loop para mejorar el modelo
4. Agregar analytics de productos más detectados
5. Implementar sistema de notificaciones para productos no mapeados
