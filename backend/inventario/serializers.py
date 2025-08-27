from rest_framework import serializers
from .models import Deposito


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
        fields = ['id', 'nombre', 'direccion', 'descripcion', 'activo', 'fecha_creacion']
