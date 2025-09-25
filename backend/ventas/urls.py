from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VentaViewSet, obtener_productos_disponibles, buscar_productos

router = DefaultRouter()
router.register(r'ventas', VentaViewSet, basename='venta')

urlpatterns = [
    path('', include(router.urls)),
    path('productos-disponibles/', obtener_productos_disponibles, name='productos-disponibles'),
    path('buscar-productos/', buscar_productos, name='buscar-productos'),
]
