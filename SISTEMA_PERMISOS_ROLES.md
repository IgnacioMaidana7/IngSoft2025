# 🔐 Sistema de Permisos y Roles en IngSoft2025

## 📋 Resumen Ejecutivo

Tu backend tiene un **sistema de roles jerárquico** con 3 niveles de acceso:

1. **👔 Administrador de Supermercado** - Acceso total
2. **📦 Reponedor** - Gestión de productos e inventario (solo su depósito)
3. **💰 Cajero** - Gestión de ventas (solo su depósito)

---

## 👥 Roles y Permisos

### 1. 👔 **Administrador de Supermercado**

**Tipo de Usuario:** `SupermercadoUser` (NO es `EmpleadoUser`)

**Permisos:**
- ✅ **Productos:** Crear, editar, eliminar productos
- ✅ **Stock:** Ver y gestionar stock en **TODOS los depósitos**
- ✅ **Empleados:** Crear, editar, eliminar empleados
- ✅ **Depósitos:** Gestionar múltiples depósitos
- ✅ **Ventas:** Ver todas las ventas del supermercado
- ✅ **Reportes:** Acceso completo a reportes y estadísticas
- ✅ **Notificaciones:** Recibe alertas de stock mínimo

**Código:**
```python
# En permissions.py
class IsSupermercadoAdmin(BasePermission):
    def has_permission(self, request, view):
        # Verificar que NO sea un empleado
        return not isinstance(request.user, EmpleadoUser)
```

**Acceso a APIs:**
- Todas las rutas con `@permission_classes([IsReponedorOrAdmin])`
- Todas las rutas con `@permission_classes([IsCajeroOrAdmin])`

---

### 2. 📦 **Reponedor**

**Tipo de Usuario:** `EmpleadoUser` con `puesto='REPONEDOR'`

**Permisos:**
- ✅ **Productos:** Ver, crear y editar productos
- ✅ **Stock:** Ver y gestionar stock **SOLO en su depósito asignado**
- ❌ **Stock otros depósitos:** NO puede ver ni modificar
- ✅ **Categorías:** Ver categorías disponibles
- ❌ **Empleados:** NO puede gestionar empleados
- ❌ **Ventas:** NO puede acceder a ventas
- ✅ **Notificaciones:** Recibe alertas de stock mínimo de su depósito

**Restricción de Depósito:**
```python
# En views.py
if isinstance(user, EmpleadoUser):
    emp = Empleado.objects.filter(email=user.email, supermercado=user.supermercado).first()
    if emp:
        stocks_qs = stocks_qs.filter(deposito=emp.deposito)
```

**Código:**
```python
# En permissions.py
class IsReponedor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            isinstance(request.user, EmpleadoUser) and
            request.user.puesto == 'REPONEDOR' and
            request.user.is_active
        )
```

**Acceso a APIs:**
- Todas las rutas con `@permission_classes([IsReponedorOrAdmin])`
- Limitado a su depósito asignado

---

### 3. 💰 **Cajero**

**Tipo de Usuario:** `EmpleadoUser` con `puesto='CAJERO'`

**Permisos:**
- ✅ **Ventas:** Crear y gestionar ventas
- ✅ **Productos (solo lectura):** Ver productos disponibles en su depósito
- ✅ **Reconocimiento:** Usar API de reconocimiento de productos
- ❌ **Stock:** NO puede modificar stock
- ❌ **Productos:** NO puede crear/editar/eliminar productos
- ❌ **Empleados:** NO puede gestionar empleados

**Código:**
```python
# En permissions.py
class IsCajero(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            isinstance(request.user, EmpleadoUser) and
            request.user.puesto == 'CAJERO' and
            request.user.is_active
        )
```

**Acceso a APIs:**
- Rutas con `@permission_classes([IsCajeroOrAdmin])`
- Ventas
- Reconocimiento de productos

---

## 📊 Matriz de Permisos

| Funcionalidad                    | Admin 👔 | Reponedor 📦 | Cajero 💰 |
|----------------------------------|----------|--------------|-----------|
| **Productos**                    |          |              |           |
| Ver productos                    | ✅       | ✅           | ✅ (lectura) |
| Crear productos                  | ✅       | ✅           | ❌        |
| Editar productos                 | ✅       | ✅           | ❌        |
| Eliminar productos               | ✅       | ✅           | ❌        |
| **Stock/Inventario**             |          |              |           |
| Ver stock (todos los depósitos)  | ✅       | ❌           | ❌        |
| Ver stock (su depósito)          | ✅       | ✅           | ✅        |
| Modificar stock (todos depósitos)| ✅       | ❌           | ❌        |
| Modificar stock (su depósito)    | ✅       | ✅           | ❌        |
| **Ventas**                       |          |              |           |
| Ver todas las ventas             | ✅       | ❌           | ❌        |
| Crear ventas                     | ✅       | ❌           | ✅        |
| Ver sus ventas                   | ✅       | ❌           | ✅        |
| **Reconocimiento de Productos**  |          |              |           |
| Usar API reconocimiento          | ✅       | ❌           | ✅        |
| **Empleados**                    |          |              |           |
| Crear empleados                  | ✅       | ❌           | ❌        |
| Editar empleados                 | ✅       | ❌           | ❌        |
| Eliminar empleados               | ✅       | ❌           | ❌        |
| **Depósitos**                    |          |              |           |
| Crear/editar depósitos           | ✅       | ❌           | ❌        |
| Ver depósitos                    | ✅       | ✅ (solo el suyo) | ✅ (solo el suyo) |
| **Notificaciones**               |          |              |           |
| Alertas de stock mínimo          | ✅       | ✅ (su depósito) | ❌        |

---

## 🔍 Respuesta a tu Pregunta

> **"¿Solo el administrador puede agregar productos en los depósitos?"**

### Respuesta: **NO, tanto Administradores como Reponedores pueden agregar productos**

### **Diferencias:**

#### 👔 **Administrador:**
```python
# Puede agregar stock en CUALQUIER depósito
POST /api/productos/1/stock/
{
  "deposito": 1,      # ← Puede elegir cualquier depósito
  "cantidad": 50,
  "cantidad_minima": 10
}
```

#### 📦 **Reponedor:**
```python
# Solo puede agregar stock en SU depósito asignado
POST /api/productos/1/stock/
{
  # El sistema FUERZA automáticamente su depósito
  "cantidad": 50,
  "cantidad_minima": 10
}

# Si intenta especificar otro depósito, el sistema lo ignora:
if isinstance(request.user, EmpleadoUser):
    emp = Empleado.objects.filter(email=request.user.email).first()
    data['deposito'] = emp.deposito.id  # ← Forzado
```

---

## 🏗️ Flujo de Creación de Productos

### **Escenario 1: Admin crea producto**

```
1. Admin hace login → SupermercadoUser
2. Crea producto:
   POST /api/productos/
   {
     "nombre": "Coca Cola 500ml",
     "categoria": 1,
     "precio": 150.00,
     "descripcion": "..."
   }
   ✅ Producto creado (ID: 10)

3. Admin asigna stock en depósito 1:
   POST /api/productos/10/stock/
   {
     "deposito": 1,
     "cantidad": 100,
     "cantidad_minima": 20
   }
   ✅ Stock creado en Depósito 1

4. Admin asigna stock en depósito 2:
   POST /api/productos/10/stock/
   {
     "deposito": 2,
     "cantidad": 50,
     "cantidad_minima": 10
   }
   ✅ Stock creado en Depósito 2
```

### **Escenario 2: Reponedor crea producto**

```
1. Reponedor hace login → EmpleadoUser (puesto='REPONEDOR', deposito_id=1)
2. Crea producto:
   POST /api/productos/
   {
     "nombre": "Sprite 500ml",
     "categoria": 1,
     "precio": 140.00,
     "descripcion": "..."
   }
   ✅ Producto creado (ID: 11)

3. Reponedor asigna stock:
   POST /api/productos/11/stock/
   {
     "cantidad": 80,
     "cantidad_minima": 15
     # NO especifica depósito → Sistema usa su depósito (1)
   }
   ✅ Stock creado SOLO en SU Depósito 1

4. Reponedor intenta ver stock de depósito 2:
   GET /api/productos/11/stock/
   ❌ Solo ve stock de su depósito (1)

5. Reponedor intenta agregar stock en depósito 2:
   POST /api/productos/11/stock/
   {
     "deposito": 2,     # ← Intenta especificar depósito 2
     "cantidad": 50
   }
   ✅ Creado, pero el sistema IGNORA el depósito 2
       y lo crea en su depósito (1) automáticamente
```

---

## 🛡️ Seguridad del Sistema

### **Protecciones Implementadas:**

1. **Aislamiento por Depósito:**
```python
# Reponedores solo ven su depósito
if isinstance(user, EmpleadoUser):
    emp = Empleado.objects.filter(email=user.email).first()
    stocks_qs = stocks_qs.filter(deposito=emp.deposito)
```

2. **Forzado de Depósito:**
```python
# Reponedores no pueden elegir depósito
if isinstance(request.user, EmpleadoUser):
    data['deposito'] = emp.deposito.id  # Forzado por el sistema
```

3. **Verificación de Permisos:**
```python
# En cada endpoint
@permission_classes([IsReponedorOrAdmin])
def gestionar_stock_producto(request, producto_id):
    # Validaciones de permisos
```

4. **Validación de Propiedad:**
```python
# Verificar que el empleado pertenece al supermercado
if stock.deposito_id != emp.deposito_id:
    return Response({"detail": "No tiene acceso"}, status=403)
```

---

## 🎯 Casos de Uso Reales

### **Caso 1: Stock Bajo - Reponedor Recibe Alerta**
```
1. Stock de "Coca Cola" baja de mínimo en Depósito 1
2. Sistema envía notificación:
   - ✅ Admin del supermercado
   - ✅ Reponedores asignados al Depósito 1
   - ❌ Reponedores de otros depósitos
3. Reponedor de Dep. 1 ve notificación y repone stock
```

### **Caso 2: Admin Consulta Stock Global**
```
GET /api/productos/1/stock-completo/
Respuesta (Admin):
{
  "producto": {"id": 1, "nombre": "Coca Cola"},
  "stocks": [
    {"deposito_id": 1, "cantidad": 5, "stock_bajo": true},
    {"deposito_id": 2, "cantidad": 50, "stock_bajo": false},
    {"deposito_id": 3, "cantidad": 0, "tiene_stock": false}
  ]
}
```

### **Caso 3: Reponedor Consulta Stock (Solo Su Depósito)**
```
GET /api/productos/1/stock-completo/
Respuesta (Reponedor Dep. 1):
{
  "producto": {"id": 1, "nombre": "Coca Cola"},
  "stocks": [
    {"deposito_id": 1, "cantidad": 5, "stock_bajo": true}
    # No ve los otros depósitos
  ]
}
```

### **Caso 4: Cajero Usa Reconocimiento**
```
1. Cajero toma foto de productos
2. API reconoce: Fritolim (ID Django: 1)
3. Backend consulta stock del depósito del cajero:
   {
     "ingsoft_product_id": 1,
     "nombre_db": "Fritolim",
     "precio_db": "680.00",
     "stock_disponible": 50  ← Stock del depósito del cajero
   }
4. Cajero agrega a la venta
```

---

## 📝 Configuración Inicial Recomendada

### **1. Crear Depósitos**
```python
# Admin crea 3 depósitos
POST /api/depositos/
{"nombre": "Depósito Central", "direccion": "..."}
POST /api/depositos/
{"nombre": "Depósito Norte", "direccion": "..."}
POST /api/depositos/
{"nombre": "Depósito Sur", "direccion": "..."}
```

### **2. Crear Empleados**
```python
# Admin crea reponedores y cajeros
POST /api/empleados/
{
  "nombre": "Juan Pérez",
  "email": "juan@super.com",
  "puesto": "REPONEDOR",
  "deposito_id": 1  # ← Asignado al Depósito Central
}
```

### **3. Crear Productos (Admin o Reponedores)**
```python
# Cualquiera puede crear productos
POST /api/productos/
{"nombre": "Coca Cola", "categoria": 1, "precio": 150}
```

### **4. Asignar Stock**
```python
# Admin: puede asignar en cualquier depósito
# Reponedor: solo en su depósito asignado
POST /api/productos/1/stock/
{"cantidad": 100, "cantidad_minima": 20}
```

---

## ⚠️ Limitaciones y Consideraciones

1. **Un Reponedor = Un Depósito**
   - Cada reponedor está asignado a un solo depósito
   - No puede trabajar en múltiples depósitos simultáneamente

2. **Productos sin Depósito**
   - Un producto puede existir sin stock en ningún depósito
   - No se puede eliminar un producto con stock > 0

3. **Cajeros y Stock**
   - Los cajeros **ven** el stock pero **NO pueden modificarlo**
   - Solo pueden crear ventas

4. **Notificaciones Automáticas**
   - Se envían al guardar stock (signal `post_save`)
   - Solo a reponedores del depósito específico

---

## 🚀 Resumen Final

### **¿Quién puede agregar productos en depósitos?**

| Rol         | Crear Producto | Agregar Stock | Depósitos Permitidos |
|-------------|----------------|---------------|----------------------|
| Admin 👔    | ✅             | ✅            | Todos                |
| Reponedor 📦| ✅             | ✅            | Solo el suyo         |
| Cajero 💰   | ❌             | ❌            | Ninguno (solo lee)   |

### **Flujo Recomendado:**
1. **Admin** crea la estructura (depósitos, categorías, empleados)
2. **Reponedores** crean productos y gestionan stock de sus depósitos
3. **Cajeros** usan productos para ventas
4. **Admin** supervisa todo desde una vista global

**Tu sistema está bien diseñado con separación de responsabilidades y seguridad por depósito.** ✅
