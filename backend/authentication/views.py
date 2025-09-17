from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, EmpleadoUser
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    EmpleadoLoginSerializer,
    EmpleadoUserSerializer,
    SupermercadoLoginSerializer
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para login con email"""
    
    # Indicamos al serializer padre que el campo de login es 'email'
    username_field = 'email'
    email = serializers.EmailField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remover el campo username ya que usaremos email
        if 'username' in self.fields:
            del self.fields['username']
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        print(f"DEBUG - Email recibido: {email}")
        print(f"DEBUG - Password recibido: {'*' * len(password) if password else 'None'}")

        if not email or not password:
            raise serializers.ValidationError('Debe incluir "email" y "password".')

        # Normalizar email para evitar fallos por mayúsculas/espacios
        normalized_email = email.strip().lower()
        attrs['email'] = normalized_email

        try:
            # Verificar que exista el usuario para un mensaje de error más claro
            user = User.objects.get(email=normalized_email)
            print(f"DEBUG - Usuario encontrado: {user.username}, activo: {user.is_active}")
        except User.DoesNotExist:
            print(f"DEBUG - Usuario no encontrado con email: {normalized_email}")
            raise serializers.ValidationError('No existe un usuario con este email.')

        # Delegar autenticación al serializer padre (usa username_field='email')
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para login"""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """Vista para registro de nuevos usuarios/supermercados"""
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        print(f"Request data: {request.data}")  # Debug logging
        print(f"Request files: {request.FILES}")  # Debug logging
        
        serializer = self.get_serializer(data=request.data)
        
        try:
            if serializer.is_valid():
                user = serializer.save()
                
                # Respuesta exitosa
                return Response(
                    {
                        'message': 'Registro exitoso. Ahora puede iniciar sesión.',
                        'user': UserSerializer(user).data
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                # Manejar errores de validación
                errors = serializer.errors
                print(f"Validation errors: {errors}")  # Debug logging
                
                # Formatear errores para el frontend
                formatted_errors = {}
                for field, error_list in errors.items():
                    if isinstance(error_list, list):
                        formatted_errors[field] = error_list[0]
                    else:
                        formatted_errors[field] = str(error_list)
                
                return Response(
                    {
                        'message': 'Error en los datos proporcionados',
                        'errors': formatted_errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {
                    'message': 'Error interno del servidor',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vista para obtener y actualizar perfil del usuario"""
    
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


class EmpleadoLoginView(APIView):
    """Vista para login de empleados usando email y DNI"""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EmpleadoLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            # Inyectar claim para distinguir tipo de usuario al autenticar el JWT
            refresh["user_type"] = "empleado"
            
            return Response({
                'message': 'Login exitoso',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': EmpleadoUserSerializer(user).data,
                'user_type': 'empleado'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Credenciales inválidas',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SupermercadoLoginView(APIView):
    """Vista para login de administradores de supermercado"""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SupermercadoLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            # Inyectar claim para distinguir tipo de usuario al autenticar el JWT
            refresh["user_type"] = "supermercado"
            
            return Response({
                'message': 'Login exitoso',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'user_type': 'supermercado'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Credenciales inválidas',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EmpleadoProfileView(generics.RetrieveAPIView):
    """Vista para obtener perfil del empleado"""
    
    serializer_class = EmpleadoUserSerializer
    
    def get_object(self):
        # Verificar que el usuario autenticado sea un empleado
        if not isinstance(self.request.user, EmpleadoUser):
            raise serializers.ValidationError("Solo los empleados pueden acceder a este endpoint")
        return self.request.user
