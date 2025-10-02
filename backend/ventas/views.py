from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, models
from django.http import HttpResponse
from decimal import Decimal

from .models import Venta, ItemVenta
from .serializers import (
    VentaSerializer, 
    ItemVentaSerializer, 
    CrearItemVentaSerializer,
    ActualizarItemVentaSerializer,
    FinalizarVentaSerializer,
    HistorialVentaSerializer
)
from productos.models import Producto, ProductoDeposito
from authentication.permissions import IsCajeroOrAdmin, IsSupermercadoAdmin
from .pdf_generator import generar_ticket_pdf_response, guardar_ticket_pdf


class VentaViewSet(ModelViewSet):
    """ViewSet para gestionar las ventas"""
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticated, IsCajeroOrAdmin]
    
    def get_queryset(self):
        """Filtrar ventas por el supermercado del usuario"""
        if self.request.user.is_superuser:
            return Venta.objects.all()
        
        user = self.request.user
        
        # Si es un admin de supermercado (User normal)
        if not hasattr(user, 'supermercado'):
            # Es un User admin - mostrar sus propias ventas o las de su supermercado
            return Venta.objects.filter(cajero=user)
        
        # Para empleados, mostrar solo las ventas de su supermercado
        # Buscar ventas donde el cajero sea el admin del supermercado del empleado
        return Venta.objects.filter(cajero=user.supermercado)
    
    def create(self, request, *args, **kwargs):
        """Crear una nueva venta"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            venta = serializer.save()
            return Response(
                VentaSerializer(venta, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': f'Error al crear la venta: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def agregar_producto(self, request, pk=None):
        """Agregar un producto a la venta"""
        venta = self.get_object()
        
        # Verificar que la venta esté en estado PENDIENTE o PROCESANDO
        if venta.estado not in ['PENDIENTE', 'PROCESANDO']:
            return Response(
                {'error': 'No se pueden agregar productos a una venta completada o cancelada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CrearItemVentaSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                producto_id = serializer.validated_data['producto_id']
                cantidad = serializer.validated_data['cantidad']
                
                producto = Producto.objects.get(id=producto_id)
                
                # Verificar si el producto ya existe en la venta
                item_existente = ItemVenta.objects.filter(
                    venta=venta,
                    producto=producto
                ).first()
                
                if item_existente:
                    # Actualizar cantidad del item existente
                    nueva_cantidad = item_existente.cantidad + cantidad
                    
                    # Validar stock para la nueva cantidad total
                    update_serializer = ActualizarItemVentaSerializer(
                        instance=item_existente,
                        data={'cantidad': nueva_cantidad},
                        context={'request': request}
                    )
                    update_serializer.is_valid(raise_exception=True)
                    
                    item_existente.cantidad = nueva_cantidad
                    item_existente.save()
                    item = item_existente
                else:
                    # Crear nuevo item
                    item = ItemVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio
                    )
                
                # Cambiar estado a PROCESANDO si está PENDIENTE
                if venta.estado == 'PENDIENTE':
                    venta.estado = 'PROCESANDO'
                    venta.save()
                
                return Response(
                    {
                        'message': 'Producto agregado exitosamente',
                        'item': ItemVentaSerializer(item).data,
                        'venta': VentaSerializer(venta, context={'request': request}).data
                    },
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response(
                {'error': f'Error al agregar producto: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'])
    def actualizar_item(self, request, pk=None):
        """Actualizar la cantidad de un item en la venta"""
        venta = self.get_object()
        
        # Verificar que la venta esté en estado PENDIENTE o PROCESANDO
        if venta.estado not in ['PENDIENTE', 'PROCESANDO']:
            return Response(
                {'error': 'No se pueden modificar items de una venta completada o cancelada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'error': 'El ID del item es requerido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = ItemVenta.objects.get(id=item_id, venta=venta)
        except ItemVenta.DoesNotExist:
            return Response(
                {'error': 'Item no encontrado en esta venta.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ActualizarItemVentaSerializer(
            instance=item,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                item.cantidad = serializer.validated_data['cantidad']
                item.save()
                
                return Response(
                    {
                        'message': 'Item actualizado exitosamente',
                        'item': ItemVentaSerializer(item).data,
                        'venta': VentaSerializer(venta, context={'request': request}).data
                    },
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {'error': f'Error al actualizar item: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'])
    def eliminar_item(self, request, pk=None):
        """Eliminar un item de la venta"""
        venta = self.get_object()
        
        # Verificar que la venta esté en estado PENDIENTE o PROCESANDO
        if venta.estado not in ['PENDIENTE', 'PROCESANDO']:
            return Response(
                {'error': 'No se pueden eliminar items de una venta completada o cancelada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'error': 'El ID del item es requerido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = ItemVenta.objects.get(id=item_id, venta=venta)
        except ItemVenta.DoesNotExist:
            return Response(
                {'error': 'Item no encontrado en esta venta.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            with transaction.atomic():
                item.delete()
                
                # Recalcular total de la venta
                venta.calcular_total()
                venta.save()
                
                return Response(
                    {
                        'message': 'Item eliminado exitosamente',
                        'venta': VentaSerializer(venta, context={'request': request}).data
                    },
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {'error': f'Error al eliminar item: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """Finalizar la venta y ajustar el stock"""
        venta = self.get_object()
        
        # Verificar que la venta tenga items
        if not venta.items.exists():
            return Response(
                {'error': 'No se puede finalizar una venta sin productos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que la venta esté en estado PENDIENTE o PROCESANDO
        if venta.estado not in ['PENDIENTE', 'PROCESANDO']:
            return Response(
                {'error': 'Esta venta ya ha sido finalizada o cancelada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = FinalizarVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Actualizar datos del cliente si se proporcionaron
                if serializer.validated_data.get('cliente_telefono'):
                    venta.cliente_telefono = serializer.validated_data['cliente_telefono']
                
                if serializer.validated_data.get('observaciones'):
                    venta.observaciones = serializer.validated_data['observaciones']
                
                # Ajustar el stock de todos los productos
                from .serializers import obtener_supermercado_usuario
                cajero_supermercado = obtener_supermercado_usuario(request.user)
                
                for item in venta.items.all():
                    # Buscar el stock del producto en el depósito del supermercado
                    producto_deposito = ProductoDeposito.objects.filter(
                        producto=item.producto,
                        deposito__supermercado=cajero_supermercado,
                        deposito__activo=True
                    ).first()
                    
                    if not producto_deposito:
                        raise Exception(
                            f"No se encontró stock para el producto {item.producto.nombre}"
                        )
                    
                    # Verificar stock suficiente
                    if producto_deposito.cantidad < item.cantidad:
                        raise Exception(
                            f"Stock insuficiente para {item.producto.nombre}. "
                            f"Disponible: {producto_deposito.cantidad}, necesario: {item.cantidad}"
                        )
                    
                    # Reducir stock
                    producto_deposito.cantidad -= item.cantidad
                    producto_deposito.save()
                
                # Cambiar estado de la venta
                venta.estado = 'COMPLETADA'
                venta.fecha_completada = timezone.now()
                venta.save()
                
                # Generar PDF del ticket
                try:
                    pdf_path = guardar_ticket_pdf(venta)
                    venta.ticket_pdf_generado = True
                    venta.save(update_fields=['ticket_pdf_generado'])
                except Exception as e:
                    print(f"Error generando PDF: {e}")
                    # No fallar la venta por error en PDF
                
                # Enviar por WhatsApp si se solicita (implementar después)
                if serializer.validated_data.get('enviar_whatsapp') and venta.cliente_telefono:
                    # TODO: Implementar envío por WhatsApp
                    pass
                
                return Response(
                    {
                        'message': 'Venta finalizada exitosamente',
                        'venta': VentaSerializer(venta, context={'request': request}).data
                    },
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response(
                {'error': f'Error al finalizar venta: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancelar una venta"""
        venta = self.get_object()
        
        # Verificar que la venta no esté completada
        if venta.estado == 'COMPLETADA':
            return Response(
                {'error': 'No se puede cancelar una venta completada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            venta.estado = 'CANCELADA'
            venta.save()
            
            return Response(
                {
                    'message': 'Venta cancelada exitosamente',
                    'venta': VentaSerializer(venta, context={'request': request}).data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Error al cancelar venta: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def descargar_ticket(self, request, pk=None):
        """Descargar el ticket de la venta en PDF"""
        venta = self.get_object()
        
        # Verificar que la venta esté completada
        if venta.estado != 'COMPLETADA':
            return Response(
                {'error': 'Solo se puede descargar el ticket de ventas completadas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generar y retornar el PDF
            return generar_ticket_pdf_response(venta)
        except Exception as e:
            return Response(
                {'error': f'Error al generar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsCajeroOrAdmin])
def obtener_productos_disponibles(request):
    """Obtener lista de productos disponibles para venta"""
    try:
        # Determinar el supermercado según el tipo de usuario
        if hasattr(request.user, 'supermercado'):
            # Es un empleado
            cajero_supermercado = request.user.supermercado
        else:
            # Es un admin de supermercado
            cajero_supermercado = request.user
        
        productos_con_stock = Producto.objects.filter(
            activo=True,
            stocks__deposito__supermercado=cajero_supermercado,
            stocks__deposito__activo=True,
            stocks__cantidad__gt=0
        ).distinct().select_related('categoria').prefetch_related('stocks')
        
        productos_data = []
        for producto in productos_con_stock:
            # Calcular stock total disponible
            stock_total = sum(
                stock.cantidad for stock in producto.stocks.filter(
                    deposito__supermercado=cajero_supermercado,
                    deposito__activo=True
                )
            )
            
            productos_data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre,
                'precio': str(producto.precio),
                'descripcion': producto.descripcion,
                'stock_disponible': stock_total
            })
        
        return Response(productos_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error al obtener productos: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsCajeroOrAdmin])
def buscar_productos(request):
    """Buscar productos por nombre o código"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return Response(
            {'error': 'La búsqueda debe tener al menos 2 caracteres.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Determinar el supermercado según el tipo de usuario
        if hasattr(request.user, 'supermercado'):
            # Es un empleado
            cajero_supermercado = request.user.supermercado
        else:
            # Es un admin de supermercado
            cajero_supermercado = request.user
        
        # Buscar productos que coincidan con la consulta
        productos = Producto.objects.filter(
            activo=True,
            nombre__icontains=query,
            stocks__deposito__supermercado=cajero_supermercado,
            stocks__deposito__activo=True,
            stocks__cantidad__gt=0
        ).distinct().select_related('categoria')[:20]  # Limitar a 20 resultados
        
        productos_data = []
        for producto in productos:
            # Calcular stock total disponible
            stock_total = sum(
                stock.cantidad for stock in producto.stocks.filter(
                    deposito__supermercado=cajero_supermercado,
                    deposito__activo=True
                )
            )
            
            productos_data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre,
                'precio': str(producto.precio),
                'stock_disponible': stock_total
            })
        
        return Response(productos_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error en la búsqueda: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsSupermercadoAdmin])
def historial_ventas(request):
    """
    Vista para obtener el historial completo de ventas.
    Solo accesible para administradores de supermercado.
    """
    try:
        # Obtener todas las ventas del supermercado del administrador
        ventas = Venta.objects.filter(cajero=request.user).order_by('-fecha_creacion')
        
        # Filtros opcionales
        estado = request.GET.get('estado')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        cajero_nombre = request.GET.get('cajero')
        
        # Aplicar filtros
        if estado and estado in [choice[0] for choice in Venta.ESTADO_CHOICES]:
            ventas = ventas.filter(estado=estado)
        
        if fecha_desde:
            try:
                from datetime import datetime
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                ventas = ventas.filter(fecha_creacion__date__gte=fecha_desde_obj)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if fecha_hasta:
            try:
                from datetime import datetime
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                ventas = ventas.filter(fecha_creacion__date__lte=fecha_hasta_obj)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if cajero_nombre:
            # Buscar por nombre de empleado cajero o usuario cajero
            ventas = ventas.filter(
                models.Q(empleado_cajero__first_name__icontains=cajero_nombre) |
                models.Q(empleado_cajero__last_name__icontains=cajero_nombre) |
                models.Q(cajero__first_name__icontains=cajero_nombre) |
                models.Q(cajero__last_name__icontains=cajero_nombre) |
                models.Q(cajero__username__icontains=cajero_nombre)
            )
        
        # Paginación
        from django.core.paginator import Paginator
        page_size = int(request.GET.get('page_size', 20))  # 20 ventas por página por defecto
        page_number = int(request.GET.get('page', 1))
        
        paginator = Paginator(ventas, page_size)
        page_obj = paginator.get_page(page_number)
        
        serializer = HistorialVentaSerializer(page_obj, many=True)
        
        return Response({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page_number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'results': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error al obtener historial de ventas: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsSupermercadoAdmin])
def descargar_ticket_pdf(request, venta_id):
    """
    Vista para descargar el ticket PDF de una venta específica.
    Solo accesible para administradores de supermercado.
    """
    try:
        # Verificar que la venta pertenezca al supermercado del administrador
        venta = get_object_or_404(Venta, id=venta_id, cajero=request.user)
        
        # Verificar que la venta esté completada
        if venta.estado != 'COMPLETADA':
            return Response(
                {'error': 'Solo se pueden descargar tickets de ventas completadas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar y devolver el PDF
        response = generar_ticket_pdf_response(venta)
        return response
        
    except Venta.DoesNotExist:
        return Response(
            {'error': 'Venta no encontrada o no tiene permisos para acceder a ella.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error al generar el PDF: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
