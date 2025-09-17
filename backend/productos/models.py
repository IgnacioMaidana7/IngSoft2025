from django.db import models
from django.contrib.auth.models import User
from inventario.models import Deposito
from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication.models import EmpleadoUser
from notificaciones.models import Notificacion

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


@receiver(post_save, sender=ProductoDeposito)
def notificar_stock_minimo(sender, instance: ProductoDeposito, created, **kwargs):
    """Crea notificaciones cuando el stock del depósito alcanza o baja del mínimo."""
    try:
        if instance.cantidad <= instance.cantidad_minima:
            # Notificar al admin dueño del depósito
            admin = instance.deposito.supermercado
            titulo = f"Stock mínimo alcanzado: {instance.producto.nombre}"
            mensaje = (
                f"El producto '{instance.producto.nombre}' en el depósito '{instance.deposito.nombre}' "
                f"ha alcanzado el stock mínimo. Actual: {instance.cantidad}, Mínimo: {instance.cantidad_minima}."
            )
            
            # Crear notificación para el admin
            Notificacion.objects.create(
                admin=admin,
                titulo=titulo,
                mensaje=mensaje,
                tipo="STOCK_MINIMO",
            )
            print(f"Notificación creada para admin: {admin.username}")

            # Notificar a todos los reponedores asignados a ese depósito
            try:
                from empleados.models import Empleado
                # Obtener empleados reponedores del depósito específico
                empleados_dep = Empleado.objects.filter(
                    deposito=instance.deposito, 
                    puesto='REPONEDOR', 
                    activo=True
                )
                
                for empleado in empleados_dep:
                    try:
                        # Buscar el EmpleadoUser correspondiente por email y supermercado
                        empleado_user = EmpleadoUser.objects.get(
                            email=empleado.email,
                            supermercado=admin,
                            is_active=True
                        )
                        Notificacion.objects.create(
                            empleado=empleado_user,
                            titulo=titulo,
                            mensaje=mensaje,
                            tipo="STOCK_MINIMO",
                        )
                        print(f"Notificación creada para empleado: {empleado_user.email}")
                    except EmpleadoUser.DoesNotExist:
                        print(f"EmpleadoUser no encontrado para email: {empleado.email}")
                        continue
                        
            except Exception as e:
                print(f"Error notificando a reponedores: {e}")
                # Si falla la lógica específica de depósito, notificar a todos los reponedores del supermercado
                reponedores = EmpleadoUser.objects.filter(
                    supermercado=admin,
                    puesto='REPONEDOR',
                    is_active=True,
                )
                for rep in reponedores:
                    Notificacion.objects.create(
                        empleado=rep,
                        titulo=titulo,
                        mensaje=mensaje,
                        tipo="STOCK_MINIMO",
                    )
                    print(f"Notificación creada para reponedor (fallback): {rep.email}")
                    
    except Exception as e:
        print(f"Error en notificar_stock_minimo: {e}")
        # Evitar que una notificación falle la transacción principal
        pass
