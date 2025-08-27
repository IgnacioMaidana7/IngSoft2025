from django.urls import path
from . import views

urlpatterns = [
    # URLs para depósitos
    path('depositos/', views.DepositoListCreateView.as_view(), name='deposito-list-create'),
    path('depositos/<int:pk>/', views.DepositoDetailView.as_view(), name='deposito-detail'),
    path('depositos/disponibles/', views.obtener_depositos_disponibles, name='depositos-disponibles'),
    path('depositos/estadisticas/', views.estadisticas_depositos, name='estadisticas-depositos'),
    
    # URLs para empleados
    path('', views.EmpleadoListCreateView.as_view(), name='empleado-list-create'),
    path('<int:pk>/', views.EmpleadoDetailView.as_view(), name='empleado-detail'),
    
    # URLs para obtener datos auxiliares
    path('roles/', views.obtener_roles_disponibles, name='roles-disponibles'),
    path('estadisticas/', views.estadisticas_empleados, name='estadisticas-empleados'),
]
