from django.urls import path
from . import views

urlpatterns = [
    # URLs para categorías
    path('categorias/', views.CategoriaListCreateView.as_view(), name='categoria-list-create'),
    path('categorias/<int:pk>/', views.CategoriaDetailView.as_view(), name='categoria-detail'),
    path('categorias/disponibles/', views.obtener_categorias_disponibles, name='categorias-disponibles'),
    
    # URLs para productos
    path('', views.ProductoListCreateView.as_view(), name='producto-list-create'),
    path('<int:pk>/', views.ProductoDetailView.as_view(), name='producto-detail'),
    path('estadisticas/', views.estadisticas_productos, name='estadisticas-productos'),
    
    # URLs para stock de productos
    path('<int:producto_id>/stock/', views.gestionar_stock_producto, name='producto-stock'),
    path('<int:producto_id>/stock-completo/', views.obtener_stock_completo_producto, name='producto-stock-completo'),
    path('<int:producto_id>/actualizar-stock/', views.actualizar_stock_completo_producto, name='actualizar-stock-completo'),
    path('stock/<int:stock_id>/', views.stock_producto_detail, name='stock-detail'),
    path('deposito/<int:deposito_id>/', views.productos_por_deposito, name='productos-por-deposito'),
]
