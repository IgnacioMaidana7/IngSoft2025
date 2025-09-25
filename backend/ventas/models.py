from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from productos.models import Producto
from authentication.models import EmpleadoUser

User = get_user_model()


class Venta(models.Model):
    """Modelo para representar una venta realizada en el supermercado"""
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    numero_venta = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Venta",
        help_text="Número único de la venta"
    )
    
    cajero = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ventas_realizadas',
        verbose_name="Cajero",
        help_text="Usuario que realizó la venta (admin o empleado cajero)"
    )
    
    empleado_cajero = models.ForeignKey(
        EmpleadoUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_como_cajero',
        verbose_name="Empleado Cajero",
        help_text="Empleado específico que realizó la venta (solo si es empleado)"
    )
    
    cliente_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono del Cliente",
        help_text="Número de teléfono del cliente (opcional)"
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Subtotal"
    )
    
    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Descuento"
    )
    
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        verbose_name="Estado"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    fecha_completada = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Completada"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    
    ticket_pdf_generado = models.BooleanField(
        default=False,
        verbose_name="PDF Generado"
    )
    
    enviado_whatsapp = models.BooleanField(
        default=False,
        verbose_name="Enviado por WhatsApp"
    )

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"Venta {self.numero_venta} - {self.cajero} - ${self.total}"
    
    def calcular_total(self):
        """Calcula el total de la venta sumando todos los items"""
        total_items = sum(item.subtotal for item in self.items.all())
        self.subtotal = total_items
        self.total = self.subtotal - self.descuento
        return self.total
    
    def generar_numero_venta(self):
        """Genera un número único de venta"""
        import datetime
        from django.db.models import Max
        
        today = datetime.date.today()
        prefix = f"{today.strftime('%Y%m%d')}"
        
        # Obtener el último número de venta del día
        ultimo_numero = Venta.objects.filter(
            numero_venta__startswith=prefix
        ).aggregate(
            max_numero=Max('numero_venta')
        )['max_numero']
        
        if ultimo_numero:
            # Extraer el sufijo y incrementarlo
            sufijo = int(ultimo_numero[-4:]) + 1
        else:
            sufijo = 1
            
        self.numero_venta = f"{prefix}{sufijo:04d}"


class ItemVenta(models.Model):
    """Modelo para representar los items individuales de una venta"""
    
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Venta"
    )
    
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='ventas',
        verbose_name="Producto"
    )
    
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio Unitario",
        help_text="Precio del producto al momento de la venta"
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Subtotal"
    )
    
    fecha_agregado = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha Agregado"
    )

    class Meta:
        verbose_name = "Item de Venta"
        verbose_name_plural = "Items de Venta"
        unique_together = ['venta', 'producto']
        
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad} - ${self.subtotal}"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal antes de guardar"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualizar el total de la venta
        self.venta.calcular_total()
        self.venta.save(update_fields=['subtotal', 'total'])
