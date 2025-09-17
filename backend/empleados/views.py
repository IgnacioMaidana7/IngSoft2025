from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from .models import Empleado
from inventario.models import Deposito
from .serializers import (
    EmpleadoSerializer, 
    EmpleadoListSerializer, 
    EmpleadoCreateSerializer
)
from authentication.permissions import IsSupermercadoAdmin


class EmpleadoListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear empleados"""
    
    permission_classes = [IsSupermercadoAdmin]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmpleadoListSerializer
        return EmpleadoCreateSerializer
    
    def get_queryset(self):
        queryset = Empleado.objects.filter(
            supermercado=self.request.user
        ).select_related('deposito').order_by('apellido', 'nombre')
        
        # Filtros opcionales
        puesto = self.request.query_params.get('puesto', None)
        deposito_id = self.request.query_params.get('deposito', None)
        activo = self.request.query_params.get('activo', None)
        busqueda = self.request.query_params.get('search', None)
        
        if puesto:
            queryset = queryset.filter(puesto=puesto)
            
        if deposito_id:
            queryset = queryset.filter(deposito_id=deposito_id)
            
        if activo is not None:
            activo_bool = activo.lower() in ['true', '1']
            queryset = queryset.filter(activo=activo_bool)
            
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) |
                Q(apellido__icontains=busqueda) |
                Q(email__icontains=busqueda) |
                Q(dni__icontains=busqueda)
            )
        
        return queryset


class EmpleadoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para obtener, actualizar y eliminar un empleado específico"""
    
    serializer_class = EmpleadoSerializer
    permission_classes = [IsSupermercadoAdmin]
    
    def get_queryset(self):
        return Empleado.objects.filter(supermercado=self.request.user)


@api_view(['GET'])
@permission_classes([IsSupermercadoAdmin])
def obtener_empleados_por_deposito(request, deposito_id):
    """Obtiene todos los empleados de un depósito específico"""
    try:
        # Verificar que el depósito pertenezca al usuario
        deposito = Deposito.objects.get(
            id=deposito_id, 
            supermercado=request.user
        )
        
        empleados = Empleado.objects.filter(
            deposito=deposito,
            supermercado=request.user,
            activo=True
        ).order_by('apellido', 'nombre')
        
        serializer = EmpleadoListSerializer(empleados, many=True)
        
        return Response({
            'success': True,
            'deposito': {
                'id': deposito.id,
                'nombre': deposito.nombre,
                'direccion': deposito.direccion
            },
            'empleados': serializer.data
        })
        
    except Deposito.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Depósito no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsSupermercadoAdmin])
def estadisticas_empleados(request):
    """Obtiene estadísticas generales de empleados"""
    try:
        # Contar empleados por estado
        total_empleados = Empleado.objects.filter(supermercado=request.user).count()
        empleados_activos = Empleado.objects.filter(
            supermercado=request.user, 
            activo=True
        ).count()
        empleados_inactivos = total_empleados - empleados_activos
        
        # Contar empleados por puesto
        empleados_por_puesto = Empleado.objects.filter(
            supermercado=request.user,
            activo=True
        ).values('puesto').annotate(
            total=Count('id')
        ).order_by('puesto')
        
        # Contar empleados por depósito
        empleados_por_deposito = Deposito.objects.filter(
            supermercado=request.user,
            activo=True
        ).annotate(
            total_empleados=Count('empleados', filter=Q(empleados__activo=True))
        ).values('id', 'nombre', 'total_empleados').order_by('nombre')
        
        estadisticas = {
            'total_empleados': total_empleados,
            'empleados_activos': empleados_activos,
            'empleados_inactivos': empleados_inactivos,
            'empleados_por_puesto': list(empleados_por_puesto),
            'empleados_por_deposito': list(empleados_por_deposito)
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


@api_view(['POST'])
@permission_classes([IsSupermercadoAdmin])
def cambiar_estado_empleado(request, pk):
    """Cambia el estado activo/inactivo de un empleado"""
    try:
        empleado = Empleado.objects.get(
            pk=pk, 
            supermercado=request.user
        )
        
        empleado.activo = not empleado.activo
        empleado.save()
        
        serializer = EmpleadoSerializer(empleado)
        
        return Response({
            'success': True,
            'message': f'Empleado {"activado" if empleado.activo else "desactivado"} correctamente',
            'empleado': serializer.data
        })
        
    except Empleado.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Empleado no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsSupermercadoAdmin])
def obtener_roles_disponibles(request):
    """Obtiene la lista de roles disponibles para empleados"""
    roles = [
        {'value': choice[0], 'label': choice[1]} 
        for choice in Empleado.ROLES_CHOICES
    ]
    
    return Response({
        'success': True,
        'roles': roles
    })
