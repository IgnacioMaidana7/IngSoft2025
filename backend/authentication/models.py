from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
import re


def validate_cuil(value):
    """Validador personalizado para CUIL"""
    # Remover espacios y guiones
    cuil_clean = re.sub(r'[\s-]', '', value)
    
    # Verificar que solo contenga números
    if not cuil_clean.isdigit():
        raise ValidationError("El CUIL debe contener solo números")
    
    # Verificar que tenga exactamente 11 dígitos
    if len(cuil_clean) != 11:
        raise ValidationError("El CUIL debe tener exactamente 11 dígitos")
    
    return cuil_clean


def validate_logo_size(value):
    """Validador para el tamaño del logo (máximo 1MB)"""
    filesize = value.size
    if filesize > 1 * 1024 * 1024:  # 1MB
        raise ValidationError("El logo no puede ser mayor a 1MB")


class User(AbstractUser):
    """Modelo de usuario personalizado para el sistema"""
    
    # Información del supermercado
    nombre_supermercado = models.CharField(
        max_length=200, 
        verbose_name="Nombre del Supermercado",
        help_text="Nombre completo del supermercado"
    )
    
    logo = models.ImageField(
        upload_to='logos/', 
        null=True, 
        blank=True,
        verbose_name="Logo del Supermercado",
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg']),
            validate_logo_size
        ],
        help_text="Logo en formato JPG, máximo 1MB"
    )
    
    cuil = models.CharField(
        max_length=11, 
        unique=True, 
        verbose_name="CUIL",
        validators=[validate_cuil],
        help_text="CUIL sin espacios ni guiones, solo números"
    )
    
    # Ubicación
    provincia = models.CharField(max_length=100, verbose_name="Provincia")
    localidad = models.CharField(max_length=100, verbose_name="Localidad")
    
    # Email ya está incluido en AbstractUser, pero podemos sobrescribirlo
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Correo electrónico válido"
    )
    
    # Metadatos
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    # Usar email como campo de autenticación en lugar de username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nombre_supermercado', 'cuil', 'provincia', 'localidad']
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Limpiar CUIL al guardar
        if self.cuil:
            self.cuil = validate_cuil(self.cuil)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.email} - {self.nombre_supermercado}"
