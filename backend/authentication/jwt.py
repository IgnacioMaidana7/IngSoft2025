from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
from .models import EmpleadoUser


class MultiUserJWTAuthentication(JWTAuthentication):
    """
    Autenticación JWT que soporta múltiples modelos de usuario.
    Distingue entre el usuario administrador (AUTH_USER_MODEL) y el usuario empleado
    usando el claim "user_type" agregado al token en el login.
    """

    def get_user(self, validated_token):
        user_type = validated_token.get("user_type", None)
        user_id = validated_token.get(api_settings.USER_ID_CLAIM)

        if user_id is None:
            raise InvalidToken("Token sin identificador de usuario")

        # Si el token es de empleado, buscar en EmpleadoUser
        if user_type == "empleado":
            try:
                return EmpleadoUser.objects.get(**{api_settings.USER_ID_FIELD: user_id})
            except EmpleadoUser.DoesNotExist:
                raise InvalidToken("Empleado no encontrado")

        # Caso contrario, usar el AUTH_USER_MODEL (administrador de supermercado)
        User = get_user_model()
        try:
            return User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist:
            raise InvalidToken("Usuario no encontrado")
