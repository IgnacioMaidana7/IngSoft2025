from django.urls import path
from . import views

app_name = 'empleados'

urlpatterns = [
    # URLs para empleados
    path('', views.EmpleadoListCreateView.as_view(), name='empleado-list-create'),
    path('<int:pk>/', views.EmpleadoDetailView.as_view(), name='empleado-detail'),
    path('deposito/<int:deposito_id>/', views.obtener_empleados_por_deposito, name='empleados-por-deposito'),
    path('estadisticas/', views.estadisticas_empleados, name='estadisticas'),
    path('<int:pk>/cambiar-estado/', views.cambiar_estado_empleado, name='cambiar-estado'),
    path('roles/', views.obtener_roles_disponibles, name='roles-disponibles'),
]
