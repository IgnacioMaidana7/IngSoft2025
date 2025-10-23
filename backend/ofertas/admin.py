from django.contrib import admin
from .models import Oferta, ProductoOferta

@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo_descuento', 'valor_descuento', 'fecha_inicio', 
        'fecha_fin', 'estado', 'activo', 'fecha_creacion'
    ]
    list_filter = ['tipo_descuento', 'activo', 'fecha_creacion', 'fecha_inicio', 'fecha_fin']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion', 'estado']
    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Descuento', {
            'fields': ('tipo_descuento', 'valor_descuento')
        }),
        ('Vigencia', {
            'fields': ('fecha_inicio', 'fecha_fin', 'activo')
        }),
        ('Información del sistema', {
            'fields': ('estado', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        # Si la oferta está expirada, hacer todos los campos de solo lectura excepto activo
        if obj and obj.estado == 'expirada':
            readonly.extend(['nombre', 'descripcion', 'tipo_descuento', 'valor_descuento', 'fecha_inicio', 'fecha_fin'])
        return readonly


@admin.register(ProductoOferta)
class ProductoOfertaAdmin(admin.ModelAdmin):
    list_display = [
        'producto', 'oferta', 'precio_original', 'precio_con_descuento', 
        'descuento_aplicado', 'fecha_asignacion'
    ]
    list_filter = ['oferta', 'producto__categoria', 'fecha_asignacion']
    search_fields = ['producto__nombre', 'oferta__nombre']
    readonly_fields = ['fecha_asignacion', 'descuento_aplicado', 'porcentaje_descuento']
    raw_id_fields = ['producto', 'oferta']
    
    fieldsets = (
        ('Relación', {
            'fields': ('producto', 'oferta')
        }),
        ('Precios', {
            'fields': ('precio_original', 'precio_con_descuento')
        }),
        ('Información calculada', {
            'fields': ('descuento_aplicado', 'porcentaje_descuento', 'fecha_asignacion'),
            'classes': ('collapse',)
        }),
    )
