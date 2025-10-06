# Script de Verificación del Sistema de Reconocimiento

Este documento describe cómo probar la funcionalidad completa del reconocimiento de productos.

## 🧪 Pre-requisitos

Antes de iniciar las pruebas, asegúrate de tener:

### 1. API de Reconocimiento Corriendo
```bash
cd c:\Users\osval\Documents\GitHub\shelf-product-identifier
python server.py
```

Verificar en: http://localhost:8080/health

### 2. Backend Django Corriendo
```bash
cd c:\Users\osval\Documents\GitHub\IngSoft2025\backend
.\backend_env\Scripts\python.exe manage.py runserver
```

Verificar en: http://localhost:8000/admin

### 3. Frontend Next.js Corriendo
```bash
cd c:\Users\osval\Documents\GitHub\IngSoft2025\frontend
npm run dev
```

Verificar en: http://localhost:3000

### 4. Base de Datos con Productos
Asegúrate de tener productos registrados en la BD con stock disponible.

---

## ✅ Pruebas Paso a Paso

### Prueba 1: Verificar Conectividad de la API

#### Usando PowerShell:
```powershell
# Verificar health de la API de reconocimiento
Invoke-WebRequest -Uri "http://localhost:8080/health" -Method GET

# Verificar endpoint de Django
Invoke-WebRequest -Uri "http://localhost:8000/api/productos/verificar-api-reconocimiento/" `
    -Headers @{"Authorization"="Bearer TU_TOKEN_AQUI"} `
    -Method GET
```

#### Resultado Esperado:
```json
{
  "success": true,
  "status": "API de reconocimiento disponible"
}
```

---

### Prueba 2: Reconocimiento con Imagen de Prueba

#### Usando PowerShell:
```powershell
# Preparar imagen de prueba
$imagePath = "c:\Users\osval\Documents\GitHub\shelf-product-identifier\data\img\si.jpg"
$token = "TU_TOKEN_AQUI"

# Crear multipart form data
$boundary = [System.Guid]::NewGuid().ToString()
$fileBin = [System.IO.File]::ReadAllBytes($imagePath)
$encoding = [System.Text.Encoding]::GetEncoding("iso-8859-1")

$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"image`"; filename=`"test.jpg`"",
    "Content-Type: application/octet-stream",
    "",
    $encoding.GetString($fileBin),
    "--$boundary--"
) -join "`r`n"

# Enviar request
Invoke-WebRequest `
    -Uri "http://localhost:8000/api/productos/reconocer-imagen/" `
    -Method POST `
    -Headers @{
        "Authorization" = "Bearer $token"
    } `
    -ContentType "multipart/form-data; boundary=$boundary" `
    -Body $bodyLines
```

#### Resultado Esperado:
```json
{
  "success": true,
  "total_productos": 2,
  "productos": [
    {
      "ingsoft_product_id": 5,
      "nombre_db": "Coca Cola 2.25L",
      "categoria_db": "Bebidas",
      "precio_db": "250.00",
      "existe_en_bd": true,
      "stock_disponible": 50,
      "classification_confidence": 0.92
    }
  ]
}
```

---

### Prueba 3: Flujo Completo desde Frontend

#### Pasos Manuales:

1. **Iniciar Sesión como Cajero**
   - Ir a http://localhost:3000/login
   - Usar credenciales de cajero
   - Navegar a "Ventas"

2. **Iniciar Nueva Venta**
   - Click en "Iniciar Nueva Venta"
   - Verificar que aparece el número de venta

3. **Capturar Foto**
   - Click en botón 📸
   - Permitir acceso a cámara (si es primera vez)
   - Posicionar productos frente a la cámara
   - Click en "Capturar Foto"
   - Verificar que aparece spinner "Analizando imagen..."

4. **Verificar Detección**
   - Esperar a que aparezca modal con productos detectados
   - Verificar que cada producto muestra:
     - ✅ Nombre correcto
     - ✅ Precio correcto
     - ✅ Stock disponible
     - ✅ Porcentaje de confianza
   - Verificar controles de cantidad funcionan

5. **Confirmar Productos**
   - Ajustar cantidades si es necesario
   - Click en "Confirmar y Agregar"
   - Verificar que productos aparecen en el ticket
   - Verificar que totales se calculan correctamente

6. **Finalizar Venta**
   - Click en "Finalizar Venta"
   - Verificar generación de ticket
   - Descargar PDF

---

## 🐛 Casos de Prueba de Error

### Error 1: API No Disponible
**Acción**: Apagar servidor de reconocimiento
**Resultado Esperado**: 
- Mensaje: "No se pudo conectar con la API de reconocimiento"
- Botón de cámara sigue funcionando pero muestra error al procesar

### Error 2: Producto No Mapeado
**Acción**: Capturar foto de producto no registrado
**Resultado Esperado**:
- Mensaje: "No se detectaron productos registrados en el sistema"
- Modal no se abre
- Sugerencia de agregar manualmente

### Error 3: Imagen Borrosa
**Acción**: Capturar foto moviendo la cámara
**Resultado Esperado**:
- Detección con baja confianza (<50%)
- Sistema puede rechazar automáticamente
- O mostrar con advertencia de baja confianza

### Error 4: Sin Stock
**Acción**: Intentar agregar producto sin stock
**Resultado Esperado**:
- Botón + deshabilitado al llegar a 0
- Mensaje de stock no disponible
- No permite agregar a la venta

---

## 📊 Métricas de Éxito

### Performance
- ✅ Tiempo de detección: < 5 segundos
- ✅ Precisión de detección: > 85%
- ✅ Tiempo de carga del modal: < 1 segundo

### Funcionalidad
- ✅ Productos correctamente detectados: > 90%
- ✅ Precios correctos: 100%
- ✅ Stock sincronizado: 100%

### Usabilidad
- ✅ Clicks hasta finalizar venta: < 10
- ✅ Tiempo total de venta con foto: < 30 segundos
- ✅ Errores de usuario: < 5%

---

## 🔍 Logs de Debugging

### Ver logs del Backend:
```bash
# En la terminal donde corre Django
# Los logs aparecerán automáticamente mostrando:
# - Requests recibidos
# - Tiempo de procesamiento
# - Errores si los hay
```

### Ver logs del Frontend:
```bash
# Abrir DevTools en el navegador (F12)
# Ir a tab "Console"
# Filtrar por "reconocimiento" o "API"
```

### Ver logs de la API de Reconocimiento:
```bash
# En la terminal donde corre server.py
# Logs muestran:
# - Imágenes recibidas
# - Productos detectados
# - Tiempo de inferencia
```

---

## 📝 Checklist de Validación

Antes de considerar la feature completa, verificar:

- [ ] ✅ API de reconocimiento responde correctamente
- [ ] ✅ Backend recibe y procesa imágenes
- [ ] ✅ Frontend muestra modal de detección
- [ ] ✅ Productos se mapean correctamente
- [ ] ✅ Precios y stock se muestran
- [ ] ✅ Cantidades se pueden ajustar
- [ ] ✅ Productos se agregan al ticket
- [ ] ✅ Totales se calculan correctamente
- [ ] ✅ Manejo de errores funciona
- [ ] ✅ Feedback visual es claro
- [ ] ✅ Performance es aceptable (<5s)
- [ ] ✅ Documentación está completa

---

## 🎯 Datos de Prueba Sugeridos

### Productos a Detectar:
1. **Coca Cola 2.25L** - Producto común, alta confianza esperada
2. **Café Soluble** - Producto mediano, confianza media
3. **Desodorante Nivea** - Producto pequeño, puede requerir buena luz
4. **Pure de Tomate** - Producto con packaging similar a otros

### Escenarios:
1. **1 producto**: Validar detección básica
2. **2-3 productos**: Validar detección múltiple
3. **Productos similares**: Validar clasificación precisa
4. **Diferentes distancias**: Validar robustez del modelo

---

## 🚀 Deploy a Producción

Cuando todas las pruebas pasen:

1. **Actualizar variables de entorno**:
```bash
# En .env del backend
RECOGNITION_API_URL=https://api-reconocimiento.tu-dominio.com
```

2. **Configurar HTTPS**:
- La cámara solo funciona en HTTPS en producción
- Configurar certificados SSL

3. **Optimizar modelo**:
- Considerar usar modelo más ligero si es necesario
- Implementar caché de resultados

4. **Monitoreo**:
- Configurar logs centralizados
- Alertas de error
- Métricas de uso

---

## 📞 Contacto

Para problemas técnicos o preguntas:
- **Backend Django**: Verificar logs en `IngSoft2025/backend/`
- **Frontend React**: Verificar consola del navegador
- **API Reconocimiento**: Verificar logs de `shelf-product-identifier/`
