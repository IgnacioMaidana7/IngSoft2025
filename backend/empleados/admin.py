from django.contrib import admin
from .models import Empleado, Deposito


@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'direccion', 'supermercado', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'supermercado', 'fecha_creacion']
    search_fields = ['nombre', 'direccion', 'supermercado__nombre_supermercado']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Información del Depósito', {
            'fields': ('nombre', 'direccion', 'supermercado', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


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
