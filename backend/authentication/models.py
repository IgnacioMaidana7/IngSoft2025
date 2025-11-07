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
    
    # Rol del usuario (por defecto es administrador del supermercado)
    rol = models.CharField(
        max_length=50,
        default='ADMIN',
        verbose_name="Rol",
        help_text="Rol del usuario en el sistema"
    )
    
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
        # Solo validar CUIL, no el logo (Django lo valida automáticamente)
        if self.cuil:
            self.cuil = validate_cuil(self.cuil)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.email} - {self.nombre_supermercado}"


class EmpleadoUser(AbstractUser):
    """Modelo de usuario para empleados del supermercado"""
    
    ROLES_CHOICES = [
        ('CAJERO', 'Cajero'),
        ('REPONEDOR', 'Reponedor'),
    ]
    
    # Información personal
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")
    
    # Información laboral
    puesto = models.CharField(
        max_length=20,
        choices=ROLES_CHOICES,
        verbose_name="Puesto"
    )
    
    # Relación con el supermercado administrador
    supermercado = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='empleados_usuarios',
        verbose_name="Supermercado"
    )
    
    # Relación con el depósito
    deposito = models.ForeignKey(
        'inventario.Deposito',
        on_delete=models.CASCADE,
        related_name='empleados_usuarios',
        verbose_name="Depósito",
        help_text="Depósito donde trabaja el empleado"
    )
    
    # Email ya está incluido en AbstractUser
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Correo electrónico del empleado"
    )
    
    # Usar email como campo de autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nombre', 'apellido', 'dni', 'puesto']
    
    # Metadatos
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Usuario Empleado"
        verbose_name_plural = "Usuarios Empleados"
        # Evitar conflictos con el modelo User principal
        db_table = 'authentication_empleado_user'
    
    # Evitar conflictos con el modelo User principal
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='empleado_users_set',
        related_query_name='empleado_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='empleado_users_set',
        related_query_name='empleado_user',
    )
    
    def get_nombre_completo(self):
        """Retorna el nombre completo del empleado"""
        return f"{self.nombre} {self.apellido}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar DNI
        if self.dni:
            dni_clean = re.sub(r'[\s.]', '', str(self.dni))
            if not dni_clean.isdigit():
                raise ValidationError({"dni": "El DNI debe contener solo números"})
            if len(dni_clean) < 7 or len(dni_clean) > 8:
                raise ValidationError({"dni": "El DNI debe tener entre 7 y 8 dígitos"})
            self.dni = dni_clean
        
        # Verificar que el depósito pertenezca al mismo supermercado
        if self.deposito and self.supermercado:
            if self.deposito.supermercado != self.supermercado:
                raise ValidationError("El depósito debe pertenecer al mismo supermercado")
    
    def __str__(self):
        return f"{self.get_nombre_completo()} - {self.puesto} ({self.supermercado.nombre_supermercado})"
