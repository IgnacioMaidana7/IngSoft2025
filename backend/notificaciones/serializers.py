from rest_framework import serializers
from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    destinatario = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            "id",
            "titulo",
            "mensaje",
            "tipo",
            "leida",
            "creada_en",
            "destinatario",
        ]
        read_only_fields = ["id", "creada_en", "destinatario"]

    def get_destinatario(self, obj):
        if obj.empleado:
            return {
                "tipo": "empleado",
                "nombre": obj.empleado.get_nombre_completo(),
                "email": obj.empleado.email,
            }
        if obj.admin:
            return {
                "tipo": "admin",
                "nombre": obj.admin.nombre_supermercado,
                "email": obj.admin.email,
            }
        return None
