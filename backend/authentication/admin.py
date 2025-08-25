from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Configuración del admin para el modelo User personalizado"""
    
    list_display = ['email', 'nombre_supermercado', 'cuil', 'provincia', 'localidad', 'is_active', 'fecha_registro']
    list_filter = ['is_active', 'provincia', 'fecha_registro']
    search_fields = ['email', 'nombre_supermercado', 'cuil']
    ordering = ['-fecha_registro']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información del Supermercado', {
            'fields': ('nombre_supermercado', 'logo', 'cuil')
        }),
        ('Ubicación', {
            'fields': ('provincia', 'localidad')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Fechas importantes', {
            'fields': ('last_login', 'date_joined', 'fecha_registro')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre_supermercado', 'cuil', 'provincia', 'localidad', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['fecha_registro']
