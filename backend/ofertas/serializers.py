from rest_framework import serializers
from .models import Oferta, ProductoOferta
from django.utils import timezone

class OfertaSerializer(serializers.ModelSerializer):
    estado = serializers.ReadOnlyField()
    puede_editar = serializers.ReadOnlyField()
    
    class Meta:
        model = Oferta
        fields = [
            'id', 'nombre', 'descripcion', 'tipo_descuento', 'valor_descuento',
            'fecha_inicio', 'fecha_fin', 'activo', 'fecha_creacion', 
            'fecha_modificacion', 'estado', 'puede_editar'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def validate(self, data):
        """Validaciones adicionales"""
        # Validar fechas
        if data.get('fecha_fin') and data.get('fecha_inicio'):
            if data['fecha_fin'] <= data['fecha_inicio']:
                raise serializers.ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
        
        # Validar que no se pueda editar una oferta expirada (solo en update)
        if self.instance and hasattr(self.instance, 'estado'):
            if self.instance.estado == 'expirada':
                raise serializers.ValidationError(
                    'No se puede modificar una oferta que ya ha expirado.'
                )
        
        # Validar valor del descuento
        tipo_descuento = data.get('tipo_descuento', self.instance.tipo_descuento if self.instance else None)
        valor_descuento = data.get('valor_descuento', self.instance.valor_descuento if self.instance else None)
        
        if tipo_descuento == 'porcentaje' and valor_descuento:
            if valor_descuento > 100:
                raise serializers.ValidationError({
                    'valor_descuento': 'El descuento porcentual no puede ser mayor a 100%.'
                })
            if valor_descuento <= 0:
                raise serializers.ValidationError({
                    'valor_descuento': 'El descuento debe ser mayor a 0.'
                })
        
        elif tipo_descuento == 'monto_fijo' and valor_descuento:
            if valor_descuento <= 0:
                raise serializers.ValidationError({
                    'valor_descuento': 'El monto fijo debe ser mayor a 0.'
                })
        
        return data

class OfertaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    estado = serializers.ReadOnlyField()
    puede_editar = serializers.ReadOnlyField()
    tipo_descuento_display = serializers.CharField(source='get_tipo_descuento_display', read_only=True)
    
    class Meta:
        model = Oferta
        fields = [
            'id', 'nombre', 'tipo_descuento', 'tipo_descuento_display', 
            'valor_descuento', 'fecha_inicio', 'fecha_fin', 'estado', 'puede_editar', 'activo'
        ]


class ProductoOfertaSerializer(serializers.ModelSerializer):
    """Serializer para ProductoOferta"""
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_categoria = serializers.CharField(source='producto.categoria.nombre', read_only=True)
    oferta_nombre = serializers.CharField(source='oferta.nombre', read_only=True)
    descuento_aplicado = serializers.ReadOnlyField()
    porcentaje_descuento = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductoOferta
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_categoria',
            'oferta', 'oferta_nombre', 'precio_original', 'precio_con_descuento',
            'descuento_aplicado', 'porcentaje_descuento', 'fecha_asignacion'
        ]
        read_only_fields = ['fecha_asignacion', 'descuento_aplicado', 'porcentaje_descuento']


class ProductoConOfertaSerializer(serializers.Serializer):
    """Serializer para productos con información de ofertas"""
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    categoria = serializers.CharField(source='categoria.nombre')
    precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    tiene_ofertas_activas = serializers.BooleanField()
    precio_con_descuento = serializers.DecimalField(max_digits=10, decimal_places=2)
    mejor_oferta = ProductoOfertaSerializer(read_only=True, allow_null=True)
    ofertas_aplicadas = ProductoOfertaSerializer(many=True, read_only=True)