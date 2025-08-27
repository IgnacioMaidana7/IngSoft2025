from django.urls import path
from . import views

urlpatterns = [
    # URLs para depósitos
    path('depositos/', views.DepositoListCreateView.as_view(), name='deposito-list-create'),
    path('depositos/<int:pk>/', views.DepositoDetailView.as_view(), name='deposito-detail'),
    path('depositos/disponibles/', views.obtener_depositos_disponibles, name='depositos-disponibles'),
    path('depositos/estadisticas/', views.estadisticas_depositos, name='estadisticas-depositos'),
]
