from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

class Oferta(models.Model):
    TIPO_DESCUENTO_CHOICES = [
        ('porcentaje', 'Porcentaje'),
        ('monto_fijo', 'Monto Fijo'),
    ]
    
    ESTADO_CHOICES = [
        ('proxima', 'Próxima'),
        ('activa', 'Activa'),
        ('expirada', 'Expirada'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la oferta")
    descripcion = models.TextField(verbose_name="Descripción", blank=True, null=True)
    tipo_descuento = models.CharField(
        max_length=20, 
        choices=TIPO_DESCUENTO_CHOICES, 
        verbose_name="Tipo de descuento"
    )
    valor_descuento = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Valor del descuento"
    )
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateTimeField(verbose_name="Fecha de fin")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Oferta"
        verbose_name_plural = "Ofertas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_descuento_display()}: {self.valor_descuento}"
    
    def clean(self):
        """Validaciones personalizadas"""
        if self.fecha_fin and self.fecha_inicio:
            if self.fecha_fin <= self.fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
        
        # Validar valor del descuento según el tipo
        if self.tipo_descuento == 'porcentaje':
            if self.valor_descuento > 100:
                raise ValidationError({
                    'valor_descuento': 'El descuento porcentual no puede ser mayor a 100%.'
                })
        elif self.tipo_descuento == 'monto_fijo':
            if self.valor_descuento <= 0:
                raise ValidationError({
                    'valor_descuento': 'El monto fijo debe ser mayor a 0.'
                })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def estado(self):
        """Calcula el estado actual de la oferta basado en las fechas"""
        ahora = timezone.now()
        
        if not self.activo:
            return 'expirada'
        
        if ahora < self.fecha_inicio:
            return 'proxima'
        elif self.fecha_inicio <= ahora <= self.fecha_fin:
            return 'activa'
        else:
            return 'expirada'
    
    def puede_editar(self):
        """Determina si la oferta puede ser editada (no expirada)"""
        return self.estado != 'expirada'
    
    def aplicar_descuento(self, monto):
        """Aplica el descuento al monto dado"""
        if self.estado != 'activa':
            return monto
        
        # Asegurar que trabajamos con Decimal
        if not isinstance(monto, Decimal):
            monto = Decimal(str(monto))
            
        if self.tipo_descuento == 'porcentaje':
            descuento = monto * (self.valor_descuento / Decimal('100'))
        else:  # monto_fijo
            descuento = min(self.valor_descuento, monto)
            
        resultado = monto - descuento
        return max(resultado, Decimal('0'))


class ProductoOferta(models.Model):
    """Modelo intermedio para relacionar productos con ofertas"""
    
    producto = models.ForeignKey('productos.Producto', on_delete=models.CASCADE, related_name='ofertas_aplicadas')
    oferta = models.ForeignKey(Oferta, on_delete=models.CASCADE, related_name='productos_asignados')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    precio_original = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio original")
    precio_con_descuento = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio con descuento")
    
    class Meta:
        verbose_name = "Producto en Oferta"
        verbose_name_plural = "Productos en Oferta"
        unique_together = ['producto', 'oferta']  # Un producto no puede tener la misma oferta duplicada
        ordering = ['-fecha_asignacion']
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.oferta.nombre}"
    
    def save(self, *args, **kwargs):
        """Calcular automáticamente el precio con descuento al guardar"""
        if not self.precio_con_descuento:
            self.precio_original = self.producto.precio
            # No convertir a float, mantener como Decimal
            self.precio_con_descuento = self.oferta.aplicar_descuento(self.precio_original)
        super().save(*args, **kwargs)
    
    @property
    def descuento_aplicado(self):
        """Calcula el monto del descuento aplicado"""
        return self.precio_original - self.precio_con_descuento
    
    @property
    def porcentaje_descuento(self):
        """Calcula el porcentaje de descuento aplicado"""
        if self.precio_original > 0:
            return ((self.precio_original - self.precio_con_descuento) / self.precio_original) * 100
        return 0
