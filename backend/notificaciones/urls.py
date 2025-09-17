from django.urls import path
from . import views


urlpatterns = [
    path('', views.MisNotificacionesListView.as_view(), name='mis-notificaciones'),
    path('<int:notificacion_id>/leida/', views.MarcarNotificacionLeidaView.as_view(), name='notificacion-leida'),
]
