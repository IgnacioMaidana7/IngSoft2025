from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Empleado, Deposito
from .serializers import (
    EmpleadoSerializer, 
    EmpleadoListSerializer, 
    EmpleadoCreateSerializer,
    DepositoSerializer,
    DepositoListSerializer
)


class DepositoListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear depósitos"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DepositoListSerializer
        return DepositoSerializer
    
    def get_queryset(self):
        return Deposito.objects.filter(
            supermercado=self.request.user,
            activo=True
        ).order_by('nombre')


class DepositoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para obtener, actualizar y eliminar un depósito específico"""
    
    serializer_class = DepositoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Deposito.objects.filter(supermercado=self.request.user)
    
    def perform_destroy(self, instance):
        # Verificar si el depósito tiene empleados asociados
        empleados_count = Empleado.objects.filter(deposito=instance, activo=True).count()
        if empleados_count > 0:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f"No se puede eliminar el depósito porque tiene {empleados_count} empleado(s) asociado(s). "
                "Reasigne o elimine los empleados primero."
            )
        
        # TODO: Verificar si el depósito tiene stock asociado
        # Esta validación se implementará cuando se desarrolle el módulo de inventario
        
        # Soft delete: marcar como inactivo en lugar de eliminar
        instance.activo = False
        instance.save()


class EmpleadoListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear empleados"""
    
    permission_classes = [IsAuthenticated]
    # filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['puesto', 'deposito', 'activo']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EmpleadoCreateSerializer
        return EmpleadoListSerializer
    
    def get_queryset(self):
        queryset = Empleado.objects.filter(
            supermercado=self.request.user,
            activo=True
        ).select_related('deposito').order_by('apellido', 'nombre')
        
        # Filtros adicionales por query params
        puesto = self.request.query_params.get('puesto', None)
        deposito = self.request.query_params.get('deposito', None)
        search = self.request.query_params.get('search', None)
        
        if puesto:
            queryset = queryset.filter(puesto=puesto)
        
        if deposito:
            queryset = queryset.filter(deposito_id=deposito)
        
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(apellido__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset


class EmpleadoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para obtener, actualizar y eliminar un empleado específico"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EmpleadoSerializer
        return EmpleadoSerializer
    
    def get_queryset(self):
        return Empleado.objects.filter(supermercado=self.request.user)
    
    def perform_destroy(self, instance):
        # Soft delete: marcar como inactivo en lugar de eliminar
        instance.activo = False
        instance.save()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_roles_disponibles(request):
    """Endpoint para obtener los roles disponibles para empleados"""
    roles = [
        {'value': role[0], 'label': role[1]} 
        for role in Empleado.ROLES_CHOICES
    ]
    return Response({'roles': roles})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_depositos_disponibles(request):
    """Endpoint para obtener los depósitos disponibles del supermercado"""
    depositos = Deposito.objects.filter(
        supermercado=request.user,
        activo=True
    ).values('id', 'nombre', 'direccion')
    
    return Response({'depositos': list(depositos)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_depositos(request):
    """Endpoint para obtener estadísticas de depósitos"""
    total_depositos = Deposito.objects.filter(
        supermercado=request.user,
        activo=True
    ).count()
    
    depositos_con_empleados = {}
    depositos = Deposito.objects.filter(
        supermercado=request.user,
        activo=True
    )
    
    for deposito in depositos:
        empleados_count = Empleado.objects.filter(
            deposito=deposito,
            activo=True
        ).count()
        depositos_con_empleados[deposito.nombre] = {
            'id': deposito.id,
            'empleados': empleados_count,
            'direccion': deposito.direccion,
            'descripcion': deposito.descripcion or "Sin descripción"
        }
    
    return Response({
        'total_depositos': total_depositos,
        'depositos_detalle': depositos_con_empleados
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_empleados(request):
    """Endpoint para obtener estadísticas de empleados"""
    total_empleados = Empleado.objects.filter(
        supermercado=request.user,
        activo=True
    ).count()
    
    empleados_por_puesto = {}
    for role in Empleado.ROLES_CHOICES:
        count = Empleado.objects.filter(
            supermercado=request.user,
            activo=True,
            puesto=role[0]
        ).count()
        empleados_por_puesto[role[1]] = count
    
    empleados_por_deposito = {}
    depositos = Deposito.objects.filter(
        supermercado=request.user,
        activo=True
    )
    
    for deposito in depositos:
        count = Empleado.objects.filter(
            deposito=deposito,
            activo=True
        ).count()
        empleados_por_deposito[deposito.nombre] = count
    
    return Response({
        'total_empleados': total_empleados,
        'empleados_por_puesto': empleados_por_puesto,
        'empleados_por_deposito': empleados_por_deposito
    })
