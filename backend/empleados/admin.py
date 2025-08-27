from django.contrib import admin
from .models import Empleado


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['get_nombre_completo', 'email', 'puesto', 'deposito', 'supermercado', 'activo']
    list_filter = ['puesto', 'activo', 'deposito', 'supermercado', 'fecha_ingreso']
    search_fields = ['nombre', 'apellido', 'email', 'dni']
    readonly_fields = ['fecha_ingreso', 'fecha_modificacion']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'email', 'dni')
        }),
        ('Información Laboral', {
            'fields': ('puesto', 'deposito', 'supermercado', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_ingreso', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_nombre_completo(self, obj):
        return obj.get_nombre_completo()
    get_nombre_completo.short_description = 'Nombre Completo'
