from .settings import *  # noqa
from pathlib import Path

# Usar SQLite para pruebas para evitar requerir permisos en PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# Ubicación de media para pruebas
MEDIA_ROOT = BASE_DIR / 'test_media'

# Permitir todos los orígenes en pruebas
CORS_ALLOW_ALL_ORIGINS = True
