from django.urls import path
from .views import RegisterView, CustomTokenObtainPairView, UserProfileView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Registro
    path('register/', RegisterView.as_view(), name='register'),
    
    # Autenticación
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Perfil de usuario
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
