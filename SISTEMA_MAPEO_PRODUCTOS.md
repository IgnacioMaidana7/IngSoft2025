# 🔗 Sistema de Mapeo de Productos entre API y Backend

## 📋 Resumen Ejecutivo

El sistema utiliza un **mapeo por IDs** para vincular productos entre:
- **API de Reconocimiento** (shelf-product-identifier) → IDs internos (1, 2, 3, 4, 5)
- **Backend Django** (IngSoft2025) → IDs de PostgreSQL (autogenerados)

Este mapeo se almacena en `product_mapping.json` y permite búsquedas **rápidas, robustas y únicas** por ID.

---

## 🎯 ¿Por qué Mapeo por ID y NO por Nombre?

### ❌ Búsqueda por Nombre (Mala Práctica)
```python
# EVITAR ESTO
producto = Producto.objects.filter(nombre="Fritolim Aceite en Aerosol").first()
```

**Problemas:**
- ❌ Si cambias "Fritolim Aceite en Aerosol" → "Fritolim" se rompe
- ❌ Sensible a mayúsculas, acentos, espacios
- ❌ Puede haber duplicados con nombres similares
- ❌ Búsquedas de texto son lentas (sin índice)
- ❌ Difícil mantener sincronización

### ✅ Búsqueda por ID (Mejor Práctica)
```python
# HACER ESTO
producto = Producto.objects.get(id=123)  # Búsqueda instantánea por primary key
```

**Ventajas:**
- ✅ IDs nunca cambian
- ✅ Búsqueda instantánea (primary key indexado)
- ✅ Unicidad garantizada por la base de datos
- ✅ Puedes renombrar productos sin romper nada
- ✅ Escalable y mantenible

---

## 🔄 Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                    1. FOTO DEL CAJERO                                │
│  Frontend captura imagen → Envía a Backend Django                   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│            2. BACKEND → API DE RECONOCIMIENTO                        │
│  Backend Django reenvía imagen a API Flask (puerto 8080)            │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│              3. API DETECTA PRODUCTOS (YOLO + ResNet18)             │
│  Resultado: [{api_product_id: 5, name: "fritolim", ...}]           │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│          4. INTEGRADOR MAPEA IDs (ingsoft_integration.py)           │
│  Consulta product_mapping.json:                                     │
│    "5": { "ingsoft_id": 123 }  ← ⭐ MAPEO CLAVE                     │
│  Resultado: [{ingsoft_product_id: 123, api_product_id: 5, ...}]    │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│        5. BACKEND ENRIQUECE CON DATOS DE POSTGRESQL                 │
│  producto_db = Producto.objects.get(id=123)  ← Búsqueda por ID     │
│  Agrega: nombre_db, precio_db, stock_disponible                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│              6. FRONTEND MUESTRA PRODUCTOS DETECTADOS               │
│  Modal con: "Fritolim - $680 - Stock: 50 unidades"                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Productos Actuales del Sistema

### Registrados en API de Reconocimiento (5 productos):

| api_product_id | name                  | display_name                | 
|----------------|-----------------------|-----------------------------|
| 1              | pure_tomate_caja      | Puré de Tomate Noel        |
| 2              | desodorante_nivea     | Desodorante Nivea          |
| 3              | desodorante_dove      | Desodorante Dove           |
| 4              | cafe_soluble          | Café Soluble La Virginia   |
| 5              | fritolim              | Fritolim Aceite en Aerosol |

### Para Crear en Django (3 productos prioritarios):

| Producto                   | Categoría         | Precio Sugerido | SKU               |
|----------------------------|-------------------|-----------------|-------------------|
| Fritolim Aceite en Aerosol | Alimentos         | $680.00         | FRITO-ACEIT-120ML |
| Desodorante Nivea          | Cuidado Personal  | $890.00         | NIVEA-DEO-150ML   |
| Puré de Tomate Noel        | Alimentos         | $450.00         | NOEL-TOMATE-520G  |

---

## 🚀 Pasos para Activar el Sistema

### Paso 1: Crear Productos en Django

```bash
cd c:\Users\osval\Documents\GitHub\IngSoft2025\backend
c:\Users\osval\Documents\GitHub\IngSoft2025\backend\backend_env\Scripts\python.exe manage.py crear_productos_reconocimiento
```

Este comando:
- ✅ Crea los 3 productos en PostgreSQL
- ✅ Genera IDs automáticamente (ej: 123, 124, 125)
- ✅ Actualiza automáticamente `product_mapping.json`

**Output esperado:**
```
🚀 Iniciando creación de productos para reconocimiento...
  ✅ Categoría creada: Alimentos
  ✅ Producto creado: Fritolim Aceite en Aerosol (ID: 123)
  ✅ Categoría creada: Cuidado Personal
  ✅ Producto creado: Desodorante Nivea (ID: 124)
  ✅ Producto creado: Puré de Tomate Noel (ID: 125)
✅ Archivo product_mapping.json actualizado
✅ ¡Proceso completado exitosamente!
```

### Paso 2: Verificar `product_mapping.json`

Debe quedar así:
```json
{
  "ingsoft_mapping": {
    "5": {
      "ingsoft_id": 123,           ← ⭐ ID real de Django
      "name": "fritolim",
      "status": "mapped",
      "notes": "Mapeado automáticamente - ID Django: 123"
    },
    "2": {
      "ingsoft_id": 124,
      "name": "desodorante_nivea",
      "status": "mapped"
    },
    "1": {
      "ingsoft_id": 125,
      "name": "pure_tomate_caja",
      "status": "mapped"
    }
  },
  "ingsoft_to_shelf": {
    "123": {"shelf_product_id": 5, "verified": true},
    "124": {"shelf_product_id": 2, "verified": true},
    "125": {"shelf_product_id": 1, "verified": true}
  }
}
```

### Paso 3: Reiniciar API de Reconocimiento

```bash
cd c:\Users\osval\Documents\GitHub\shelf-product-identifier
python server.py
```

La API cargará automáticamente el nuevo `product_mapping.json`.

---

## 🧪 Ejemplo de Respuesta Completa

Cuando un cajero toma una foto de Fritolim:

### 1. API Detecta
```json
{
  "success": true,
  "products": [
    {
      "product_id": 5,
      "name": "fritolim",
      "display_name": "Fritolim Aceite en Aerosol",
      "detection_confidence": 0.95
    }
  ]
}
```

### 2. Integrador Mapea
```json
{
  "success": true,
  "productos": [
    {
      "api_product_id": 5,
      "ingsoft_product_id": 123,     ← ⭐ ID de Django
      "name": "fritolim",
      "display_name": "Fritolim Aceite en Aerosol",
      "is_mapped_to_ingsoft": true
    }
  ]
}
```

### 3. Backend Enriquece
```json
{
  "success": true,
  "productos": [
    {
      "ingsoft_product_id": 123,
      "api_product_id": 5,
      "nombre_db": "Fritolim Aceite en Aerosol",
      "precio_db": "680.00",
      "categoria_db": "Alimentos",
      "stock_disponible": 50,
      "existe_en_bd": true
    }
  ]
}
```

---

## 🔍 Código Clave del Sistema

### ingsoft_integration.py (Mapeo)
```python
def _adapt_single_product(self, product: Dict) -> Dict:
    api_product_id = product.get('product_id')  # ID de la API: 5
    ingsoft_mapping = self.producto_mapping.get(str(api_product_id), {})
    
    # ⭐ OBTENER ID DE DJANGO
    ingsoft_id = ingsoft_mapping.get('ingsoft_id')  # ID Django: 123
    
    return {
        "ingsoft_product_id": ingsoft_id,  # 123
        "api_product_id": api_product_id,  # 5
        "is_mapped_to_ingsoft": ingsoft_id is not None,
        ...
    }
```

### recognition_views.py (Búsqueda)
```python
for producto_detectado in result['productos']:
    ingsoft_id = producto_detectado.get('ingsoft_product_id')  # 123
    
    if ingsoft_id:
        # 🔍 Búsqueda por ID - Instantánea y segura
        producto_db = Producto.objects.get(id=ingsoft_id, activo=True)
        
        # Enriquecer con datos reales de la BD
        producto_detectado['nombre_db'] = producto_db.nombre
        producto_detectado['precio_db'] = str(producto_db.precio)
        producto_detectado['stock_disponible'] = ...
```

---

## 🛡️ Ventajas del Sistema Actual

### 1. **Robustez**
- Si renombras "Fritolim" → "Aceite Fritolim" en Django, sigue funcionando
- Los IDs son inmutables y garantizan consistencia

### 2. **Performance**
- Búsqueda por ID (primary key) es O(1) - instantánea
- Búsqueda por nombre sería O(n) con escaneo de tabla

### 3. **Escalabilidad**
- Fácil agregar nuevos productos sin conflictos
- Mapeo centralizado en un solo archivo JSON

### 4. **Mantenibilidad**
- Cambios de precio/nombre/descripción no afectan el mapeo
- Debug más fácil: "ID 123 no encontrado" vs "Producto 'Fritolm' no encontrado" (typo)

### 5. **Trazabilidad**
- Cada producto tiene 2 IDs: api_product_id + ingsoft_product_id
- Permite auditoría y debugging del flujo completo

---

## 📝 Notas Importantes

1. **El archivo `product_mapping.json` es la fuente de verdad**
   - Debe estar sincronizado con la BD de Django
   - Si creas/eliminas productos, actualiza el mapeo

2. **IDs de Django son autogenerados**
   - No puedes predecir qué ID tendrá un producto
   - Por eso el comando automático actualiza el JSON

3. **Productos no mapeados**
   - Si `ingsoft_product_id` es `null`, el backend devuelve:
     ```json
     {
       "existe_en_bd": false,
       "mensaje": "Producto no mapeado en el sistema"
     }
     ```

4. **Agregar nuevos productos**
   - Opción A: Crearlos manualmente en Django y actualizar `product_mapping.json`
   - Opción B: Modificar el comando `crear_productos_reconocimiento.py`

---

## 🎓 Resumen: ¿Por qué es Mejor?

| Criterio           | Por Nombre ❌        | Por ID ✅           |
|--------------------|---------------------|---------------------|
| Velocidad          | Lenta (O(n))        | Instantánea (O(1))  |
| Unicidad           | No garantizada      | Garantizada por DB  |
| Robustez           | Frágil a cambios    | Inmutable           |
| Mantenibilidad     | Difícil             | Fácil               |
| Escalabilidad      | Problemática        | Excelente           |
| Debugging          | Confuso             | Claro               |

**Conclusión:** El mapeo por ID es la mejor práctica en sistemas de integración entre APIs.
