from django.urls import path
from .views import (
    RegisterView, 
    CustomTokenObtainPairView, 
    UserProfileView,
    EmpleadoLoginView,
    SupermercadoLoginView,
    EmpleadoProfileView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Registro
    path('register/', RegisterView.as_view(), name='register'),
    
    # Autenticación - Supermercados (Administradores)
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Mantener compatibilidad
    path('supermercado/login/', SupermercadoLoginView.as_view(), name='supermercado_login'),
    
    # Autenticación - Empleados
    path('empleado/login/', EmpleadoLoginView.as_view(), name='empleado_login'),
    
    # Tokens
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Perfiles
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('empleado/profile/', EmpleadoProfileView.as_view(), name='empleado_profile'),
]
