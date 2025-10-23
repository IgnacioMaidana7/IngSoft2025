# 📋 Scripts de Precarga del Backend - Orden de Ejecución

Esta guía muestra **todos los comandos necesarios** para configurar el backend de IngSoft2025 desde cero en una PC nueva.

---

## 🚀 Configuración Inicial (Solo Primera Vez)

### 1. Crear y Activar Entorno Virtual

```powershell
cd c:\Users\TU_USUARIO\Documents\GitHub\IngSoft2025\backend
python -m venv backend_env
.\backend_env\Scripts\Activate.ps1
```

### 2. Instalar Dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno (.env)

Crear archivo `.env` en `backend/` con:

```env
# Database Configuration
DB_NAME=ingsoft2025_db
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_POSTGRESQL
DB_HOST=localhost
DB_PORT=5432

# Django Secret Key
SECRET_KEY=django-insecure-cambiar-en-produccion-12345

# Debug Mode
DEBUG=True

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Reconocimiento API
RECOGNITION_API_URL=http://localhost:8080
```

---

## 📦 Base de Datos PostgreSQL

### 1. Crear Base de Datos

```sql
-- Ejecutar en psql o pgAdmin
CREATE DATABASE ingsoft2025_db;
```

O desde PowerShell:

```powershell
psql -U postgres -c "CREATE DATABASE ingsoft2025_db;"
```

### 2. Verificar Conexión

```powershell
python manage.py check
```

**Salida esperada:** `System check identified no issues (0 silenced).`

---

## 🔄 Migraciones de Base de Datos

### 1. Crear Migraciones

```powershell
python manage.py makemigrations
```

### 2. Aplicar Migraciones

```powershell
python manage.py migrate
```

**Salida esperada:**
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying productos.0001_initial... OK
  Applying inventario.0001_initial... OK
  ...
```

---

## 👤 Crear Superusuario (Administrador Principal)

```powershell
python manage.py createsuperuser
```

**Te pedirá:**
- Username: `admin` (o el que prefieras)
- Email: `admin@example.com`
- Password: (elige una contraseña segura)

---

## 🎯 SCRIPTS DE PRECARGA (LO IMPORTANTE)

### 1. ✅ Crear Productos de Reconocimiento

**Este es el comando MÁS IMPORTANTE** - Crea los 4 productos que la IA puede reconocer:

```powershell
python manage.py crear_productos_reconocimiento
```

**¿Qué hace?**
- ✅ Crea 4 productos en la base de datos:
  - Fritolim Aceite en Aerosol ($680)
  - Desodorante Nivea 150ml ($890)
  - Puré de Tomate Noel 530g ($450)
  - Raid Insecticida 233g ($1450)
- ✅ Crea las categorías necesarias (Alimentos, Cuidado Personal, Limpieza)
- ✅ Inicializa los productos con **stock 0**
- ✅ Actualiza automáticamente `product_mapping.json` en el proyecto de la API

**Salida esperada:**
```
🚀 Iniciando creación de productos para reconocimiento...
  ✅ Categoría creada: Alimentos
  ✅ Producto creado: Fritolim Aceite en Aerosol (ID: 1)
  ✅ Categoría creada: Cuidado Personal
  ✅ Producto creado: Desodorante Nivea 150ml (ID: 2)
  ✅ Producto creado: Puré de Tomate Noel 530g (ID: 3)
  ✅ Categoría creada: Limpieza
  ✅ Producto creado: Raid Insecticida 233g (ID: 4)

✅ Archivo product_mapping.json actualizado
✅ ¡Proceso completado exitosamente!
```

**⚠️ IMPORTANTE:** 
- Ejecuta este comando **SOLO UNA VEZ** por base de datos
- Si lo ejecutas nuevamente, detecta que los productos ya existen y no los duplica
- Los IDs generados (1, 2, 3, 4) se mapean automáticamente en la API de reconocimiento

---

### 2. ⏸️ Resetear Stock (Opcional)

Si necesitas limpiar el stock de los productos de reconocimiento:

```powershell
python manage.py resetear_stock_reconocimiento --confirmar
```

**¿Cuándo usarlo?**
- Para testing/desarrollo
- Cuando quieras empezar de cero con el stock
- Si migraste datos y quieres limpiar

**¿Qué hace?**
- ✅ Resetea el stock a 0 de los 4 productos de reconocimiento
- ✅ Afecta TODOS los depósitos que tengan estos productos
- ✅ Muestra verificación del resultado

**Salida esperada:**
```
⚠️  RESETEAR STOCK A 0

Se resetearán 4 productos:
  • Desodorante Nivea 150ml (Stock actual: 17)
  • Fritolim Aceite en Aerosol (Stock actual: 10)
  • Puré de Tomate Noel 530g (Stock actual: 10)
  • Raid Insecticida 233g (Stock actual: 6)

✅ Stock reseteado exitosamente
   5 registros de stock actualizados a 0
```

**Opciones:**
```powershell
# Con confirmación interactiva
python manage.py resetear_stock_reconocimiento

# Sin preguntar (automático)
python manage.py resetear_stock_reconocimiento --confirmar

# Resetear TODOS los productos (peligroso)
python manage.py resetear_stock_reconocimiento --todos --confirmar
```

---

## 🖥️ Iniciar el Servidor

```powershell
python manage.py runserver
```

**Servidor corriendo en:** http://127.0.0.1:8000/

---

## ✅ Verificación Post-Precarga

### 1. Verificar Productos Creados

**Opción A: Django Admin**
```
http://localhost:8000/admin
Login: admin / tu_password
Navega a: Productos → Productos
```

**Opción B: Django Shell**
```powershell
python manage.py shell
```

```python
from productos.models import Producto
productos = Producto.objects.all()
for p in productos:
    print(f"ID: {p.id} - {p.nombre} - ${p.precio} - Categoría: {p.categoria.nombre}")
exit()
```

**Salida esperada:**
```
ID: 1 - Fritolim Aceite en Aerosol - $680.00 - Categoría: Alimentos
ID: 2 - Desodorante Nivea 150ml - $890.00 - Categoría: Cuidado Personal
ID: 3 - Puré de Tomate Noel 530g - $450.00 - Categoría: Alimentos
ID: 4 - Raid Insecticida 233g - $1450.00 - Categoría: Limpieza
```

### 2. Verificar Categorías

```powershell
python manage.py shell -c "from productos.models import Categoria; [print(f'{c.id}: {c.nombre}') for c in Categoria.objects.all()]"
```

**Salida esperada:**
```
1: Alimentos
2: Cuidado Personal
3: Limpieza
```

### 3. Verificar Stock

```powershell
python manage.py shell -c "from productos.models import ProductoDeposito; total = ProductoDeposito.objects.count(); print(f'Total registros de stock: {total}')"
```

**Salida esperada:** `Total registros de stock: 0` (correcto, se crean sin stock)

---

## 📋 Checklist de Precarga Completa

Usa este checklist para asegurarte de que todo está configurado:

- [ ] Base de datos PostgreSQL creada (`ingsoft2025_db`)
- [ ] Archivo `.env` configurado con credenciales correctas
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Migraciones aplicadas (`python manage.py migrate`)
- [ ] Superusuario creado (`python manage.py createsuperuser`)
- [ ] ✅ **Productos de reconocimiento creados** (`python manage.py crear_productos_reconocimiento`)
- [ ] Servidor iniciado correctamente (`python manage.py runserver`)
- [ ] Productos verificados en Admin (4 productos visibles)
- [ ] API de reconocimiento configurada (puerto 8080)
- [ ] Frontend Next.js corriendo (puerto 3000)

---

## 🔄 Comandos de Uso Diario

### Iniciar Servicios

```powershell
# Terminal 1: Backend Django
cd c:\Users\TU_USUARIO\Documents\GitHub\IngSoft2025\backend
.\backend_env\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2: API de Reconocimiento
cd c:\Users\TU_USUARIO\Documents\GitHub\shelf-product-identifier
.\.venv\Scripts\Activate.ps1
python server.py

# Terminal 3: Frontend Next.js
cd c:\Users\TU_USUARIO\Documents\GitHub\IngSoft2025\frontend
npm run dev
```

### Crear Nuevos Datos

```powershell
# Crear un depósito (desde el frontend o admin)
http://localhost:3000/depositos

# Agregar stock a un producto (desde el frontend)
http://localhost:3000/productos
# Click en "Ver/Editar" → Agregar Stock
```

---

## 🎯 Resumen de Scripts de Precarga

### Scripts Obligatorios (Ejecutar en este orden):

1. **Migraciones:**
   ```powershell
   python manage.py migrate
   ```

2. **Superusuario:**
   ```powershell
   python manage.py createsuperuser
   ```

3. **Productos de Reconocimiento:**
   ```powershell
   python manage.py crear_productos_reconocimiento
   ```

### Scripts Opcionales:

4. **Resetear Stock (si necesitas):**
   ```powershell
   python manage.py resetear_stock_reconocimiento --confirmar
   ```

---

## 📝 Notas Importantes

### ✅ Ventajas del Sistema Actual:

1. **Productos Globales**: Los 4 productos de reconocimiento son compartidos entre todos los usuarios
2. **Stock Aislado**: Cada usuario maneja su propio stock en sus propios depósitos
3. **Sin Duplicación**: El comando `crear_productos_reconocimiento` detecta si ya existen y no los duplica
4. **Mapeo Automático**: El `product_mapping.json` se actualiza automáticamente con los IDs correctos
5. **Stock Inicial Cero**: Los productos se crean sin stock, el usuario lo agrega según necesite

### ⚠️ Consideraciones:

- **NO ejecutes** `crear_productos_reconocimiento` múltiples veces en la misma base de datos (detecta duplicados pero es innecesario)
- **SI migras** a una nueva PC, ejecuta `crear_productos_reconocimiento` UNA vez en la nueva base de datos
- **Los IDs de Django** (1, 2, 3, 4) pueden variar si creaste otros productos antes, el mapeo se ajusta automáticamente
- **El archivo `.env`** NO debe compartirse (tiene credenciales sensibles)

---

## 🐛 Problemas Comunes

### "django.db.utils.OperationalError: FATAL: database does not exist"
```powershell
# Crear la base de datos primero
psql -U postgres -c "CREATE DATABASE ingsoft2025_db;"
```

### "ModuleNotFoundError: No module named 'X'"
```powershell
# Activar el entorno virtual
.\backend_env\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "CommandError: product_mapping.json no encontrado"
- El comando intenta actualizar el archivo pero no es crítico
- Puedes copiar el archivo manualmente o ejecutar el comando desde la API

### "Ya existe un producto con este nombre"
- Normal: el comando detectó productos duplicados
- Los productos existentes no se modifican
- Solo se actualizan los IDs en el mapeo

---

## 📞 Soporte

Si encuentras problemas:

1. Verifica el checklist completo
2. Lee los mensajes de error del comando
3. Consulta `FIX_AISLAMIENTO_STOCK_USUARIOS.md` para entender el sistema de stock
4. Revisa `SISTEMA_MAPEO_PRODUCTOS.md` para entender el mapeo de IDs

---

## 🎉 ¡Listo!

Si completaste todos los pasos, tu backend está **100% configurado** y listo para:

- ✅ Reconocer productos con la cámara
- ✅ Gestionar stock por depósitos
- ✅ Registrar ventas
- ✅ Crear empleados y asignar roles
- ✅ Recibir notificaciones de stock bajo

**¡A programar! 🚀**
