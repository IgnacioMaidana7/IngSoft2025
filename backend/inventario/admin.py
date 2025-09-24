from django.contrib import admin
from .models import Deposito, Transferencia, DetalleTransferencia, HistorialMovimiento


class DetalleTransferenciaInline(admin.TabularInline):
    model = DetalleTransferencia
    extra = 1
    readonly_fields = ['fecha_creacion']


@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'direccion', 'supermercado', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'supermercado', 'fecha_creacion')
    search_fields = ('nombre', 'direccion', 'supermercado__username')
    ordering = ('-fecha_creacion',)


@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'deposito_origen', 'deposito_destino', 'administrador', 'estado', 'fecha_transferencia')
    list_filter = ('estado', 'fecha_transferencia', 'administrador')
    search_fields = ('deposito_origen__nombre', 'deposito_destino__nombre', 'administrador__username')
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    inlines = [DetalleTransferenciaInline]
    ordering = ('-fecha_transferencia',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('deposito_origen', 'deposito_destino', 'administrador')
        }),
        ('Detalles de la Transferencia', {
            'fields': ('fecha_transferencia', 'estado', 'observaciones')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetalleTransferencia)
class DetalleTransferenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'transferencia', 'producto', 'cantidad')
    list_filter = ('transferencia__estado', 'producto__categoria')
    search_fields = ('producto__nombre', 'transferencia__id')
    ordering = ('-fecha_creacion',)


@admin.register(HistorialMovimiento)
class HistorialMovimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'tipo_movimiento', 'producto', 'deposito_origen', 'deposito_destino', 'cantidad')
    list_filter = ('tipo_movimiento', 'fecha', 'administrador')
    search_fields = ('producto__nombre', 'deposito_origen__nombre', 'deposito_destino__nombre')
    readonly_fields = ['fecha_creacion']
    ordering = ('-fecha',)
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('fecha', 'tipo_movimiento', 'producto', 'cantidad')
        }),
        ('Depósitos', {
            'fields': ('deposito_origen', 'deposito_destino')
        }),
        ('Transferencia Relacionada', {
            'fields': ('transferencia', 'detalle_transferencia'),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('administrador', 'observaciones', 'fecha_creacion'),
            'classes': ('collapse',)
        }),
    )
