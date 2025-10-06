"""
Comando Django para crear los productos necesarios para el sistema de reconocimiento.
Crea los 3 productos principales y actualiza el archivo product_mapping.json
con los IDs generados.

Uso: python manage.py crear_productos_reconocimiento
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from productos.models import Producto, Categoria
import json
import os


class Command(BaseCommand):
    help = 'Crea los productos necesarios para el sistema de reconocimiento'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🚀 Iniciando creación de productos para reconocimiento...'))

        # Productos a crear (basados en la API de reconocimiento)
        productos_config = [
            {
                'api_id': 5,
                'nombre': 'Fritolim Aceite en Aerosol',
                'descripcion': 'Aceite en aerosol Fritolim de 120g - SKU: FRITO-ACEIT-120ML',
                'precio': 680.00,
                'stock': 50,
                'categoria_nombre': 'Alimentos',
                'api_name': 'fritolim',
                'sku': 'FRITO-ACEIT-120ML'
            },
            {
                'api_id': 2,
                'nombre': 'Desodorante Nivea 150ml',
                'descripcion': 'Desodorante Nivea en aerosol de 150ml - SKU: NIVEA-DEO-150ML',
                'precio': 890.00,
                'stock': 30,
                'categoria_nombre': 'Cuidado Personal',
                'api_name': 'desodorante_nivea',
                'sku': 'NIVEA-DEO-150ML'
            },
            {
                'api_id': 1,
                'nombre': 'Puré de Tomate Noel 530g',
                'descripcion': 'Puré de tomate Noel de 530g - SKU: NOEL-TOMATE-520G',
                'precio': 450.00,
                'stock': 40,
                'categoria_nombre': 'Alimentos',
                'api_name': 'pure_tomate_caja',
                'sku': 'NOEL-TOMATE-520G'
            }
        ]

        mapping_updates = {}

        with transaction.atomic():
            for prod_config in productos_config:
                # Crear o actualizar categoría
                categoria, created = Categoria.objects.get_or_create(
                    nombre=prod_config['categoria_nombre']
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Categoría creada: {categoria.nombre}')
                    )

                # Verificar si el producto ya existe (por nombre exacto)
                producto_existente = Producto.objects.filter(
                    nombre=prod_config['nombre'],
                    categoria=categoria
                ).first()

                if producto_existente:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Producto ya existe: {producto_existente.nombre} (ID: {producto_existente.id})'
                        )
                    )
                    producto = producto_existente
                else:
                    # Crear nuevo producto
                    producto = Producto.objects.create(
                        nombre=prod_config['nombre'],
                        descripcion=prod_config['descripcion'],
                        precio=prod_config['precio'],
                        categoria=categoria
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Producto creado: {producto.nombre} (ID: {producto.id})'
                        )
                    )

                # Guardar el mapeo para actualizar product_mapping.json
                mapping_updates[str(prod_config['api_id'])] = {
                    'ingsoft_id': producto.id,
                    'nombre_django': producto.nombre,
                    'sku': prod_config['sku'],
                    'api_name': prod_config['api_name']
                }

        # Intentar actualizar product_mapping.json
        self.actualizar_mapping_file(mapping_updates)

        self.stdout.write(self.style.SUCCESS('\n✅ ¡Proceso completado exitosamente!'))
        self.stdout.write(self.style.SUCCESS(f'   Total productos procesados: {len(productos_config)}'))
        self.stdout.write(self.style.WARNING('\n📝 IMPORTANTE: Verifica el archivo product_mapping.json'))
        self.stdout.write(self.style.WARNING('   en el proyecto shelf-product-identifier'))

    def actualizar_mapping_file(self, mapping_updates):
        """Actualiza el archivo product_mapping.json con los IDs de Django"""
        # Intentar encontrar el archivo product_mapping.json
        possible_paths = [
            r'c:\Users\osval\Documents\GitHub\shelf-product-identifier\product_mapping.json',
            os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 
                        'shelf-product-identifier', 'product_mapping.json')
        ]

        mapping_file = None
        for path in possible_paths:
            if os.path.exists(path):
                mapping_file = path
                break

        if not mapping_file:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  No se encontró product_mapping.json. '
                    'Deberás actualizarlo manualmente con estos IDs:'
                )
            )
            self.stdout.write(json.dumps(mapping_updates, indent=2))
            return

        try:
            # Leer el archivo actual
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)

            # Actualizar los ingsoft_ids
            for api_id, update_info in mapping_updates.items():
                if api_id in mapping_data['ingsoft_mapping']:
                    mapping_data['ingsoft_mapping'][api_id]['ingsoft_id'] = update_info['ingsoft_id']
                    mapping_data['ingsoft_mapping'][api_id]['status'] = 'mapped'
                    mapping_data['ingsoft_mapping'][api_id]['notes'] = f"Mapeado automáticamente - ID Django: {update_info['ingsoft_id']}"

            # Actualizar el mapeo inverso
            if 'ingsoft_to_shelf' not in mapping_data:
                mapping_data['ingsoft_to_shelf'] = {}

            for api_id, update_info in mapping_updates.items():
                ingsoft_id = str(update_info['ingsoft_id'])
                mapping_data['ingsoft_to_shelf'][ingsoft_id] = {
                    'shelf_product_id': int(api_id),
                    'confidence_mapping': 1.0,
                    'verified': True,
                    'nombre': update_info['nombre_django']
                }

            # Guardar el archivo actualizado
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping_data, f, indent=2, ensure_ascii=False)

            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Archivo product_mapping.json actualizado: {mapping_file}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error al actualizar product_mapping.json: {str(e)}')
            )
            self.stdout.write(
                self.style.WARNING('Mapeo manual necesario:')
            )
            self.stdout.write(json.dumps(mapping_updates, indent=2))
