from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from authentication.models import EmpleadoUser

User = get_user_model()


class EmpleadoAuthBackend(BaseBackend):
    """
    Backend de autenticación personalizado para empleados.
    Permite autenticación con email y DNI como contraseña.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica un usuario empleado usando email como username y DNI como password.
        """
        if username is None or password is None:
            return None
        
        try:
            # Buscar el usuario empleado por email
            usuario_empleado = EmpleadoUser.objects.get(
                email=username,
                is_active=True
            )
            
            # Verificar que el DNI (password) coincida
            if usuario_empleado.dni == password:
                return usuario_empleado
            else:
                return None
                
        except EmpleadoUser.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """
        Obtiene un usuario empleado por su ID.
        """
        try:
            return EmpleadoUser.objects.get(pk=user_id, is_active=True)
        except EmpleadoUser.DoesNotExist:
            return None


class SupermercadoAuthBackend(BaseBackend):
    """
    Backend de autenticación para administradores de supermercado.
    Permite autenticación con email y contraseña tradicional.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica un administrador de supermercado usando email y contraseña.
        """
        if username is None or password is None:
            return None
        
        try:
            # Buscar el usuario administrador por email
            usuario = User.objects.get(
                email=username,
                is_active=True
            )
            
            # Verificar la contraseña usando el método check_password
            if usuario.check_password(password):
                return usuario
            else:
                return None
                
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """
        Obtiene un usuario administrador por su ID.
        """
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None