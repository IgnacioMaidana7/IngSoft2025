from django.urls import path
from . import views
from . import recognition_views

urlpatterns = [
    # URLs para categorías
    path('categorias/', views.CategoriaListCreateView.as_view(), name='categoria-list-create'),
    path('categorias/<int:pk>/', views.CategoriaDetailView.as_view(), name='categoria-detail'),
    path('categorias/disponibles/', views.obtener_categorias_disponibles, name='categorias-disponibles'),
    path('categorias/crear-personalizada/', views.crear_categoria_personalizada, name='crear-categoria-personalizada'),
    
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
    
    # URLs para reconocimiento de productos
    path('reconocer-imagen/', recognition_views.reconocer_productos_imagen, name='reconocer-productos-imagen'),
    path('catalogo-reconocimiento/', recognition_views.obtener_catalogo_reconocimiento, name='catalogo-reconocimiento'),
    path('verificar-api-reconocimiento/', recognition_views.verificar_api_reconocimiento, name='verificar-api-reconocimiento'),
]
