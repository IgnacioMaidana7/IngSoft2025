from django.db import models
from django.contrib.auth.models import User
from inventario.models import Deposito

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']
        
    def __str__(self):
        return self.nombre

class ProductoDeposito(models.Model):
    """Modelo para gestionar el stock de productos en diferentes depósitos"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stocks')
    deposito = models.ForeignKey(Deposito, on_delete=models.CASCADE, related_name='productos')
    cantidad = models.PositiveIntegerField(default=0)
    cantidad_minima = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Stock de Producto"
        verbose_name_plural = "Stocks de Productos"
        unique_together = ['producto', 'deposito']
        
    def __str__(self):
        return f"{self.producto.nombre} - {self.deposito.nombre}: {self.cantidad}"
    
    def tiene_stock(self):
        return self.cantidad > 0
    
    def stock_bajo(self):
        return self.cantidad <= self.cantidad_minima
