from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Deposito
from .serializers import (
    DepositoSerializer,
    DepositoListSerializer
)
from authentication.permissions import IsReponedorOrAdmin


class DepositoListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar y crear depósitos.
    GET: Lista todos los depósitos del supermercado autenticado
    POST: Crea un nuevo depósito
    """
    permission_classes = [IsReponedorOrAdmin]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DepositoListSerializer
        return DepositoSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Si es un EmpleadoUser, obtener el supermercado desde el empleado
        if hasattr(user, 'supermercado') and user.supermercado:
            return Deposito.objects.filter(
                supermercado=user.supermercado
            ).order_by('nombre')
        
        # Si es un admin (User), usar directamente
        return Deposito.objects.filter(
            supermercado=user
        ).order_by('nombre')


class DepositoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para obtener, actualizar y eliminar un depósito específico.
    GET: Obtiene los detalles de un depósito
    PUT/PATCH: Actualiza un depósito
    DELETE: Elimina un depósito
    """
    serializer_class = DepositoSerializer
    permission_classes = [IsReponedorOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        
        # Si es un EmpleadoUser, obtener el supermercado desde el empleado
        if hasattr(user, 'supermercado') and user.supermercado:
            return Deposito.objects.filter(
                supermercado=user.supermercado
            )
        
        # Si es un admin (User), usar directamente
        return Deposito.objects.filter(supermercado=user)


@api_view(['GET'])
@permission_classes([IsReponedorOrAdmin])
def obtener_depositos_disponibles(request):
    """
    Obtiene una lista simplificada de depósitos disponibles para selección.
    """
    user = request.user
    
    # Si es un EmpleadoUser, obtener el supermercado desde el empleado
    if hasattr(user, 'supermercado') and user.supermercado:
        depositos = Deposito.objects.filter(
            supermercado=user.supermercado,
            activo=True
        ).values('id', 'nombre', 'direccion').order_by('nombre')
    else:
        # Si es un admin (User), usar directamente
        depositos = Deposito.objects.filter(
            supermercado=user,
            activo=True
        ).values('id', 'nombre', 'direccion').order_by('nombre')
    
    return Response({
        'success': True,
        'data': list(depositos)
    })


@api_view(['GET'])
@permission_classes([IsReponedorOrAdmin])
def estadisticas_depositos(request):
    """
    Obtiene estadísticas generales de los depósitos.
    """
    try:
        user = request.user
        
        # Si es un EmpleadoUser, obtener el supermercado desde el empleado
        if hasattr(user, 'supermercado') and user.supermercado:
            supermercado_filter = user.supermercado
        else:
            # Si es un admin (User), usar directamente
            supermercado_filter = user
        
        # Contar depósitos por estado
        total_depositos = Deposito.objects.filter(supermercado=supermercado_filter).count()
        depositos_activos = Deposito.objects.filter(
            supermercado=supermercado_filter, 
            activo=True
        ).count()
        depositos_inactivos = total_depositos - depositos_activos
        
        # Contar empleados por depósito (si la relación existe)
        try:
            from empleados.models import Empleado
            depositos_con_empleados = Deposito.objects.filter(
                supermercado=supermercado_filter
            ).annotate(
                total_empleados=Count('empleados', filter=Q(empleados__activo=True))
            ).values('id', 'nombre', 'total_empleados')
        except ImportError:
            depositos_con_empleados = []
        
        estadisticas = {
            'total_depositos': total_depositos,
            'depositos_activos': depositos_activos,
            'depositos_inactivos': depositos_inactivos,
            'depositos_con_empleados': list(depositos_con_empleados)
        }
        
        return Response({
            'success': True,
            'data': estadisticas
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
