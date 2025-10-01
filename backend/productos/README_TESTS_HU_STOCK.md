# Tests para HU: Visualización de Stock Total y por Depósito

## Ubicación de Tests

Los tests para la Historia de Usuario **"Como administrador quiero visualizar el stock total y de cada depósito"** están distribuidos en las carpetas correspondientes:

### 📁 `productos/tests.py`
Contiene los tests principales de funcionalidad de stock:

#### `StockVisualizationTestCase`
- ✅ `test_visualizar_stock_total_vista_productos()` - **CA1**
- ✅ `test_visualizar_detalle_producto_con_stock_completo()` - **CA1 Detallado**
- ✅ `test_visualizar_stock_por_deposito_central()` - **CA2**
- ✅ `test_visualizar_stock_por_deposito_norte()` - **CA2**
- ✅ `test_lista_productos_incluye_nombre_y_stock()` - **CA3**
- ✅ `test_lista_productos_por_deposito_incluye_nombre_y_stock()` - **CA3**
- ✅ `test_filtrar_productos_por_deposito()` - Funcionalidad adicional
- ✅ `test_estadisticas_productos_stock_total()` - Estadísticas

#### `StockVisualizationSecurityTestCase`
- ⚠️ `test_acceso_solo_depositos_propios()` - **Test de Seguridad** (detecta vulnerabilidad)
- ✅ `test_autenticacion_requerida_stock_views()` - Autenticación

### 📁 `inventario/tests.py`
Contiene tests específicos de depósitos para la HU:

#### `DepositoStockVisualizationTestCase`
- ✅ `test_listar_depositos_para_gestion_stock()` - **CA2 Inventario**
- ✅ `test_obtener_depositos_disponibles_para_stock()` - **CA2 Inventario**
- ✅ `test_estadisticas_depositos_para_stock()` - Estadísticas de depósitos
- ✅ `test_detalle_deposito_para_contexto_stock()` - **CA2 Detallado**
- ✅ `test_seguridad_acceso_depositos_stock()` - Seguridad de depósitos
- ✅ `test_modificar_deposito_para_optimizar_stock()` - Gestión de depósitos

## Criterios de Aceptación Cubiertos

### ✅ CA1: Visualizar stock total desde vista "Productos"
**Tests en**: `productos/tests.py`
- Vista de lista con stock total ✅
- Vista de detalle con desglose por depósito ✅
- Campos requeridos: nombre, stock_total ✅

### ✅ CA2: Ver stock por depósito desde "Gestionar Depósitos"
**Tests en**: `productos/tests.py` + `inventario/tests.py`
- Vista de productos por depósito específico ✅
- Lista de depósitos disponibles ✅
- Gestión completa de depósitos ✅

### ✅ CA3: Lista con nombre y stock correspondiente
**Tests en**: `productos/tests.py`
- Formato correcto en vista de productos ✅
- Formato correcto en vista por depósito ✅

## Ejecución de Tests

### Tests de Productos (Principal)
```bash
python manage.py test productos.tests.StockVisualizationTestCase -v 2 --settings=appproductos.settings_test
python manage.py test productos.tests.StockVisualizationSecurityTestCase -v 2 --settings=appproductos.settings_test
```

### Tests de Inventario (Complementario)
```bash
python manage.py test inventario.tests.DepositoStockVisualizationTestCase -v 2 --settings=appproductos.settings_test
```

### Todos los Tests de la HU
```bash
python manage.py test productos.tests inventario.tests -k "Stock" -v 2 --settings=appproductos.settings_test
```

## Vulnerabilidades Identificadas

### 🔴 CRÍTICA: En `productos/tests.py`
**Test**: `test_acceso_solo_depositos_propios()`
- **Problema**: Vista permite acceso a depósitos de otros supermercados
- **Vista afectada**: `productos_por_deposito`
- **Estado**: Test falla intencionalmente para alertar del bug

## Datos de Test

### Configuración Estándar (productos/tests.py):
- **Categorías**: Bebidas, Lácteos, Limpieza
- **Depósitos**: Central, Norte, Sur
- **Productos**: Agua (150 stock), Leche (80), Detergente (20), Yogur (0)

### Configuración Inventario (inventario/tests.py):
- **Depósitos**: Principal (activo), Secundario (activo), Inactivo
- **Enfoque**: Gestión y administración de depósitos

## Integración con Tests Existentes

Los nuevos tests se integran perfectamente con los tests existentes:
- **productos/tests.py**: Mantiene `ProductosABMTests` + agrega `StockVisualization*`
- **inventario/tests.py**: Mantiene `DepositoModelTestCase` + `DepositoAPITestCase` + agrega `DepositoStockVisualization*`

## Resultados Esperados

### ✅ Tests Funcionales
Todos los tests de funcionalidad deben pasar, confirmando que la HU está completamente implementada.

### ❌ Tests de Seguridad
El test `test_acceso_solo_depositos_propios()` debe fallar, indicando la necesidad de corrección en el código de producción.

---

**Nota**: Los tests están diseñados para ser exhaustivos y detectar tanto funcionalidad correcta como vulnerabilidades de seguridad. La organización por carpetas facilita el mantenimiento y la comprensión del código.