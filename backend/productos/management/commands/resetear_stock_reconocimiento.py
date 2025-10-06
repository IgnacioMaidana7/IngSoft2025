"""
Comando Django para resetear el stock a 0 de los productos de reconocimiento.
Útil para limpiar la base de datos y empezar de cero con el stock.

Uso: python manage.py resetear_stock_reconocimiento
"""

from django.core.management.base import BaseCommand
from django.db import transaction, models
from productos.models import Producto, ProductoDeposito


class Command(BaseCommand):
    help = 'Resetea el stock a 0 de los productos de reconocimiento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Resetear stock de TODOS los productos (no solo los de reconocimiento)',
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirmar la acción sin preguntar',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('⚠️  RESETEAR STOCK A 0'))
        self.stdout.write()

        # Determinar qué productos resetear
        if options['todos']:
            productos = Producto.objects.all()
            mensaje = 'TODOS los productos'
        else:
            # Solo productos de reconocimiento (IDs basados en los que creamos)
            productos_nombres = [
                'Fritolim Aceite en Aerosol',
                'Desodorante Nivea 150ml',
                'Puré de Tomate Noel 530g',
                'Raid Insecticida 233g'
            ]
            productos = Producto.objects.filter(nombre__in=productos_nombres)
            mensaje = 'los productos de reconocimiento'

        if not productos.exists():
            self.stdout.write(self.style.ERROR('❌ No se encontraron productos para resetear'))
            return

        # Mostrar productos que se van a resetear
        self.stdout.write(f'Se resetearán {productos.count()} productos:')
        for prod in productos:
            stock_actual = ProductoDeposito.objects.filter(producto=prod).aggregate(
                total=models.Sum('cantidad')
            )['total'] or 0
            self.stdout.write(f'  • {prod.nombre} (Stock actual: {stock_actual})')

        self.stdout.write()

        # Confirmar acción
        if not options['confirmar']:
            confirmacion = input('¿Estás seguro de resetear el stock a 0? (si/no): ')
            if confirmacion.lower() not in ['si', 's', 'yes', 'y']:
                self.stdout.write(self.style.WARNING('❌ Operación cancelada'))
                return

        # Resetear stock
        with transaction.atomic():
            productos_ids = list(productos.values_list('id', flat=True))
            
            # Resetear stock en todos los depósitos
            stock_actualizado = ProductoDeposito.objects.filter(
                producto_id__in=productos_ids
            ).update(cantidad=0)

            self.stdout.write()
            self.stdout.write(self.style.SUCCESS(f'✅ Stock reseteado exitosamente'))
            self.stdout.write(self.style.SUCCESS(f'   {stock_actualizado} registros de stock actualizados a 0'))

        # Verificar resultado
        self.stdout.write()
        self.stdout.write('📊 Verificación:')
        for prod in productos:
            stock_depositos = ProductoDeposito.objects.filter(producto=prod)
            if stock_depositos.exists():
                for stock_dep in stock_depositos:
                    self.stdout.write(
                        f'   ✅ {prod.nombre} - Depósito: {stock_dep.deposito.nombre} - Stock: {stock_dep.cantidad}'
                    )
            else:
                self.stdout.write(f'   ℹ️  {prod.nombre} - Sin registros de stock')

        self.stdout.write()
        self.stdout.write(self.style.SUCCESS('✅ ¡Proceso completado!'))

