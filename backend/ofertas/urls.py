from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OfertaViewSet, ProductoOfertaViewSet

router = DefaultRouter()
router.register(r'ofertas', OfertaViewSet, basename='ofertas')
router.register(r'producto-ofertas', ProductoOfertaViewSet, basename='producto-ofertas')

urlpatterns = [
    path('api/', include(router.urls)),
]
