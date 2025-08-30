from django.contrib import admin
from .models import Categoria, Producto, ProductoDeposito

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'activo', 'fecha_creacion')
    list_filter = ('categoria', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')

@admin.register(ProductoDeposito)
class ProductoDepositoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'deposito', 'cantidad', 'cantidad_minima', 'tiene_stock', 'stock_bajo')
    list_filter = ('deposito', 'fecha_creacion')
    search_fields = ('producto__nombre', 'deposito__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
