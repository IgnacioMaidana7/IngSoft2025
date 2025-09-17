from django.urls import path
from . import views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from authentication.permissions import IsReponedorOrAdmin
from authentication.models import EmpleadoUser
from empleados.models import Empleado

urlpatterns = [
    # URLs para depósitos
    path('depositos/', views.DepositoListCreateView.as_view(), name='deposito-list-create'),
    path('depositos/<int:pk>/', views.DepositoDetailView.as_view(), name='deposito-detail'),
    path('depositos/disponibles/', views.obtener_depositos_disponibles, name='depositos-disponibles'),
    path('depositos/estadisticas/', views.estadisticas_depositos, name='estadisticas-depositos'),
]


@api_view(['GET'])
@permission_classes([IsReponedorOrAdmin])
def mi_deposito(request):
    user = request.user
    if isinstance(user, EmpleadoUser):
        emp = Empleado.objects.filter(email=user.email, supermercado=user.supermercado).first()
        if emp:
            dep = emp.deposito
            return Response({
                'id': dep.id,
                'nombre': dep.nombre,
                'direccion': dep.direccion,
                'activo': dep.activo
            })
    return Response({'detail': 'Sin depósito asignado'}, status=404)


urlpatterns += [
    path('mi-deposito/', mi_deposito, name='mi-deposito'),
]
