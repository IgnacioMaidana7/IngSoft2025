# Setup del Backend - Django

## Configuración del Entorno Virtual

### Crear el entorno virtual (solo primera vez)
```powershell
# Navegar a la carpeta del backend
cd "C:\Users\ignac\OneDrive\Documentos\Facultad\Ingeniería de Software\tpIntegrador\backend"

# Crear entorno virtual
python -m venv backend_env
```

### Activar el entorno virtual
```powershell
# Permitir ejecución de scripts (si está bloqueado)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Activar el entorno
.\backend_env\Scripts\Activate.ps1
```

### Instalar dependencias
```powershell
# Actualizar herramientas básicas
python -m pip install -U pip setuptools wheel

# Instalar dependencias del proyecto
python -m pip install -r .\requirements.txt
```

## Comandos útiles de Django

### Verificar configuración
```powershell
python manage.py check
```

### Ejecutar migraciones
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Crear superusuario
```powershell
python manage.py createsuperuser
```

### Ejecutar servidor de desarrollo
```powershell
python manage.py runserver
```

## Notas importantes

- **Python 3.13**: Las versiones de `psycopg2-binary` y `Pillow` han sido actualizadas para compatibilidad.
- **Entorno virtual**: Siempre activar el entorno virtual antes de trabajar con Django.
- **Base de datos**: Configurada para PostgreSQL. Verificar configuración en `.env`.

## Dependencias instaladas

- Django 4.2.7
- Django REST Framework 3.14.0
- psycopg2-binary (>=2.9.10)
- Pillow (>=10.4.0)
- django-cors-headers
- djangorestframework-simplejwt
- django-allauth
- python-decouple
- django-extensions
- drf-spectacular
- pytz
- django-filter
