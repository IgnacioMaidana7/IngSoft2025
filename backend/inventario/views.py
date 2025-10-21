from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from .models import Deposito, Transferencia, DetalleTransferencia, HistorialMovimiento
from .serializers import (
    DepositoSerializer,
    DepositoListSerializer,
    TransferenciaSerializer,
    TransferenciaListSerializer,
    HistorialMovimientoSerializer,
    ConfirmarTransferenciaSerializer
)
from authentication.permissions import IsReponedorOrAdmin
from productos.models import ProductoDeposito
from notificaciones.models import Notificacion
from authentication.models import EmpleadoUser
from empleados.models import Empleado


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


class TransferenciaListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar y crear transferencias.
    GET: Lista todas las transferencias del supermercado
    POST: Crea una nueva transferencia
    """
    permission_classes = [IsAuthenticated]  # Solo admins pueden crear transferencias
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TransferenciaListSerializer
        return TransferenciaSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Si es un empleado (reponedor)
        if isinstance(user, EmpleadoUser):
            # Obtener el depósito asignado al empleado
            try:
                empleado = Empleado.objects.get(
                    email=user.email,
                    supermercado=user.supermercado
                )
                if empleado.deposito:
                    # Mostrar transferencias donde su depósito está involucrado (origen o destino)
                    return Transferencia.objects.filter(
                        Q(deposito_origen=empleado.deposito) | Q(deposito_destino=empleado.deposito)
                    ).select_related(
                        'deposito_origen', 'deposito_destino', 'administrador'
                    ).prefetch_related('detalles').order_by('-fecha_transferencia')
            except Empleado.DoesNotExist:
                pass
            
            # Si no tiene depósito asignado, no mostrar nada
            return Transferencia.objects.none()
        
        # Si es un admin, puede ver todas sus transferencias
        return Transferencia.objects.filter(
            administrador=user
        ).select_related(
            'deposito_origen', 'deposito_destino', 'administrador'
        ).prefetch_related('detalles').order_by('-fecha_transferencia')


class TransferenciaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para obtener, actualizar y eliminar una transferencia específica.
    """
    serializer_class = TransferenciaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Si es un empleado (reponedor)
        if isinstance(user, EmpleadoUser):
            # Obtener el depósito asignado al empleado
            try:
                empleado = Empleado.objects.get(
                    email=user.email,
                    supermercado=user.supermercado
                )
                if empleado.deposito:
                    # Puede acceder a transferencias donde su depósito está involucrado
                    return Transferencia.objects.filter(
                        Q(deposito_origen=empleado.deposito) | Q(deposito_destino=empleado.deposito)
                    ).select_related(
                        'deposito_origen', 'deposito_destino', 'administrador'
                    ).prefetch_related('detalles')
            except Empleado.DoesNotExist:
                pass
            
            # Si no tiene depósito asignado, no puede acceder
            return Transferencia.objects.none()
        
        # Si es un admin, puede acceder a todas sus transferencias
        return Transferencia.objects.filter(
            administrador=user
        ).select_related(
            'deposito_origen', 'deposito_destino', 'administrador'
        ).prefetch_related('detalles')
    
    def destroy(self, request, *args, **kwargs):
        """
        Eliminar transferencia. Solo se permiten eliminar transferencias PENDIENTES.
        Los reponedores solo pueden eliminar transferencias donde su depósito es el origen.
        """
        transferencia = self.get_object()
        user = request.user
        
        # Verificar que la transferencia esté PENDIENTE
        if transferencia.estado != 'PENDIENTE':
            return Response({
                'success': False,
                'error': 'Solo se pueden eliminar transferencias en estado PENDIENTE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Si es un empleado (reponedor), solo puede eliminar si es del depósito origen
        if isinstance(user, EmpleadoUser):
            try:
                empleado = Empleado.objects.get(
                    email=user.email,
                    supermercado=user.supermercado
                )
                if transferencia.deposito_origen != empleado.deposito:
                    return Response({
                        'success': False,
                        'error': 'Solo puedes eliminar transferencias creadas desde tu depósito'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Empleado.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Empleado no encontrado'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Eliminar la transferencia (y sus detalles por CASCADE)
        transferencia.delete()
        
        return Response({
            'success': True,
            'message': 'Transferencia eliminada exitosamente'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmar_transferencia(request, transferencia_id):
    """
    Confirma una transferencia pendiente y actualiza los stocks.
    """
    try:
        user = request.user
        
        # Si es un empleado (reponedor)
        if isinstance(user, EmpleadoUser):
            # Solo puede confirmar transferencias que llegan a su depósito
            try:
                empleado = Empleado.objects.get(
                    email=user.email,
                    supermercado=user.supermercado
                )
                if not empleado.deposito:
                    return Response({
                        'success': False,
                        'error': 'No tienes un depósito asignado'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # La transferencia debe tener como destino el depósito del empleado
                transferencia = get_object_or_404(
                    Transferencia, 
                    id=transferencia_id,
                    deposito_destino=empleado.deposito
                )
            except Empleado.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Empleado no encontrado'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            # Si es admin, puede confirmar cualquier transferencia de su supermercado
            transferencia = get_object_or_404(
                Transferencia, 
                id=transferencia_id, 
                administrador=user
            )
        
        serializer = ConfirmarTransferenciaSerializer(
            data=request.data,
            context={'transferencia': transferencia}
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Confirmar la transferencia en una transacción
        with transaction.atomic():
            # Actualizar estado
            transferencia.estado = 'CONFIRMADA'
            if serializer.validated_data.get('observaciones'):
                transferencia.observaciones = serializer.validated_data['observaciones']
            transferencia.save()
            
            # Procesar cada detalle de la transferencia
            for detalle in transferencia.detalles.all():
                # Reducir stock en origen
                stock_origen = ProductoDeposito.objects.get(
                    producto=detalle.producto,
                    deposito=transferencia.deposito_origen
                )
                stock_origen.cantidad -= detalle.cantidad
                stock_origen.save()
                
                # Aumentar stock en destino (crear si no existe)
                stock_destino, created = ProductoDeposito.objects.get_or_create(
                    producto=detalle.producto,
                    deposito=transferencia.deposito_destino,
                    defaults={'cantidad': 0, 'cantidad_minima': 0}
                )
                stock_destino.cantidad += detalle.cantidad
                stock_destino.save()
                
                # Registrar movimientos en el historial
                # Movimiento de salida del depósito origen
                HistorialMovimiento.objects.create(
                    fecha=transferencia.fecha_transferencia,
                    tipo_movimiento='TRANSFERENCIA',
                    producto=detalle.producto,
                    deposito_origen=transferencia.deposito_origen,
                    deposito_destino=transferencia.deposito_destino,
                    cantidad=-detalle.cantidad,  # Negativo para salida
                    transferencia=transferencia,
                    detalle_transferencia=detalle,
                    administrador=transferencia.administrador,
                    observaciones=f'Transferencia {transferencia.id} - Salida'
                )
                
                # Movimiento de entrada al depósito destino
                HistorialMovimiento.objects.create(
                    fecha=transferencia.fecha_transferencia,
                    tipo_movimiento='TRANSFERENCIA',
                    producto=detalle.producto,
                    deposito_origen=transferencia.deposito_origen,
                    deposito_destino=transferencia.deposito_destino,
                    cantidad=detalle.cantidad,  # Positivo para entrada
                    transferencia=transferencia,
                    detalle_transferencia=detalle,
                    administrador=transferencia.administrador,
                    observaciones=f'Transferencia {transferencia.id} - Entrada'
                )
            
            # Enviar notificaciones a reponedores
            _enviar_notificaciones_transferencia(transferencia)
        
        return Response({
            'success': True,
            'message': 'Transferencia confirmada exitosamente',
            'data': TransferenciaSerializer(transferencia).data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _enviar_notificaciones_transferencia(transferencia):
    """Función auxiliar para enviar notificaciones sobre transferencias"""
    try:
        # Notificar reponedores del depósito origen
        reponedores_origen = EmpleadoUser.objects.filter(
            supermercado=transferencia.administrador,
            puesto='REPONEDOR',
            is_active=True
        )
        
        # Filtrar por depósito específico si es posible
        empleados_origen = Empleado.objects.filter(
            deposito=transferencia.deposito_origen,
            puesto='REPONEDOR',
            activo=True
        )
        
        for empleado in empleados_origen:
            try:
                empleado_user = EmpleadoUser.objects.get(
                    email=empleado.email,
                    supermercado=transferencia.administrador,
                    is_active=True
                )
                Notificacion.objects.create(
                    empleado=empleado_user,
                    titulo=f"Transferencia de productos - Salida",
                    mensaje=f"Se ha realizado una transferencia desde {transferencia.deposito_origen.nombre} "
                           f"hacia {transferencia.deposito_destino.nombre}. Revisa los productos transferidos.",
                    tipo="INFO"
                )
            except EmpleadoUser.DoesNotExist:
                continue
        
        # Notificar reponedores del depósito destino
        empleados_destino = Empleado.objects.filter(
            deposito=transferencia.deposito_destino,
            puesto='REPONEDOR',
            activo=True
        )
        
        for empleado in empleados_destino:
            try:
                empleado_user = EmpleadoUser.objects.get(
                    email=empleado.email,
                    supermercado=transferencia.administrador,
                    is_active=True
                )
                Notificacion.objects.create(
                    empleado=empleado_user,
                    titulo=f"Transferencia de productos - Entrada",
                    mensaje=f"Se ha recibido una transferencia desde {transferencia.deposito_origen.nombre}. "
                           f"Verifica la recepción de los productos.",
                    tipo="INFO"
                )
            except EmpleadoUser.DoesNotExist:
                continue
                
    except Exception as e:
        print(f"Error enviando notificaciones de transferencia: {e}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar_transferencia(request, transferencia_id):
    """
    Cancela una transferencia CONFIRMADA y revierte los stocks.
    Solo administradores pueden cancelar transferencias confirmadas.
    """
    try:
        user = request.user
        
        # Solo administradores pueden cancelar transferencias confirmadas
        if isinstance(user, EmpleadoUser):
            return Response({
                'success': False,
                'error': 'Solo los administradores pueden cancelar transferencias confirmadas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        transferencia = get_object_or_404(
            Transferencia, 
            id=transferencia_id, 
            administrador=user
        )
        
        # Verificar que la transferencia esté CONFIRMADA
        if transferencia.estado != 'CONFIRMADA':
            return Response({
                'success': False,
                'error': 'Solo se pueden cancelar transferencias en estado CONFIRMADA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancelar la transferencia en una transacción
        with transaction.atomic():
            # Actualizar estado
            transferencia.estado = 'CANCELADA'
            if request.data.get('observaciones'):
                transferencia.observaciones = f"{transferencia.observaciones or ''}\n[CANCELADA] {request.data.get('observaciones')}"
            transferencia.save()
            
            # Revertir cada detalle de la transferencia
            for detalle in transferencia.detalles.all():
                # Devolver stock al origen
                stock_origen = ProductoDeposito.objects.get(
                    producto=detalle.producto,
                    deposito=transferencia.deposito_origen
                )
                stock_origen.cantidad += detalle.cantidad
                stock_origen.save()
                
                # Reducir stock en destino
                stock_destino = ProductoDeposito.objects.get(
                    producto=detalle.producto,
                    deposito=transferencia.deposito_destino
                )
                stock_destino.cantidad -= detalle.cantidad
                stock_destino.save()
                
                # Registrar movimientos de reversión en el historial
                # Movimiento de devolución al depósito origen
                HistorialMovimiento.objects.create(
                    fecha=timezone.now(),
                    tipo_movimiento='TRANSFERENCIA',
                    producto=detalle.producto,
                    deposito_origen=transferencia.deposito_destino,  # Invertido
                    deposito_destino=transferencia.deposito_origen,  # Invertido
                    cantidad=detalle.cantidad,  # Positivo para devolución al origen
                    transferencia=transferencia,
                    detalle_transferencia=detalle,
                    administrador=transferencia.administrador,
                    observaciones=f'Transferencia {transferencia.id} - CANCELADA - Devolución al origen'
                )
                
                # Movimiento de salida del depósito destino
                HistorialMovimiento.objects.create(
                    fecha=timezone.now(),
                    tipo_movimiento='TRANSFERENCIA',
                    producto=detalle.producto,
                    deposito_origen=transferencia.deposito_destino,  # Invertido
                    deposito_destino=transferencia.deposito_origen,  # Invertido
                    cantidad=-detalle.cantidad,  # Negativo para salida del destino
                    transferencia=transferencia,
                    detalle_transferencia=detalle,
                    administrador=transferencia.administrador,
                    observaciones=f'Transferencia {transferencia.id} - CANCELADA - Salida del destino'
                )
            
            # Enviar notificaciones sobre la cancelación
            _enviar_notificaciones_cancelacion(transferencia)
        
        return Response({
            'success': True,
            'message': 'Transferencia cancelada exitosamente. Los stocks han sido revertidos.',
            'data': TransferenciaSerializer(transferencia).data
        })
        
    except ProductoDeposito.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Error al revertir stocks: producto no encontrado en depósito'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _enviar_notificaciones_cancelacion(transferencia):
    """Función auxiliar para enviar notificaciones sobre cancelación de transferencias"""
    try:
        # Notificar reponedores del depósito origen
        empleados_origen = Empleado.objects.filter(
            deposito=transferencia.deposito_origen,
            puesto='REPONEDOR',
            activo=True
        )
        
        for empleado in empleados_origen:
            try:
                empleado_user = EmpleadoUser.objects.get(
                    email=empleado.email,
                    supermercado=transferencia.administrador,
                    is_active=True
                )
                Notificacion.objects.create(
                    empleado=empleado_user,
                    titulo=f"Transferencia CANCELADA - Productos devueltos",
                    mensaje=f"La transferencia desde {transferencia.deposito_origen.nombre} "
                           f"hacia {transferencia.deposito_destino.nombre} ha sido CANCELADA. "
                           f"Los productos han sido devueltos al depósito origen.",
                    tipo="ALERTA"
                )
            except EmpleadoUser.DoesNotExist:
                continue
        
        # Notificar reponedores del depósito destino
        empleados_destino = Empleado.objects.filter(
            deposito=transferencia.deposito_destino,
            puesto='REPONEDOR',
            activo=True
        )
        
        for empleado in empleados_destino:
            try:
                empleado_user = EmpleadoUser.objects.get(
                    email=empleado.email,
                    supermercado=transferencia.administrador,
                    is_active=True
                )
                Notificacion.objects.create(
                    empleado=empleado_user,
                    titulo=f"Transferencia CANCELADA",
                    mensaje=f"La transferencia desde {transferencia.deposito_origen.nombre} "
                           f"ha sido CANCELADA. Los productos han sido retirados del inventario.",
                    tipo="ALERTA"
                )
            except EmpleadoUser.DoesNotExist:
                continue
                
    except Exception as e:
        print(f"Error enviando notificaciones de cancelación: {e}")


class HistorialMovimientoListView(generics.ListAPIView):
    """
    Vista para listar el historial de movimientos de inventario.
    """
    serializer_class = HistorialMovimientoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Si es un empleado (reponedor), puede ver movimientos de su depósito
        if isinstance(user, EmpleadoUser):
            try:
                empleado = Empleado.objects.get(
                    email=user.email,
                    supermercado=user.supermercado
                )
                if empleado.deposito:
                    # Ver movimientos donde su depósito está involucrado
                    return HistorialMovimiento.objects.filter(
                        Q(deposito_origen=empleado.deposito) | Q(deposito_destino=empleado.deposito),
                        cantidad__gt=0  # Solo movimientos de entrada (evita duplicados)
                    ).select_related(
                        'producto', 'producto__categoria',
                        'deposito_origen', 'deposito_destino', 
                        'administrador', 'transferencia'
                    ).order_by('-fecha')
            except Empleado.DoesNotExist:
                pass
            
            # Si no tiene depósito, no puede ver historial
            return HistorialMovimiento.objects.none()
        
        # Si es admin, puede ver el historial completo de su supermercado
        queryset = HistorialMovimiento.objects.filter(
            administrador=user,
            cantidad__gt=0  # Solo movimientos de entrada (evita duplicados en transferencias)
        ).select_related(
            'producto', 'producto__categoria',
            'deposito_origen', 'deposito_destino', 
            'administrador', 'transferencia'
        ).order_by('-fecha')
        
        # Filtros opcionales
        deposito_id = self.request.query_params.get('deposito')
        if deposito_id:
            queryset = queryset.filter(
                Q(deposito_origen_id=deposito_id) | Q(deposito_destino_id=deposito_id)
            )
        
        tipo_movimiento = self.request.query_params.get('tipo')
        if tipo_movimiento:
            queryset = queryset.filter(tipo_movimiento=tipo_movimiento)
        
        producto_id = self.request.query_params.get('producto')
        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        
        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generar_remito_pdf(request, transferencia_id):
    """
    Genera un PDF con formato de remito para una transferencia.
    """
    try:
        # Verificar que es un admin
        if hasattr(request.user, 'supermercado'):
            return Response({
                'success': False,
                'error': 'No tienes permisos para generar remitos'
            }, status=status.HTTP_403_FORBIDDEN)
        
        transferencia = get_object_or_404(
            Transferencia, 
            id=transferencia_id, 
            administrador=request.user
        )
        
        # Solo se puede generar remito para transferencias confirmadas
        if transferencia.estado != 'CONFIRMADA':
            return Response({
                'success': False,
                'error': 'Solo se puede generar remito para transferencias confirmadas'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generar PDF
        pdf_content = _generar_pdf_remito(transferencia)
        
        # Convertir a base64 para evitar problemas de CORS
        import base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        return Response({
            'success': True,
            'pdf_data': pdf_base64,
            'filename': f'remito_transferencia_{transferencia.id}.pdf'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _generar_pdf_remito(transferencia):
    """Función auxiliar para generar el PDF del remito"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Contenedor para los elementos del PDF
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    # Título
    story.append(Paragraph(f"REMITO DE TRANSFERENCIA N° {transferencia.id}", title_style))
    story.append(Spacer(1, 20))
    
    # Información de la transferencia
    data_info = [
        ['Fecha:', transferencia.fecha_transferencia.strftime('%d/%m/%Y %H:%M')],
        ['Depósito Origen:', transferencia.deposito_origen.nombre],
        ['Depósito Destino:', transferencia.deposito_destino.nombre],
        ['Administrador:', transferencia.administrador.nombre_supermercado],
        ['Estado:', transferencia.get_estado_display()],
    ]
    
    if transferencia.observaciones:
        data_info.append(['Observaciones:', transferencia.observaciones])
    
    table_info = Table(data_info, colWidths=[2*inch, 4*inch])
    table_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(table_info)
    story.append(Spacer(1, 30))
    
    # Título de productos
    story.append(Paragraph("PRODUCTOS TRANSFERIDOS", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Tabla de productos
    data_productos = [['Producto', 'Categoría', 'Cantidad']]
    
    for detalle in transferencia.detalles.all():
        data_productos.append([
            detalle.producto.nombre,
            detalle.producto.categoria.nombre,
            str(detalle.cantidad)
        ])
    
    table_productos = Table(data_productos, colWidths=[3*inch, 2*inch, 1*inch])
    table_productos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table_productos)
    story.append(Spacer(1, 50))
    
    # Firmas
    story.append(Paragraph("FIRMAS", styles['Heading3']))
    story.append(Spacer(1, 30))
    
    data_firmas = [
        ['Entrega:', '_' * 30, 'Recibe:', '_' * 30],
        ['', '', '', ''],
        ['Nombre:', '', 'Nombre:', ''],
        ['Fecha:', '', 'Fecha:', ''],
    ]
    
    table_firmas = Table(data_firmas, colWidths=[1*inch, 2*inch, 1*inch, 2*inch])
    table_firmas.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(table_firmas)
    
    # Generar PDF
    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


@api_view(['GET'])
@permission_classes([IsReponedorOrAdmin])
def obtener_productos_deposito(request, deposito_id):
    """
    Obtiene todos los productos con stock disponible en un depósito específico
    """
    try:
        deposito = get_object_or_404(Deposito, id=deposito_id)
        
        # Verificar que el usuario tenga acceso al depósito
        user = request.user
        if hasattr(user, 'supermercado') and user.supermercado:
            # EmpleadoUser
            if deposito.supermercado != user.supermercado:
                return Response({'detail': 'No tiene permisos para acceder a este depósito'}, 
                              status=status.HTTP_403_FORBIDDEN)
        else:
            # User admin
            if deposito.supermercado != user:
                return Response({'detail': 'No tiene permisos para acceder a este depósito'}, 
                              status=status.HTTP_403_FORBIDDEN)
        
        # Obtener productos con stock en el depósito
        productos_stock = ProductoDeposito.objects.filter(
            deposito=deposito,
            cantidad__gt=0  # Solo productos con stock disponible
        ).select_related('producto', 'producto__categoria', 'deposito')
        
        # Serializar los datos
        data = []
        for ps in productos_stock:
            data.append({
                'id': ps.id,
                'producto': {
                    'id': ps.producto.id,
                    'nombre': ps.producto.nombre,
                    'categoria': {
                        'id': ps.producto.categoria.id,
                        'nombre': ps.producto.categoria.nombre
                    },
                    'precio': str(ps.producto.precio),
                    'descripcion': ps.producto.descripcion,
                    'activo': ps.producto.activo
                },
                'deposito': {
                    'id': ps.deposito.id,
                    'nombre': ps.deposito.nombre,
                    'direccion': ps.deposito.direccion,
                    'activo': ps.deposito.activo
                },
                'cantidad': ps.cantidad,
                'cantidad_minima': ps.cantidad_minima
            })
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
