from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VentaViewSet, 
    obtener_productos_disponibles, 
    buscar_productos,
    historial_ventas,
    descargar_ticket_pdf
)

router = DefaultRouter()
router.register(r'ventas', VentaViewSet, basename='venta')

urlpatterns = [
    path('', include(router.urls)),
    path('productos-disponibles/', obtener_productos_disponibles, name='productos-disponibles'),
    path('buscar-productos/', buscar_productos, name='buscar-productos'),
    path('historial/', historial_ventas, name='historial-ventas'),
    path('ticket/<int:venta_id>/pdf/', descargar_ticket_pdf, name='descargar-ticket-pdf'),
]
