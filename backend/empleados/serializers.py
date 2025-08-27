from rest_framework import serializers
from .models import Empleado, Deposito
from django.contrib.auth import get_user_model

User = get_user_model()


class DepositoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Deposito"""
    
    class Meta:
        model = Deposito
        fields = ['id', 'nombre', 'direccion', 'descripcion', 'activo', 'fecha_creacion', 'fecha_modificacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_modificacion']
    
    def validate(self, data):
        """Validaciones personalizadas"""
        nombre = data.get('nombre')
        direccion = data.get('direccion')
        user = self.context['request'].user
        
        # Validar que no exista otro depósito con el mismo nombre y dirección
        existing_query = Deposito.objects.filter(
            nombre=nombre,
            direccion=direccion,
            supermercado=user,
            activo=True
        )
        
        # Si estamos editando, excluir el depósito actual
        if self.instance:
            existing_query = existing_query.exclude(id=self.instance.id)
        
        if existing_query.exists():
            raise serializers.ValidationError(
                "Ya existe un depósito con el mismo nombre y dirección"
            )
        
        return data
    
    def create(self, validated_data):
        # Asignar automáticamente el supermercado del usuario autenticado
        validated_data['supermercado'] = self.context['request'].user
        return super().create(validated_data)


class DepositoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar depósitos"""
    
    class Meta:
        model = Deposito
        fields = ['id', 'nombre', 'direccion', 'descripcion']


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
        read_only_fields = ['id', 'fecha_ingreso', 'fecha_modificacion']
    
    def validate_deposito(self, value):
        """Validar que el depósito pertenezca al supermercado del usuario"""
        user = self.context['request'].user
        if value.supermercado != user:
            raise serializers.ValidationError(
                "El depósito seleccionado no pertenece a tu supermercado"
            )
        return value
    
    def create(self, validated_data):
        # Asignar automáticamente el supermercado del usuario autenticado
        validated_data['supermercado'] = self.context['request'].user
        return super().create(validated_data)


class EmpleadoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar empleados"""
    
    deposito_nombre = serializers.CharField(source='deposito.nombre', read_only=True)
    nombre_completo = serializers.CharField(source='get_nombre_completo', read_only=True)
    puesto_display = serializers.CharField(source='get_puesto_display', read_only=True)
    
    class Meta:
        model = Empleado
        fields = [
            'id', 'nombre', 'apellido', 'email', 'puesto', 'puesto_display',
            'deposito', 'deposito_nombre', 'nombre_completo', 'activo'
        ]


class EmpleadoCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para crear empleados"""
    
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Empleado
        fields = [
            'nombre', 'apellido', 'email', 'dni', 'puesto', 'deposito', 'password'
        ]
    
    def validate_deposito(self, value):
        """Validar que el depósito pertenezca al supermercado del usuario"""
        user = self.context['request'].user
        if value.supermercado != user:
            raise serializers.ValidationError(
                "El depósito seleccionado no pertenece a tu supermercado"
            )
        return value
    
    def validate(self, attrs):
        """Validación adicional para verificar que la contraseña sea el DNI"""
        dni = attrs.get('dni')
        password = attrs.get('password')
        
        if password and password != dni:
            raise serializers.ValidationError({
                'password': 'La contraseña debe ser igual al DNI del empleado'
            })
        
        # Si no se proporciona password, usar el DNI
        if not password:
            attrs['password'] = dni
        
        return attrs
    
    def create(self, validated_data):
        # Remover el password del validated_data ya que no es parte del modelo Empleado
        validated_data.pop('password', None)
        # Asignar automáticamente el supermercado del usuario autenticado
        validated_data['supermercado'] = self.context['request'].user
        return super().create(validated_data)
