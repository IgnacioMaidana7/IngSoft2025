from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
import re

User = get_user_model()


def validate_dni(value):
    """Validador personalizado para DNI"""
    # Remover espacios y puntos
    dni_clean = re.sub(r'[\s.]', '', str(value))
    
    # Verificar que solo contenga números
    if not dni_clean.isdigit():
        raise ValidationError("El DNI debe contener solo números")
    
    # Verificar que tenga entre 7 y 8 dígitos
    if len(dni_clean) < 7 or len(dni_clean) > 8:
        raise ValidationError("El DNI debe tener entre 7 y 8 dígitos")
    
    return dni_clean


class Deposito(models.Model):
    """Modelo para representar los depósitos del supermercado"""
    
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Depósito",
        help_text="Nombre del depósito (ej: Depósito Central, Sucursal Norte)"
    )
    
    direccion = models.CharField(
        max_length=200,
        verbose_name="Dirección",
        help_text="Dirección completa del depósito"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción opcional del depósito"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el depósito está activo"
    )
    
    supermercado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='depositos',
        verbose_name="Supermercado"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Depósito"
        verbose_name_plural = "Depósitos"
        unique_together = ['nombre', 'direccion', 'supermercado']
    
    def __str__(self):
        return f"{self.nombre} - {self.supermercado.nombre_supermercado}"


class Empleado(models.Model):
    """Modelo para representar los empleados del supermercado"""
    
    ROLES_CHOICES = [
        ('CAJERO', 'Cajero'),
        ('REPONEDOR', 'Reponedor'),
    ]
    
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre",
        help_text="Nombre del empleado"
    )
    
    apellido = models.CharField(
        max_length=100,
        verbose_name="Apellido",
        help_text="Apellido del empleado"
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name="Correo Electrónico",
        validators=[EmailValidator()],
        help_text="Correo electrónico único del empleado"
    )
    
    dni = models.CharField(
        max_length=8,
        unique=True,
        verbose_name="DNI",
        validators=[validate_dni],
        help_text="DNI del empleado (sin puntos ni espacios)"
    )
    
    puesto = models.CharField(
        max_length=20,
        choices=ROLES_CHOICES,
        verbose_name="Puesto",
        help_text="Rol del empleado en el supermercado"
    )
    
    deposito = models.ForeignKey(
        Deposito,
        on_delete=models.CASCADE,
        related_name='empleados',
        verbose_name="Depósito",
        help_text="Depósito donde trabaja el empleado"
    )
    
    supermercado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='empleados',
        verbose_name="Supermercado"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el empleado está activo"
    )
    
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        unique_together = ['email', 'supermercado']
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Limpiar DNI al guardar
        if self.dni:
            self.dni = validate_dni(self.dni)
        
        # Verificar que el depósito pertenezca al mismo supermercado
        if self.deposito and self.supermercado:
            if self.deposito.supermercado != self.supermercado:
                raise ValidationError("El depósito debe pertenecer al mismo supermercado")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_nombre_completo(self):
        """Retorna el nombre completo del empleado"""
        return f"{self.nombre} {self.apellido}"
    
    def __str__(self):
        return f"{self.get_nombre_completo()} - {self.puesto} ({self.supermercado.nombre_supermercado})"
