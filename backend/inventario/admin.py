from django.contrib import admin
from .models import Deposito


@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'direccion', 'supermercado', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'supermercado', 'fecha_creacion')
    search_fields = ('nombre', 'direccion', 'supermercado__username')
    ordering = ('-fecha_creacion',)
