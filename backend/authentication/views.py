from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import requests
from .models import User, EmpleadoUser
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    EmpleadoLoginSerializer,
    EmpleadoUserSerializer,
    SupermercadoLoginSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer
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

        if not email or not password:
            raise serializers.ValidationError('Debe incluir "email" y "password".')

        # Normalizar email para evitar fallos por mayúsculas/espacios
        normalized_email = email.strip().lower()
        attrs['email'] = normalized_email

        try:
            # Verificar que exista el usuario para un mensaje de error más claro
            user = User.objects.get(email=normalized_email)
        except User.DoesNotExist:
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
                    'error': str(e),
                    'type': type(e).__name__
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vista para obtener y actualizar perfil del usuario"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Usar diferentes serializers para GET y PUT/PATCH"""
        if self.request.method == 'GET':
            return UserSerializer
        return UserProfileUpdateSerializer
    
    def get_object(self):
        # Verificar que el usuario autenticado sea un administrador (User, no EmpleadoUser)
        if isinstance(self.request.user, EmpleadoUser):
            raise serializers.ValidationError(
                "Solo los administradores pueden acceder a este endpoint"
            )
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        """Actualizar perfil del usuario"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # Devolver los datos completos del usuario
            return Response({
                'message': 'Perfil actualizado exitosamente',
                'user': UserSerializer(instance).data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                'message': 'Error en los datos proporcionados',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Vista para cambiar contraseña del usuario"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Verificar que el usuario autenticado sea un administrador (User, no EmpleadoUser)
        if isinstance(request.user, EmpleadoUser):
            return Response({
                'message': 'Solo los administradores pueden cambiar su contraseña desde aquí'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Contraseña actualizada exitosamente'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Error al cambiar la contraseña',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


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


# Vistas proxy para API de Georef (resolver CORS)

class ProvinciasProxyView(APIView):
    """Proxy para obtener provincias desde la API de Georef"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            print("📍 Intentando obtener provincias...")
            
            # Configurar sesión con reintentos
            session = requests.Session()
            retry_strategy = requests.adapters.Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            response = session.get(
                'https://apis.datos.gob.ar/georef/api/provincias',
                params={'campos': 'id,nombre'},
                timeout=30  # Aumentar timeout a 30 segundos
            )
            response.raise_for_status()
            data = response.json()
            return Response(data, status=status.HTTP_200_OK)
        except requests.exceptions.Timeout as e:
            return Response(
                {
                    'error': 'Timeout al conectar con el servicio de provincias',
                    'message': 'El servidor de datos geográficos está tardando demasiado. Por favor, intenta nuevamente en unos momentos.',
                    'detail': str(e)
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {
                    'error': 'Error al obtener provincias',
                    'message': 'No se pudo conectar con el servicio de datos geográficos. Verifica tu conexión a internet.',
                    'detail': str(e)
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LocalidadesProxyView(APIView):
    """Proxy para obtener localidades desde la API de Georef"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        provincia = request.query_params.get('provincia')
        if not provincia:
            return Response(
                {'error': 'El parámetro "provincia" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Configurar sesión con reintentos
            session = requests.Session()
            retry_strategy = requests.adapters.Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            response = session.get(
                'https://apis.datos.gob.ar/georef/api/localidades',
                params={
                    'provincia': provincia,
                    'campos': 'id,nombre',
                    'max': 1000
                },
                timeout=30  # Aumentar timeout a 30 segundos
            )
            response.raise_for_status()
            data = response.json()
            return Response(data, status=status.HTTP_200_OK)
        except requests.exceptions.Timeout as e:
            return Response(
                {
                    'error': 'Timeout al conectar con el servicio de localidades',
                    'message': 'El servidor de datos geográficos está tardando demasiado. Por favor, intenta nuevamente en unos momentos.',
                    'detail': str(e)
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {
                    'error': 'Error al obtener localidades',
                    'message': 'No se pudo conectar con el servicio de datos geográficos. Verifica tu conexión a internet.',
                    'detail': str(e)
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EmpleadoListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear empleados"""
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Desactivar paginación para retornar lista directa
    
    def get_serializer_class(self):
        from .serializers import EmpleadoUserSerializer, EmpleadoRegistrationSerializer
        if self.request.method == 'POST':
            return EmpleadoRegistrationSerializer
        return EmpleadoUserSerializer
    
    def get_serializer_context(self):
        """Agregar el supermercado al contexto del serializer"""
        context = super().get_serializer_context()
        context['supermercado'] = self.request.user
        return context
    
    def get_queryset(self):
        """Filtrar empleados del supermercado autenticado"""
        user = self.request.user
        if hasattr(user, 'empleados_usuarios'):
            # Si es un User (supermercado), mostrar sus empleados
            return EmpleadoUser.objects.filter(supermercado=user)
        return EmpleadoUser.objects.none()
    
    def perform_create(self, serializer):
        """El supermercado ya se asigna en el serializer"""
        serializer.save()


class EmpleadoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar un empleado específico"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import EmpleadoUserSerializer, EmpleadoUpdateSerializer
        if self.request.method in ['PUT', 'PATCH']:
            return EmpleadoUpdateSerializer
        return EmpleadoUserSerializer
    
    def get_queryset(self):
        """Solo permitir acceso a empleados del supermercado autenticado"""
        user = self.request.user
        if hasattr(user, 'empleados_usuarios'):
            return EmpleadoUser.objects.filter(supermercado=user)
        return EmpleadoUser.objects.none()


class RolesListView(APIView):
    """Vista para obtener la lista de roles disponibles"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retornar los roles disponibles"""
        roles = [
            {'value': choice[0], 'label': choice[1]}
            for choice in EmpleadoUser.ROLES_CHOICES
        ]
        return Response({
            'success': True,
            'roles': roles
        }, status=status.HTTP_200_OK)


class EstadisticasEmpleadosView(APIView):
    """Vista para obtener estadísticas de empleados"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retornar estadísticas de empleados del supermercado"""
        from django.db.models import Count
        
        user = request.user
        
        # Filtrar empleados del supermercado autenticado
        empleados = EmpleadoUser.objects.filter(supermercado=user)
        
        # Contar totales
        total_empleados = empleados.count()
        empleados_activos = empleados.filter(is_active=True).count()
        empleados_inactivos = empleados.filter(is_active=False).count()
        
        # Empleados por puesto
        empleados_por_puesto = list(
            empleados.values('puesto')
            .annotate(total=Count('id'))
            .order_by('puesto')
        )
        
        # Empleados por depósito
        empleados_por_deposito = list(
            empleados.values('deposito__id', 'deposito__nombre')
            .annotate(total_empleados=Count('id'))
            .order_by('deposito__nombre')
        )
        
        # Formatear empleados_por_deposito
        empleados_por_deposito_formatted = [
            {
                'id': item['deposito__id'],
                'nombre': item['deposito__nombre'],
                'total_empleados': item['total_empleados']
            }
            for item in empleados_por_deposito
        ]
        
        return Response({
            'success': True,
            'data': {
                'total_empleados': total_empleados,
                'empleados_activos': empleados_activos,
                'empleados_inactivos': empleados_inactivos,
                'empleados_por_puesto': empleados_por_puesto,
                'empleados_por_deposito': empleados_por_deposito_formatted
            }
        }, status=status.HTTP_200_OK)
