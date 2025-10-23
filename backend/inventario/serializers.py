from rest_framework import serializers
from .models import Deposito, Transferencia, DetalleTransferencia, HistorialMovimiento
from productos.models import Producto, ProductoDeposito
from productos.serializers import ProductoSerializer
from authentication.models import EmpleadoUser


class DepositoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Deposito"""
    
    class Meta:
        model = Deposito
        fields = ['id', 'nombre', 'direccion', 'descripcion', 'activo', 'fecha_creacion', 'fecha_modificacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_modificacion']
    
    def validate(self, data):
        """Validaciones personalizadas"""
        # Obtener el supermercado del contexto (usuario autenticado)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            supermercado = request.user
            
            # Verificar si ya existe un depósito con el mismo nombre y dirección
            existing_query = Deposito.objects.filter(
                nombre__iexact=data.get('nombre', ''),
                direccion__iexact=data.get('direccion', ''),
                supermercado=supermercado
            )
            
            # Si estamos editando, excluir el objeto actual
            if self.instance:
                existing_query = existing_query.exclude(pk=self.instance.pk)
            
            if existing_query.exists():
                raise serializers.ValidationError({
                    'nombre': 'Ya existe un depósito con este nombre y dirección.'
                })
        
        return data
    
    def create(self, validated_data):
        """Crear un nuevo depósito"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['supermercado'] = request.user
        return super().create(validated_data)


class DepositoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de depósitos"""
    
    class Meta:
        model = Deposito
        fields = ['id', 'nombre', 'direccion', 'descripcion', 'activo', 'fecha_creacion', 'fecha_modificacion']


class DetalleTransferenciaSerializer(serializers.ModelSerializer):
    """Serializer para los detalles de transferencia"""
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_categoria = serializers.CharField(source='producto.categoria.nombre', read_only=True)
    
    class Meta:
        model = DetalleTransferencia
        fields = ['id', 'producto', 'producto_nombre', 'producto_categoria', 'cantidad']
        
    def validate(self, data):
        """Validaciones personalizadas para el detalle"""
        producto = data.get('producto')
        cantidad = data.get('cantidad')
        
        if cantidad <= 0:
            raise serializers.ValidationError({'cantidad': 'La cantidad debe ser mayor a 0'})
        
        # Validar stock disponible si tenemos acceso a la transferencia
        transferencia = self.context.get('transferencia')
        if transferencia and transferencia.deposito_origen:
            try:
                stock_origen = ProductoDeposito.objects.get(
                    producto=producto,
                    deposito=transferencia.deposito_origen
                )
                if stock_origen.cantidad < cantidad:
                    raise serializers.ValidationError({
                        'cantidad': f'Stock insuficiente. Disponible: {stock_origen.cantidad}'
                    })
            except ProductoDeposito.DoesNotExist:
                raise serializers.ValidationError({
                    'producto': 'El producto no existe en el depósito origen'
                })
        
        return data


class TransferenciaSerializer(serializers.ModelSerializer):
    """Serializer completo para transferencias"""
    detalles = DetalleTransferenciaSerializer(many=True)
    deposito_origen_nombre = serializers.CharField(source='deposito_origen.nombre', read_only=True)
    deposito_destino_nombre = serializers.CharField(source='deposito_destino.nombre', read_only=True)
    administrador_nombre = serializers.CharField(source='administrador.nombre_supermercado', read_only=True)
    
    class Meta:
        model = Transferencia
        fields = [
            'id', 'deposito_origen', 'deposito_origen_nombre', 
            'deposito_destino', 'deposito_destino_nombre',
            'administrador', 'administrador_nombre',
            'fecha_transferencia', 'estado', 'observaciones',
            'detalles', 'fecha_creacion', 'fecha_modificacion'
        ]
        read_only_fields = ['id', 'administrador', 'fecha_creacion', 'fecha_modificacion']
    
    def validate(self, data):
        """Validaciones de la transferencia"""
        deposito_origen = data.get('deposito_origen')
        deposito_destino = data.get('deposito_destino')
        
        if deposito_origen == deposito_destino:
            raise serializers.ValidationError({
                'deposito_destino': 'El depósito origen y destino no pueden ser el mismo'
            })
        
        # Validar que ambos depósitos pertenezcan al usuario autenticado
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            
            # Determinar el supermercado según el tipo de usuario
            if isinstance(user, EmpleadoUser):
                # Es un empleado, usar user.supermercado
                supermercado = user.supermercado
            else:
                # Es un administrador, el user ES el supermercado
                supermercado = user
            
            if deposito_origen.supermercado != supermercado or deposito_destino.supermercado != supermercado:
                raise serializers.ValidationError(
                    'Los depósitos deben pertenecer a su supermercado'
                )
        
        return data
    
    def create(self, validated_data):
        """Crear transferencia con detalles"""
        detalles_data = validated_data.pop('detalles')
        request = self.context.get('request')
        
        # Asignar el administrador (supermercado)
        if request and hasattr(request, 'user'):
            user = request.user
            # Si es un empleado, usar su supermercado. Si es admin, usar el user directamente
            if isinstance(user, EmpleadoUser):
                validated_data['administrador'] = user.supermercado
            else:
                validated_data['administrador'] = user
        
        transferencia = Transferencia.objects.create(**validated_data)
        
        # Crear los detalles
        for detalle_data in detalles_data:
            detalle_data['transferencia'] = transferencia
            DetalleTransferencia.objects.create(**detalle_data)
        
        return transferencia
    
    def update(self, instance, validated_data):
        """Actualizar transferencia y sus detalles"""
        detalles_data = validated_data.pop('detalles', None)
        
        # Actualizar la transferencia
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar detalles si se proporcionan
        if detalles_data is not None:
            # Eliminar detalles existentes
            instance.detalles.all().delete()
            
            # Crear nuevos detalles
            for detalle_data in detalles_data:
                detalle_data['transferencia'] = instance
                DetalleTransferencia.objects.create(**detalle_data)
        
        return instance


class TransferenciaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de transferencias"""
    deposito_origen_nombre = serializers.CharField(source='deposito_origen.nombre', read_only=True)
    deposito_destino_nombre = serializers.CharField(source='deposito_destino.nombre', read_only=True)
    total_productos = serializers.SerializerMethodField()
    
    class Meta:
        model = Transferencia
        fields = [
            'id', 'deposito_origen_nombre', 'deposito_destino_nombre',
            'fecha_transferencia', 'estado', 'total_productos'
        ]
    
    def get_total_productos(self, obj):
        """Obtener el total de productos en la transferencia"""
        return obj.detalles.count()


class HistorialMovimientoSerializer(serializers.ModelSerializer):
    """Serializer para el historial de movimientos"""
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_categoria = serializers.CharField(source='producto.categoria.nombre', read_only=True)
    deposito_origen_nombre = serializers.CharField(source='deposito_origen.nombre', read_only=True)
    deposito_destino_nombre = serializers.CharField(source='deposito_destino.nombre', read_only=True)
    administrador_nombre = serializers.CharField(source='administrador.nombre_supermercado', read_only=True)
    tipo_movimiento_display = serializers.CharField(source='get_tipo_movimiento_display', read_only=True)
    
    class Meta:
        model = HistorialMovimiento
        fields = [
            'id', 'fecha', 'tipo_movimiento', 'tipo_movimiento_display',
            'producto', 'producto_nombre', 'producto_categoria',
            'deposito_origen', 'deposito_origen_nombre',
            'deposito_destino', 'deposito_destino_nombre',
            'cantidad', 'transferencia', 'detalle_transferencia',
            'administrador_nombre', 'observaciones', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']


class ConfirmarTransferenciaSerializer(serializers.Serializer):
    """Serializer para confirmar una transferencia"""
    observaciones = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validar que la transferencia puede ser confirmada"""
        transferencia = self.context.get('transferencia')
        if not transferencia:
            raise serializers.ValidationError('Transferencia no encontrada')
        
        if transferencia.estado != 'PENDIENTE':
            raise serializers.ValidationError(
                f'No se puede confirmar una transferencia en estado {transferencia.estado}'
            )
        
        # Validar stock disponible para todos los productos
        for detalle in transferencia.detalles.all():
            try:
                stock_origen = ProductoDeposito.objects.get(
                    producto=detalle.producto,
                    deposito=transferencia.deposito_origen
                )
                if stock_origen.cantidad < detalle.cantidad:
                    raise serializers.ValidationError(
                        f'Stock insuficiente para {detalle.producto.nombre}. '
                        f'Disponible: {stock_origen.cantidad}, Requerido: {detalle.cantidad}'
                    )
            except ProductoDeposito.DoesNotExist:
                raise serializers.ValidationError(
                    f'El producto {detalle.producto.nombre} no existe en el depósito origen'
                )
        
        return data
