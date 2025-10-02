# Documentación de Tests - HU: Visualización de Stock

## Archivo de Test: `test_hu_visualizacion_stock.py`

### Descripción
Tests comprehensivos para la Historia de Usuario: **"Como administrador quiero visualizar el stock total y de cada depósito"**

### Criterios de Aceptación Testeados

1. ✅ **CA1**: El administrador puede visualizar el stock total de cada producto desde la vista de "Productos"
2. ✅ **CA2**: El administrador puede ver el stock de cada depósito desde la vista "Gestionar mis Depósitos"  
3. ✅ **CA3**: Se despliega una lista con el nombre del producto y su stock correspondiente

## Estructura de Tests

### 1. `StockVisualizationTestCase` - Tests Principales
**Objetivo**: Validar los criterios de aceptación principales

#### Tests Implementados:
- `test_visualizar_stock_total_vista_productos()` - **CA1**
  - Valida que la API `/productos/` muestre stock total correctamente
  - Verifica cálculo de stock sumando todos los depósitos
  - Confirma presencia de campos requeridos (`nombre`, `stock_total`, `categoria_nombre`)

- `test_visualizar_detalle_producto_con_stock_completo()` - **CA1 Detallado**
  - Valida que el detalle del producto muestre stock total y desglose por depósito
  - Verifica información completa de cada depósito

- `test_visualizar_stock_por_deposito_central/norte/sur()` - **CA2**
  - Valida que cada depósito muestre solo sus productos
  - Verifica cantidades específicas por depósito
  - Confirma filtrado correcto de productos

- `test_lista_productos_incluye_nombre_y_stock()` - **CA3**
  - Valida formato de respuesta de lista de productos
  - Confirma campos obligatorios presentes

- `test_lista_productos_por_deposito_incluye_nombre_y_stock()` - **CA3**
  - Valida formato de respuesta por depósito
  - Confirma información adicional (categoría, precio, estados de stock)

#### Tests Adicionales:
- `test_filtrar_productos_por_deposito()` - Filtrado por depósito
- `test_deposito_inexistente()` - Manejo de errores
- `test_estadisticas_productos_stock_total()` - Estadísticas generales
- `test_autenticacion_requerida()` - Seguridad básica

### 2. `StockVisualizationEdgeCasesTestCase` - Casos Edge
**Objetivo**: Validar comportamiento en situaciones límite

#### Tests Implementados:
- `test_producto_sin_stock_en_ningun_deposito()` - Productos sin stock
- `test_deposito_sin_productos()` - Depósitos vacíos
- `test_producto_inactivo_no_aparece_en_deposito()` - Filtrado de inactivos
- `test_stock_con_cantidades_grandes()` - Manejo de cantidades grandes

### 3. `StockVisualizationSecurityTestCase` - Tests de Seguridad
**Objetivo**: Identificar vulnerabilidades de seguridad

#### Tests Críticos:
- `test_acceso_solo_depositos_propios()` - **CRÍTICO**
  - ⚠️ **Detecta vulnerabilidad**: Vista permite acceso a depósitos ajenos
  - Falla intencionalmente si encuentra el bug de seguridad
  - Documenta la corrección necesaria

- `test_listado_productos_solo_muestra_stock_propio()` - **IMPORTANTE**
  - Verifica que el cálculo de stock se filtre por supermercado
  - Detecta si se está mostrando stock global vs stock propio

### 4. `StockVisualizationIntegrationTestCase` - Tests de Integración
**Objetivo**: Validar flujo completo del usuario

#### Test Principal:
- `test_flujo_completo_visualizacion_stock()` - **Flujo E2E**
  - Simula el recorrido completo de un administrador
  - Valida consistencia entre todas las vistas
  - Verifica cálculos en diferentes contextos

## APIs Testeadas

### GET `/productos/`
- **Propósito**: Lista productos con stock total
- **Campos validados**: `nombre`, `stock_total`, `categoria_nombre`, `depositos_count`
- **Filtros testeados**: Por depósito, categoría, búsqueda

### GET `/productos/{id}/`
- **Propósito**: Detalle de producto con desglose completo
- **Campos validados**: `stock_total`, `stocks` (array de depósitos)
- **Validaciones**: Suma correcta, información por depósito

### GET `/productos/deposito/{deposito_id}/`
- **Propósito**: Productos en depósito específico
- **Campos validados**: `nombre`, `cantidad`, `categoria`, `tiene_stock`, `stock_bajo`
- **Seguridad**: ⚠️ **Vulnerabilidad detectada** - No valida ownership

### GET `/productos/estadisticas/`
- **Propósito**: Estadísticas generales
- **Campos validados**: `total_productos`, `productos_sin_stock`, `stock_por_categoria`

## Datos de Test

### Setup Estándar:
- **3 Categorías**: Bebidas, Lácteos, Limpieza
- **3 Depósitos**: Central, Norte, Sur
- **4 Productos**: Agua, Leche, Detergente, Yogur
- **Stocks Variados**: Diferentes distribuciones por depósito

### Escenarios de Stock:
- **Agua**: 150 total (50+75+25) - En todos los depósitos
- **Leche**: 80 total (30+50) - Solo Central y Norte
- **Detergente**: 20 total - Solo Central
- **Yogur**: 0 total - Sin stock (edge case)

## Vulnerabilidades Identificadas

### 🔴 CRÍTICA: Vista `productos_por_deposito`
**Problema**: No valida que el depósito pertenezca al usuario autenticado

**Impacto**: Administrador puede ver stock de cualquier supermercado

**Test que lo detecta**: `test_acceso_solo_depositos_propios()`

**Corrección requerida**:
```python
# En productos/views.py, función productos_por_deposito
deposito = get_object_or_404(Deposito, id=deposito_id, supermercado=request.user)
```

### 🟡 POTENCIAL: Cálculo de stock total
**Problema**: Posible inclusión de stock de otros supermercados

**Test que lo detecta**: `test_listado_productos_solo_muestra_stock_propio()`

**Verificación**: Confirmar que el cálculo se filtre por supermercado

## Configuración de Ejecución

### Comando de Ejecución:
```bash
python manage.py test test_hu_visualizacion_stock -v 2 --settings=appproductos.settings_test
```

### Configuración Requerida:
- **Base de datos**: SQLite (configurada en `settings_test.py`)
- **Entorno virtual**: `backend_env` activado
- **Dependencias**: Django, DRF, pytest

## Resultados Esperados

### Tests que DEBEN Pasar:
- Todos los tests de funcionalidad básica (CA1, CA2, CA3)
- Tests de casos edge
- Tests de integración
- Test de autenticación

### Tests que PUEDEN Fallar (Intencionalmente):
- `test_acceso_solo_depositos_propios()` - Si existe la vulnerabilidad
- `test_listado_productos_solo_muestra_stock_propio()` - Si hay filtrado incorrecto

## Interpretación de Resultados

### ✅ Si todos pasan:
- La funcionalidad está completamente implementada
- No hay vulnerabilidades de seguridad detectadas
- El sistema cumple todos los criterios de aceptación

### ❌ Si fallan tests de seguridad:
- **ACCIÓN REQUERIDA**: Corregir vulnerabilidades antes de despliegue
- Los tests documentan exactamente qué corregir
- Re-ejecutar después de correcciones

### ⚠️ Si fallan tests de funcionalidad:
- Revisar implementación de las vistas
- Verificar configuración de URLs
- Confirmar estructura de modelos

## Mantenimiento

### Cuando agregar nuevos tests:
- Nuevas funcionalidades de stock
- Cambios en la estructura de datos
- Reportes de bugs en producción
- Nuevos requisitos de seguridad

### Cuando actualizar tests existentes:
- Cambios en APIs existentes
- Modificaciones en criterios de aceptación
- Nuevos campos en respuestas
- Cambios en reglas de negocio

## Archivos Relacionados

- `productos/models.py` - Modelos testeados
- `productos/views.py` - Vistas testeadas (⚠️ Con vulnerabilidad)
- `productos/serializers.py` - Serializers testeados
- `productos/urls.py` - URLs testeadas
- `inventario/models.py` - Modelo Deposito
- `appproductos/settings_test.py` - Configuración de testing