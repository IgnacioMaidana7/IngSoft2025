from rest_framework import serializers
from .models import Empleado
from inventario.models import Deposito
from django.contrib.auth import get_user_model

User = get_user_model()


class EmpleadoSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Empleado"""
    
    deposito_nombre = serializers.CharField(source='deposito.nombre', read_only=True)
    nombre_completo = serializers.CharField(source='get_nombre_completo', read_only=True)
    
    class Meta:
        model = Empleado
        fields = [
            'id', 'nombre', 'apellido', 'email', 'dni', 'puesto', 
            'deposito', 'deposito_nombre', 'nombre_completo', 'activo', 
            'fecha_ingreso', 'fecha_modificacion'
        ]
        read_only_fields = ['id', 'fecha_ingreso', 'fecha_modificacion', 'nombre_completo']
        
    def validate_deposito(self, value):
        """Validar que el depósito pertenezca al mismo supermercado"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            supermercado = request.user
            if value.supermercado != supermercado:
                raise serializers.ValidationError(
                    "El depósito debe pertenecer a su supermercado"
                )
        return value
    
    def create(self, validated_data):
        """Crear un nuevo empleado"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['supermercado'] = request.user
        return super().create(validated_data)


class EmpleadoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar empleados"""
    
    deposito_nombre = serializers.CharField(source='deposito.nombre', read_only=True)
    nombre_completo = serializers.CharField(source='get_nombre_completo', read_only=True)
    
    class Meta:
        model = Empleado
        fields = [
            'id', 'nombre', 'apellido', 'email', 'dni', 'puesto', 
            'deposito', 'deposito_nombre', 'nombre_completo', 'activo',
            'fecha_ingreso', 'fecha_modificacion'
        ]


class EmpleadoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear empleados"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = Empleado
        fields = [
            'nombre', 'apellido', 'email', 'dni', 'puesto', 'deposito', 'password'
        ]
    
    def validate_deposito(self, value):
        """Validar que el depósito pertenezca al mismo supermercado"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            supermercado = request.user
            if value.supermercado != supermercado:
                raise serializers.ValidationError(
                    "El depósito debe pertenecer a su supermercado"
                )
        return value
    
    def create(self, validated_data):
        """Crear un nuevo empleado con contraseña hasheada"""
        password = validated_data.pop('password')
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['supermercado'] = request.user
        
        empleado = Empleado.objects.create(**validated_data)
        # Aquí podrías agregar lógica para crear un usuario asociado si es necesario
        return empleado
