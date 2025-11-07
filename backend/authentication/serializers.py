from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import authenticate
from .models import User, EmpleadoUser
import re


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm', 'nombre_supermercado', 
            'logo', 'cuil', 'provincia', 'localidad'
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'nombre_supermercado': {'required': True},
            'cuil': {'required': True},
            'provincia': {'required': True},
            'localidad': {'required': True},
        }
    
    def validate_email(self, value):
        """Validar formato de email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email")
        
        # Validación adicional de formato
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Revise si el dato Email ha sido ingresado correctamente")
        
        return value
    
    def validate_cuil(self, value):
        """Validar CUIL"""
        # Remover espacios y guiones
        cuil_clean = re.sub(r'[\s-]', '', value)
        
        # Verificar que solo contenga números
        if not cuil_clean.isdigit():
            raise serializers.ValidationError(
                "Revisa si el dato CUIL ha sido ingresado correctamente, "
                "para ingresarlo no coloque espacios ni guiones"
            )
        
        # Verificar que tenga exactamente 11 dígitos
        if len(cuil_clean) != 11:
            raise serializers.ValidationError(
                "Revisa si el dato CUIL ha sido ingresado correctamente, "
                "para ingresarlo no coloque espacios ni guiones"
            )
        
        # Verificar que no exista otro usuario con el mismo CUIL
        if User.objects.filter(cuil=cuil_clean).exists():
            raise serializers.ValidationError("Ya existe un usuario con este CUIL")
        
        return cuil_clean
    
    def validate_password(self, value):
        """Validar contraseña según los criterios especificados"""
        # Mínimo 8 caracteres
        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres"
            )
        
        # Debe contener al menos un número
        if not re.search(r'\d', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número"
            )
        
        # Debe contener al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un carácter especial"
            )
        
        # Usar validadores de Django
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate(self, attrs):
        """Validaciones a nivel de objeto"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })
        
        # Validar combinación de errores de email y CUIL
        email_error = None
        cuil_error = None
        
        try:
            self.validate_email(attrs.get('email'))
        except serializers.ValidationError:
            email_error = True
        
        try:
            self.validate_cuil(attrs.get('cuil'))
        except serializers.ValidationError:
            cuil_error = True
        
        # Si ambos tienen errores, mostrar mensaje combinado
        if email_error and cuil_error:
            raise serializers.ValidationError(
                "Revise si los datos Email y CUIL han sido bien ingresados, "
                "para ingresar correctamente el CUIL no escriba espacios ni guiones"
            )
        
        return attrs
    
    def create(self, validated_data):
        """Crear nuevo usuario"""
        # Remover campos que no van directamente al modelo
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        
        # Generar username único desde email si no se proporciona
        if 'username' not in validated_data or not validated_data.get('username'):
            base_username = validated_data['email'].split('@')[0]
            username = base_username
            counter = 1
            
            # Asegurar que el username sea único
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            validated_data['username'] = username
        
        # Crear usuario
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer para mostrar información del usuario"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'nombre_supermercado', 
            'logo', 'cuil', 'provincia', 'localidad', 
            'fecha_registro', 'is_active'
        ]
        read_only_fields = ['id', 'fecha_registro']


class EmpleadoLoginSerializer(serializers.Serializer):
    """Serializer para login de empleados usando email y DNI"""
    
    email = serializers.EmailField()
    dni = serializers.CharField(max_length=8)
    
    def validate(self, attrs):
        email = attrs.get('email')
        dni = attrs.get('dni')
        
        if email and dni:
            # Intentar autenticar usando el backend personalizado
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=dni
            )
            
            if not user:
                raise serializers.ValidationError(
                    'No es posible iniciar sesión con las credenciales proporcionadas.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'La cuenta de usuario está desactivada.'
                )
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError(
            'Debe incluir "email" y "dni".'
        )


class EmpleadoUserSerializer(serializers.ModelSerializer):
    """Serializer para mostrar información del usuario empleado"""
    
    nombre_completo = serializers.CharField(source='get_nombre_completo', read_only=True)
    supermercado_nombre = serializers.CharField(source='supermercado.nombre_supermercado', read_only=True)
    deposito_id = serializers.SerializerMethodField()
    deposito_nombre = serializers.SerializerMethodField()
    fecha_ingreso = serializers.DateTimeField(source='fecha_registro', read_only=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = EmpleadoUser
        fields = [
            'id', 'email', 'nombre', 'apellido', 'nombre_completo', 
            'dni', 'puesto', 'supermercado_nombre', 'deposito_id', 'deposito_nombre',
            'fecha_registro', 'fecha_ingreso', 'fecha_modificacion', 'is_active'
        ]
        read_only_fields = ['id', 'fecha_registro', 'fecha_ingreso', 'fecha_modificacion']
    
    def get_deposito_id(self, obj):
        """Obtiene el ID del depósito asignado al empleado"""
        return obj.deposito.id if obj.deposito else None
    
    def get_deposito_nombre(self, obj):
        """Obtiene el nombre del depósito asignado al empleado"""
        return obj.deposito.nombre if obj.deposito else None


class SupermercadoLoginSerializer(serializers.Serializer):
    """Serializer para login de administradores de supermercado"""
    
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Intentar autenticar usando el backend personalizado
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'No es posible iniciar sesión con las credenciales proporcionadas.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'La cuenta de usuario está desactivada.'
                )
            
            # Verificar que sea un administrador de supermercado (User, no EmpleadoUser)
            if isinstance(user, EmpleadoUser):
                raise serializers.ValidationError(
                    'Use el login de empleados para acceder con esta cuenta.'
                )
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError(
            'Debe incluir "email" y "password".'
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar perfil del usuario (sin cambiar contraseña)"""
    
    class Meta:
        model = User
        fields = [
            'nombre_supermercado', 'logo', 'provincia', 'localidad'
        ]
    
    def validate_logo(self, value):
        """Validar logo si se proporciona"""
        if value:
            # Validar extensión
            if not value.name.lower().endswith(('.jpg', '.jpeg')):
                raise serializers.ValidationError(
                    "El logo debe ser un archivo JPG o JPEG"
                )
            
            # Validar tamaño (máximo 1MB)
            if value.size > 1 * 1024 * 1024:
                raise serializers.ValidationError(
                    "El logo no puede ser mayor a 1MB"
                )
        
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña del usuario"""
    
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    def validate_current_password(self, value):
        """Verificar que la contraseña actual sea correcta"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta")
        return value
    
    def validate_new_password(self, value):
        """Validar nueva contraseña según los criterios especificados"""
        # Mínimo 8 caracteres
        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres"
            )
        
        # Debe contener al menos un número
        if not re.search(r'\d', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número"
            )
        
        # Debe contener al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un carácter especial"
            )
        
        # Usar validadores de Django
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate(self, attrs):
        """Validar que las contraseñas nuevas coincidan"""
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden'
            })
        
        # Validar que la nueva contraseña sea diferente a la actual
        current_password = attrs.get('current_password')
        if new_password == current_password:
            raise serializers.ValidationError({
                'new_password': 'La nueva contraseña debe ser diferente a la actual'
            })
        
        return attrs
    
    def save(self):
        """Actualizar contraseña del usuario"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class EmpleadoRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevos empleados"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False)
    deposito = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = EmpleadoUser
        fields = [
            'email', 'nombre', 'apellido', 'dni', 'puesto',
            'deposito', 'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        # Si no se proporciona password_confirm, usar el mismo password
        if 'password_confirm' not in attrs or not attrs['password_confirm']:
            attrs['password_confirm'] = attrs['password']
        
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })
        
        # Validar DNI
        dni = attrs.get('dni', '')
        if not dni.isdigit() or len(dni) < 7 or len(dni) > 8:
            raise serializers.ValidationError({
                'dni': 'El DNI debe tener entre 7 y 8 dígitos'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Crear nuevo empleado"""
        from inventario.models import Deposito
        
        # Remover campos que no van directamente al modelo
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        deposito_id = validated_data.pop('deposito')
        
        # Obtener el supermercado del contexto
        supermercado = self.context.get('supermercado')
        if not supermercado:
            raise serializers.ValidationError({
                'supermercado': 'No se pudo identificar el supermercado'
            })
        
        # Obtener el depósito y validar que pertenezca al supermercado
        try:
            deposito = Deposito.objects.get(id=deposito_id, supermercado=supermercado)
        except Deposito.DoesNotExist:
            raise serializers.ValidationError({
                'deposito': 'El depósito especificado no existe o no pertenece a su supermercado'
            })
        
        # Generar username único desde email
        base_username = validated_data['email'].split('@')[0]
        username = base_username
        counter = 1
        
        while EmpleadoUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        validated_data['username'] = username
        validated_data['deposito'] = deposito
        validated_data['supermercado'] = supermercado
        
        # Crear empleado
        empleado = EmpleadoUser.objects.create_user(
            password=password,
            **validated_data
        )
        
        return empleado


class EmpleadoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar empleados"""
    
    deposito = serializers.IntegerField(required=False)
    
    class Meta:
        model = EmpleadoUser
        fields = ['email', 'nombre', 'apellido', 'dni', 'puesto', 'deposito', 'is_active']
    
    def validate_dni(self, value):
        """Validar formato de DNI"""
        if not value.isdigit() or len(value) < 7 or len(value) > 8:
            raise serializers.ValidationError('El DNI debe tener entre 7 y 8 dígitos')
        return value
    
    def update(self, instance, validated_data):
        """Actualizar empleado"""
        from inventario.models import Deposito
        
        # Si se actualiza el depósito
        if 'deposito' in validated_data:
            deposito_id = validated_data.pop('deposito')
            try:
                deposito = Deposito.objects.get(id=deposito_id)
                instance.deposito = deposito
            except Deposito.DoesNotExist:
                raise serializers.ValidationError({
                    'deposito': 'El depósito especificado no existe'
                })
        
        # Actualizar otros campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
