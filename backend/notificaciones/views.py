from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from .models import Notificacion
from .serializers import NotificacionSerializer
from authentication.models import EmpleadoUser


class MisNotificacionesListView(generics.ListAPIView):
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, EmpleadoUser):
            return Notificacion.objects.filter(empleado=user)
        # admin
        return Notificacion.objects.filter(admin=user)


class MarcarNotificacionLeidaView(generics.UpdateAPIView):
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "notificacion_id"

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, EmpleadoUser):
            return Notificacion.objects.filter(empleado=user)
        return Notificacion.objects.filter(admin=user)

    def update(self, request, *args, **kwargs):
        instancia = self.get_object()
        instancia.leida = True
        instancia.save(update_fields=["leida"])
        serializer = self.get_serializer(instancia)
        return Response(serializer.data, status=status.HTTP_200_OK)
