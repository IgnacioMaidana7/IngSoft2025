from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


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
