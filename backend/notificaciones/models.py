from django.db import models
from django.conf import settings
from django.utils import timezone
from authentication.models import EmpleadoUser


class Notificacion(models.Model):
    """Notificación simple para administradores o empleados."""

    TIPO_CHOICES = [
        ("STOCK_MINIMO", "Stock mínimo alcanzado"),
        ("INFO", "Información"),
        ("ALERTA", "Alerta"),
    ]

    # Destinatarios: puede ser un admin (User) o un empleado (EmpleadoUser)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notificaciones",
    )
    empleado = models.ForeignKey(
        EmpleadoUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notificaciones",
    )

    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default="INFO")
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-creada_en"]

    def __str__(self) -> str:
        target = self.empleado.get_nombre_completo() if self.empleado else (self.admin.nombre_supermercado if self.admin else "-")
        return f"[{self.tipo}] {self.titulo} -> {target}"
