from rest_framework import serializers
from .models import Venta, ItemVenta
from productos.models import Producto, ProductoDeposito
from authentication.models import EmpleadoUser
from decimal import Decimal


def obtener_supermercado_usuario(user):
    """Función auxiliar para obtener el supermercado según el tipo de usuario"""
    if hasattr(user, 'supermercado'):
        # Es un empleado
        return user.supermercado
    else:
        # Es un admin de supermercado
        return user


class ItemVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    tiene_descuento = serializers.SerializerMethodField()
    porcentaje_descuento = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemVenta
        fields = [
            'id', 'producto', 'producto_nombre', 'cantidad', 
            'precio_unitario', 'precio_original', 'descuento_aplicado',
            'oferta_nombre', 'tiene_descuento', 'porcentaje_descuento',
            'subtotal', 'fecha_agregado'
        ]
        read_only_fields = [
            'id', 'subtotal', 'fecha_agregado', 'producto_nombre',
            'precio_original', 'descuento_aplicado', 'oferta_nombre',
            'tiene_descuento', 'porcentaje_descuento'
        ]
    
    def get_tiene_descuento(self, obj):
        """Indica si el item tiene un descuento aplicado"""
        return obj.descuento_aplicado > 0
    
    def get_porcentaje_descuento(self, obj):
        """Calcula el porcentaje de descuento si aplica"""
        if obj.precio_original and obj.precio_original > 0:
            return round((obj.descuento_aplicado / obj.precio_original) * 100, 2)
        return 0
    
    def validate(self, data):
        """Validaciones personalizadas para el item de venta"""
        producto = data.get('producto')
        cantidad = data.get('cantidad')
        
        if producto and cantidad:
            # Verificar que hay stock suficiente
            # Buscar en el depósito del supermercado del cajero
            cajero_supermercado = obtener_supermercado_usuario(self.context['request'].user)
            
            try:
                # Buscar el stock en algún depósito del supermercado
                producto_deposito = ProductoDeposito.objects.filter(
                    producto=producto,
                    deposito__supermercado=cajero_supermercado,
                    deposito__activo=True
                ).first()
                
                if not producto_deposito:
                    raise serializers.ValidationError(
                        f"El producto {producto.nombre} no está disponible en ningún depósito."
                    )
                
                if producto_deposito.cantidad < cantidad:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para {producto.nombre}. "
                        f"Stock disponible: {producto_deposito.cantidad}, solicitado: {cantidad}"
                    )
                    
            except Exception as e:
                raise serializers.ValidationError(f"Error al verificar stock: {str(e)}")
        
        return data


class VentaSerializer(serializers.ModelSerializer):
    items = ItemVentaSerializer(many=True, read_only=True)
    cajero_nombre = serializers.SerializerMethodField()
    numero_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Venta
        fields = [
            'id', 'numero_venta', 'cajero', 'cajero_nombre', 'cliente_telefono',
            'subtotal', 'descuento', 'total', 'estado', 'fecha_creacion', 
            'fecha_completada', 'observaciones', 'ticket_pdf_generado', 
            'enviado_whatsapp', 'items', 'numero_items'
        ]
        read_only_fields = [
            'id', 'numero_venta', 'cajero', 'empleado_cajero', 'subtotal', 'total', 
            'fecha_creacion', 'fecha_completada', 'ticket_pdf_generado',
            'enviado_whatsapp', 'cajero_nombre', 'numero_items'
        ]
    
    def get_cajero_nombre(self, obj):
        """Devuelve el nombre del cajero según el tipo de usuario"""
        # Verificar si fue realizada por un empleado cajero
        if obj.empleado_cajero:
            return f"{obj.empleado_cajero.nombre} {obj.empleado_cajero.apellido}"
        
        # Si no hay empleado_cajero, es una venta realizada por el admin
        cajero = obj.cajero
        if hasattr(cajero, 'nombre_supermercado'):
            # Es un User admin del supermercado
            return f"Admin - {cajero.nombre_supermercado}"
        elif cajero.first_name and cajero.last_name:
            # User con nombre y apellido
            return f"{cajero.first_name} {cajero.last_name}"
        else:
            # Fallback al username
            return cajero.username
    
    def get_numero_items(self, obj):
        """Devuelve el número total de items en la venta"""
        return obj.items.count()
    
    def validate_cliente_telefono(self, value):
        """Validación para el teléfono del cliente"""
        if value:
            # Remover espacios y caracteres especiales
            telefono_limpio = ''.join(filter(str.isdigit, value))
            
            # Verificar que tenga al menos 8 dígitos
            if len(telefono_limpio) < 8:
                raise serializers.ValidationError(
                    "El número de teléfono debe tener al menos 8 dígitos."
                )
            
            return telefono_limpio
        return value
    
    def create(self, validated_data):
        """Crea una nueva venta"""
        user = self.context['request'].user
        
        # Verificar que el usuario puede realizar ventas
        puede_realizar_ventas = False
        
        if hasattr(user, 'puesto'):
            # Es un EmpleadoUser - verificar que sea cajero
            if user.puesto == 'CAJERO':
                puede_realizar_ventas = True
        elif hasattr(user, 'nombre_supermercado') or user.is_staff:
            # Es un User admin de supermercado o staff
            puede_realizar_ventas = True
        
        if not puede_realizar_ventas:
            raise serializers.ValidationError(
                "Solo los administradores y cajeros pueden realizar ventas."
            )
        
        # Asignar el usuario correcto como cajero
        if hasattr(user, 'puesto'):
            # Es un EmpleadoUser - asignar su supermercado como cajero y guardarlo como empleado_cajero
            validated_data['cajero'] = user.supermercado
            validated_data['empleado_cajero'] = user
        else:
            # Es un User admin - asignarlo directamente
            validated_data['cajero'] = user
        
        # Crear la venta
        venta = Venta.objects.create(**validated_data)
        
        # Generar número de venta
        venta.generar_numero_venta()
        venta.save()
        
        return venta


class CrearItemVentaSerializer(serializers.Serializer):
    """Serializer para agregar items a una venta"""
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)
    
    def validate_producto_id(self, value):
        """Validar que el producto existe y está activo"""
        try:
            producto = Producto.objects.get(id=value, activo=True)
            return value
        except Producto.DoesNotExist:
            raise serializers.ValidationError("El producto no existe o no está activo.")
    
    def validate(self, data):
        """Validaciones adicionales"""
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad')
        
        if producto_id and cantidad:
            producto = Producto.objects.get(id=producto_id)
            
            # Verificar stock disponible
            cajero_supermercado = obtener_supermercado_usuario(self.context['request'].user)
            
            try:
                producto_deposito = ProductoDeposito.objects.filter(
                    producto=producto,
                    deposito__supermercado=cajero_supermercado,
                    deposito__activo=True
                ).first()
                
                if not producto_deposito:
                    raise serializers.ValidationError(
                        f"El producto {producto.nombre} no está disponible en ningún depósito."
                    )
                
                if producto_deposito.cantidad < cantidad:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para {producto.nombre}. "
                        f"Stock disponible: {producto_deposito.cantidad}, solicitado: {cantidad}"
                    )
                    
            except Exception as e:
                raise serializers.ValidationError(f"Error al verificar stock: {str(e)}")
        
        return data


class ActualizarItemVentaSerializer(serializers.Serializer):
    """Serializer para actualizar la cantidad de un item en una venta"""
    cantidad = serializers.IntegerField(min_value=1)
    
    def validate_cantidad(self, value):
        """Validar que hay stock suficiente para la nueva cantidad"""
        if hasattr(self, 'instance') and self.instance:
            item = self.instance
            producto = item.producto
            
            # Verificar stock disponible (considerando la cantidad actual del item)
            cajero_supermercado = obtener_supermercado_usuario(self.context['request'].user)
            
            try:
                producto_deposito = ProductoDeposito.objects.filter(
                    producto=producto,
                    deposito__supermercado=cajero_supermercado,
                    deposito__activo=True
                ).first()
                
                if not producto_deposito:
                    raise serializers.ValidationError(
                        f"El producto {producto.nombre} no está disponible en ningún depósito."
                    )
                
                # Stock disponible = stock actual + cantidad ya reservada en este item
                stock_disponible = producto_deposito.cantidad + item.cantidad
                
                if stock_disponible < value:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para {producto.nombre}. "
                        f"Stock disponible: {stock_disponible}, solicitado: {value}"
                    )
                    
            except Exception as e:
                raise serializers.ValidationError(f"Error al verificar stock: {str(e)}")
        
        return value


class FinalizarVentaSerializer(serializers.Serializer):
    """Serializer para finalizar una venta"""
    cliente_telefono = serializers.CharField(required=False, allow_blank=True, max_length=20)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    enviar_whatsapp = serializers.BooleanField(default=False)
    
    def validate_cliente_telefono(self, value):
        """Validación para el teléfono del cliente"""
        if value:
            # Remover espacios y caracteres especiales
            telefono_limpio = ''.join(filter(str.isdigit, value))
            
            # Verificar que tenga al menos 8 dígitos
            if len(telefono_limpio) < 8:
                raise serializers.ValidationError(
                    "El número de teléfono debe tener al menos 8 dígitos."
                )
            
            return telefono_limpio
        return value


class HistorialVentaSerializer(serializers.ModelSerializer):
    """Serializer para el historial de ventas (solo para administradores)"""
    cajero_nombre = serializers.SerializerMethodField()
    empleado_cajero_nombre = serializers.SerializerMethodField()
    fecha_formateada = serializers.SerializerMethodField()
    total_formateado = serializers.SerializerMethodField()
    
    class Meta:
        model = Venta
        fields = [
            'id',
            'numero_venta',
            'cajero_nombre',
            'empleado_cajero_nombre',
            'cliente_telefono',
            'fecha_creacion',
            'fecha_formateada',
            'total',
            'total_formateado',
            'estado',
            'ticket_pdf_generado'
        ]
    
    def get_cajero_nombre(self, obj):
        """Obtener el nombre del cajero (admin o empleado)"""
        if obj.empleado_cajero:
            return f"{obj.empleado_cajero.first_name} {obj.empleado_cajero.last_name}".strip()
        return f"{obj.cajero.first_name} {obj.cajero.last_name}".strip() or obj.cajero.username
    
    def get_empleado_cajero_nombre(self, obj):
        """Obtener el nombre del empleado cajero si existe"""
        if obj.empleado_cajero:
            return f"{obj.empleado_cajero.first_name} {obj.empleado_cajero.last_name}".strip()
        return None
    
    def get_fecha_formateada(self, obj):
        """Formatear la fecha para mostrar"""
        if obj.fecha_creacion:
            return obj.fecha_creacion.strftime("%d/%m/%Y %H:%M")
        return None
    
    def get_total_formateado(self, obj):
        """Formatear el total como string con símbolo de moneda"""
        return f"${obj.total}"