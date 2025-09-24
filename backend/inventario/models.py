from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

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


class Transferencia(models.Model):
    """Modelo para registrar transferencias de productos entre depósitos"""
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    deposito_origen = models.ForeignKey(
        Deposito,
        on_delete=models.CASCADE,
        related_name='transferencias_origen',
        verbose_name="Depósito Origen"
    )
    
    deposito_destino = models.ForeignKey(
        Deposito,
        on_delete=models.CASCADE,
        related_name='transferencias_destino',
        verbose_name="Depósito Destino"
    )
    
    administrador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transferencias_creadas',
        verbose_name="Administrador"
    )
    
    fecha_transferencia = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Transferencia"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        verbose_name="Estado"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transferencia"
        verbose_name_plural = "Transferencias"
        ordering = ['-fecha_transferencia']
        
    def __str__(self):
        return f"Transferencia {self.id}: {self.deposito_origen.nombre} → {self.deposito_destino.nombre}"
    
    def clean(self):
        """Validaciones personalizadas"""
        if self.deposito_origen == self.deposito_destino:
            raise ValidationError("El depósito origen y destino no pueden ser el mismo")
        
        # Validar que ambos depósitos pertenezcan al mismo supermercado
        if self.deposito_origen.supermercado != self.deposito_destino.supermercado:
            raise ValidationError("Los depósitos deben pertenecer al mismo supermercado")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class DetalleTransferencia(models.Model):
    """Detalle de productos en cada transferencia"""
    
    transferencia = models.ForeignKey(
        Transferencia,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Transferencia"
    )
    
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.CASCADE,
        verbose_name="Producto"
    )
    
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad a Transferir"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Detalle de Transferencia"
        verbose_name_plural = "Detalles de Transferencias"
        unique_together = ['transferencia', 'producto']
        
    def __str__(self):
        return f"{self.producto.nombre} - Cantidad: {self.cantidad}"
    
    def clean(self):
        """Validar que hay stock suficiente en el depósito origen"""
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")
        
        # Importar aquí para evitar circular imports
        from productos.models import ProductoDeposito
        
        try:
            stock_origen = ProductoDeposito.objects.get(
                producto=self.producto,
                deposito=self.transferencia.deposito_origen
            )
            if stock_origen.cantidad < self.cantidad:
                raise ValidationError(
                    f"Stock insuficiente en {self.transferencia.deposito_origen.nombre}. "
                    f"Disponible: {stock_origen.cantidad}, Solicitado: {self.cantidad}"
                )
        except ProductoDeposito.DoesNotExist:
            raise ValidationError(
                f"El producto {self.producto.nombre} no existe en el depósito origen"
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class HistorialMovimiento(models.Model):
    """Registro histórico de todos los movimientos de inventario"""
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('TRANSFERENCIA', 'Transferencia entre depósitos'),
        ('INGRESO', 'Ingreso de mercadería'),
        ('EGRESO', 'Egreso de mercadería'),
        ('AJUSTE', 'Ajuste de inventario'),
        ('VENTA', 'Venta'),
    ]
    
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha del Movimiento"
    )
    
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TIPO_MOVIMIENTO_CHOICES,
        verbose_name="Tipo de Movimiento"
    )
    
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.CASCADE,
        verbose_name="Producto"
    )
    
    deposito_origen = models.ForeignKey(
        Deposito,
        on_delete=models.CASCADE,
        related_name='movimientos_origen',
        null=True,
        blank=True,
        verbose_name="Depósito Origen"
    )
    
    deposito_destino = models.ForeignKey(
        Deposito,
        on_delete=models.CASCADE,
        related_name='movimientos_destino',
        null=True,
        blank=True,
        verbose_name="Depósito Destino"
    )
    
    cantidad = models.IntegerField(
        verbose_name="Cantidad",
        help_text="Cantidad positiva para ingresos, negativa para egresos"
    )
    
    transferencia = models.ForeignKey(
        Transferencia,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='movimientos',
        verbose_name="Transferencia Relacionada"
    )
    
    detalle_transferencia = models.ForeignKey(
        DetalleTransferencia,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Detalle de Transferencia"
    )
    
    administrador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario que realizó el movimiento"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
        
    def __str__(self):
        origen = self.deposito_origen.nombre if self.deposito_origen else "N/A"
        destino = self.deposito_destino.nombre if self.deposito_destino else "N/A"
        return f"{self.get_tipo_movimiento_display()}: {self.producto.nombre} - {origen} → {destino}"
