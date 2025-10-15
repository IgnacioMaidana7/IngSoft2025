from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from authentication.permissions import IsSupermercadoAdmin
from productos.models import Producto
from .models import Oferta, ProductoOferta
from .serializers import OfertaSerializer, OfertaListSerializer, ProductoOfertaSerializer, ProductoConOfertaSerializer

class OfertaViewSet(viewsets.ModelViewSet):
    queryset = Oferta.objects.all()
    permission_classes = [IsAuthenticated, IsSupermercadoAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo_descuento', 'activo']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OfertaListSerializer
        return OfertaSerializer
    
    def get_queryset(self):
        queryset = Oferta.objects.all()
        estado = self.request.query_params.get('estado', None)
        
        if estado:
            ahora = timezone.now()
            if estado == 'activa':
                queryset = queryset.filter(
                    activo=True,
                    fecha_inicio__lte=ahora,
                    fecha_fin__gte=ahora
                )
            elif estado == 'proxima':
                queryset = queryset.filter(
                    activo=True,
                    fecha_inicio__gt=ahora
                )
            elif estado == 'expirada':
                queryset = queryset.filter(
                    Q(activo=False) | Q(fecha_fin__lt=ahora)
                )
        
        return queryset
    
    def perform_update(self, serializer):
        # Verificar si la oferta puede ser editada
        oferta = self.get_object()
        if oferta.estado == 'expirada':
            return Response(
                {'error': 'No se puede modificar una oferta que ya ha expirado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """Eliminación con validación"""
        oferta = self.get_object()
        
        # Opcional: Si quisieras evitar eliminar ofertas activas
        # if oferta.estado == 'activa':
        #     return Response(
        #         {'error': 'No se puede eliminar una oferta activa.'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        
        response = super().destroy(request, *args, **kwargs)
        return Response(
            {'message': 'Oferta eliminada correctamente.'},
            status=status.HTTP_200_OK
        )
    
    def create(self, request, *args, **kwargs):
        """Crear oferta con mensaje de confirmación"""
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({
                'message': 'Oferta creada correctamente.',
                'data': response.data
            }, status=status.HTTP_201_CREATED)
        return response
    
    def update(self, request, *args, **kwargs):
        """Actualizar oferta con mensaje de confirmación"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Verificar si puede editarse
        if instance.estado == 'expirada':
            return Response(
                {'error': 'No se puede modificar una oferta que ya ha expirado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Oferta actualizada correctamente.',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Endpoint para obtener estadísticas de ofertas"""
        total = Oferta.objects.count()
        ahora = timezone.now()
        
        activas = Oferta.objects.filter(
            activo=True,
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora
        ).count()
        
        proximas = Oferta.objects.filter(
            activo=True,
            fecha_inicio__gt=ahora
        ).count()
        
        expiradas = Oferta.objects.filter(
            Q(activo=False) | Q(fecha_fin__lt=ahora)
        ).count()
        
        return Response({
            'total': total,
            'activas': activas,
            'proximas': proximas,
            'expiradas': expiradas
        })
    
    @action(detail=True, methods=['post'])
    def activar_desactivar(self, request, pk=None):
        """Activar o desactivar una oferta"""
        oferta = self.get_object()
        oferta.activo = not oferta.activo
        oferta.save()
        
        estado_texto = "activada" if oferta.activo else "desactivada"
        return Response({
            'message': f'Oferta {estado_texto} correctamente.',
            'activo': oferta.activo
        })
    
    @action(detail=True, methods=['get'])
    def productos(self, request, pk=None):
        """Obtener productos asociados a una oferta"""
        oferta = self.get_object()
        productos_oferta = ProductoOferta.objects.filter(oferta=oferta)
        serializer = ProductoOfertaSerializer(productos_oferta, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def asignar_productos(self, request, pk=None):
        """Asignar productos a una oferta"""
        oferta = self.get_object()
        
        # Verificar que la oferta esté vigente
        if oferta.estado == 'expirada':
            return Response(
                {'error': 'No se pueden asignar productos a una oferta expirada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        productos_ids = request.data.get('productos_ids', [])
        if not productos_ids:
            return Response(
                {'error': 'Debe seleccionar al menos un producto.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        productos = Producto.objects.filter(id__in=productos_ids, activo=True)
        asignaciones_creadas = []
        errores = []
        
        for producto in productos:
            # Verificar si ya tiene esta oferta
            if ProductoOferta.objects.filter(producto=producto, oferta=oferta).exists():
                errores.append(f'El producto "{producto.nombre}" ya tiene esta oferta asignada.')
                continue
                
            # Crear la asignación
            try:
                producto_oferta = ProductoOferta.objects.create(
                    producto=producto,
                    oferta=oferta,
                    precio_original=producto.precio
                )
                asignaciones_creadas.append(producto_oferta)
            except Exception as e:
                errores.append(f'Error al asignar "{producto.nombre}": {str(e)}')
        
        # Serializar las asignaciones creadas
        serializer = ProductoOfertaSerializer(asignaciones_creadas, many=True)
        
        response_data = {
            'message': f'Se asignaron {len(asignaciones_creadas)} productos a la oferta.',
            'asignaciones': serializer.data
        }
        
        if errores:
            response_data['errores'] = errores
            
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def quitar_productos(self, request, pk=None):
        """Quitar productos de una oferta"""
        oferta = self.get_object()
        productos_ids = request.data.get('productos_ids', [])
        
        if not productos_ids:
            return Response(
                {'error': 'Debe seleccionar al menos un producto.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        eliminados = ProductoOferta.objects.filter(
            oferta=oferta, 
            producto_id__in=productos_ids
        ).delete()
        
        return Response({
            'message': f'Se quitaron {eliminados[0]} productos de la oferta.'
        })


class ProductoOfertaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar productos en ofertas"""
    queryset = ProductoOferta.objects.all()
    serializer_class = ProductoOfertaSerializer
    permission_classes = [IsAuthenticated, IsSupermercadoAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['oferta', 'producto']
    
    @action(detail=False, methods=['get'])
    def productos_con_ofertas(self, request):
        """Listar todos los productos con información de ofertas"""
        categoria_id = request.query_params.get('categoria')
        estado_oferta = request.query_params.get('estado_oferta')  # 'con_oferta', 'sin_oferta'
        
        productos = Producto.objects.filter(activo=True)
        
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)
        
        # Construir respuesta con información de ofertas
        productos_data = []
        for producto in productos:
            tiene_ofertas = producto.tiene_ofertas_activas()
            
            # Filtrar por estado de oferta si se especifica
            if estado_oferta == 'con_oferta' and not tiene_ofertas:
                continue
            elif estado_oferta == 'sin_oferta' and tiene_ofertas:
                continue
                
            producto_data = {
                'id': producto.id,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre,
                'precio': producto.precio,
                'tiene_ofertas_activas': tiene_ofertas,
                'precio_con_descuento': producto.get_precio_con_descuento(),
                'mejor_oferta': None,
                'ofertas_aplicadas': []
            }
            
            if tiene_ofertas:
                mejor_oferta = producto.get_mejor_oferta()
                if mejor_oferta:
                    producto_data['mejor_oferta'] = ProductoOfertaSerializer(mejor_oferta).data
                
                ofertas_aplicadas = ProductoOferta.objects.filter(
                    producto=producto,
                    oferta__activo=True,
                    oferta__fecha_inicio__lte=timezone.now(),
                    oferta__fecha_fin__gte=timezone.now()
                )
                producto_data['ofertas_aplicadas'] = ProductoOfertaSerializer(ofertas_aplicadas, many=True).data
            
            productos_data.append(producto_data)
        
        return Response(productos_data)
