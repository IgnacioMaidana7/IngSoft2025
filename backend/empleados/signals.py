from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Empleado
from authentication.models import EmpleadoUser

User = get_user_model()


@receiver(post_save, sender=Empleado)
def crear_usuario_empleado(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de crear un empleado.
    Crea automáticamente una cuenta de usuario para el empleado.
    """
    if created:
        try:
            # Crear el usuario empleado
            usuario_empleado = EmpleadoUser.objects.create_user(
                username=instance.email,
                email=instance.email,
                password=instance.dni,  # DNI como contraseña
                nombre=instance.nombre,
                apellido=instance.apellido,
                dni=instance.dni,
                puesto=instance.puesto,
                supermercado=instance.supermercado,
                first_name=instance.nombre,
                last_name=instance.apellido
            )
            
            print(f"Usuario empleado creado: {usuario_empleado.email}")
            
        except Exception as e:
            print(f"Error al crear usuario empleado: {e}")
            # En caso de error, podrías decidir si eliminar el empleado o manejar de otra manera
            raise


@receiver(post_save, sender=Empleado)
def actualizar_usuario_empleado(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de actualizar un empleado.
    Actualiza la información del usuario empleado correspondiente.
    """
    if not created:
        try:
            # Buscar el usuario empleado correspondiente
            usuario_empleado = EmpleadoUser.objects.filter(
                email=instance.email,
                supermercado=instance.supermercado
            ).first()
            
            if usuario_empleado:
                # Actualizar los datos del usuario empleado
                usuario_empleado.nombre = instance.nombre
                usuario_empleado.apellido = instance.apellido
                usuario_empleado.first_name = instance.nombre
                usuario_empleado.last_name = instance.apellido
                usuario_empleado.puesto = instance.puesto
                usuario_empleado.is_active = instance.activo
                
                # Si cambió el DNI, actualizar la contraseña
                if usuario_empleado.dni != instance.dni:
                    usuario_empleado.dni = instance.dni
                    usuario_empleado.set_password(instance.dni)
                
                usuario_empleado.save()
                print(f"Usuario empleado actualizado: {usuario_empleado.email}")
                
        except Exception as e:
            print(f"Error al actualizar usuario empleado: {e}")