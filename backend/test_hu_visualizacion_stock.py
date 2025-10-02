"""
Tests específicos para la Historia de Usuario:
"Como administrador quiero visualizar el stock total y de cada depósito"

Criterios de aceptación:
1. El administrador puede visualizar el stock total de cada producto desde la vista de "Productos".
2. El administrador puede ver el stock de cada depósito desde la vista "Gestionar mis Depósitos".
3. En ambos casos, se debe desplegar una lista con el nombre del producto y su stock, total o por depósito correspondientemente.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from productos.models import Categoria, Producto, ProductoDeposito
from inventario.models import Deposito

User = get_user_model()


class StockVisualizationTestCase(TestCase):
    """Tests para visualización de stock total y por depósito"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            email='admin@stocktest.com',
            username='admin_stock',
            password='StrongPass1!',
            nombre_supermercado='SuperStock',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata',
        )
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categorías
        self.categoria_bebidas = Categoria.objects.create(
            nombre='Bebidas',
            descripcion='Bebidas varias'
        )
        self.categoria_lacteos = Categoria.objects.create(
            nombre='Lácteos',
            descripcion='Productos lácteos'
        )
        self.categoria_limpieza = Categoria.objects.create(
            nombre='Limpieza',
            descripcion='Productos de limpieza'
        )
        
        # Crear depósitos
        self.deposito_central = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Av. Principal 123',
            descripcion='Depósito principal',
            supermercado=self.admin_user
        )
        self.deposito_norte = Deposito.objects.create(
            nombre='Depósito Norte',
            direccion='Calle Norte 456',
            descripcion='Depósito zona norte',
            supermercado=self.admin_user
        )
        self.deposito_sur = Deposito.objects.create(
            nombre='Depósito Sur',
            direccion='Av. Sur 789',
            descripcion='Depósito zona sur',
            supermercado=self.admin_user
        )
        
        # Crear productos
        self.producto_agua = Producto.objects.create(
            nombre='Agua Mineral 1L',
            categoria=self.categoria_bebidas,
            precio=Decimal('100.50'),
            descripcion='Agua mineral sin gas'
        )
        self.producto_leche = Producto.objects.create(
            nombre='Leche Entera 1L',
            categoria=self.categoria_lacteos,
            precio=Decimal('200.00'),
            descripcion='Leche entera pasteurizada'
        )
        self.producto_detergente = Producto.objects.create(
            nombre='Detergente 500ml',
            categoria=self.categoria_limpieza,
            precio=Decimal('350.75'),
            descripcion='Detergente líquido concentrado'
        )
        self.producto_yogur = Producto.objects.create(
            nombre='Yogur Natural 200g',
            categoria=self.categoria_lacteos,
            precio=Decimal('150.25'),
            descripcion='Yogur natural cremoso'
        )
        
        # Crear stocks en diferentes depósitos
        # Agua: Total 150 unidades (50 + 75 + 25)
        ProductoDeposito.objects.create(
            producto=self.producto_agua,
            deposito=self.deposito_central,
            cantidad=50,
            cantidad_minima=10
        )
        ProductoDeposito.objects.create(
            producto=self.producto_agua,
            deposito=self.deposito_norte,
            cantidad=75,
            cantidad_minima=15
        )
        ProductoDeposito.objects.create(
            producto=self.producto_agua,
            deposito=self.deposito_sur,
            cantidad=25,
            cantidad_minima=5
        )
        
        # Leche: Total 80 unidades (30 + 50, sin stock en depósito sur)
        ProductoDeposito.objects.create(
            producto=self.producto_leche,
            deposito=self.deposito_central,
            cantidad=30,
            cantidad_minima=8
        )
        ProductoDeposito.objects.create(
            producto=self.producto_leche,
            deposito=self.deposito_norte,
            cantidad=50,
            cantidad_minima=12
        )
        
        # Detergente: Total 20 unidades (solo en depósito central)
        ProductoDeposito.objects.create(
            producto=self.producto_detergente,
            deposito=self.deposito_central,
            cantidad=20,
            cantidad_minima=3
        )
        
        # Yogur: Total 0 unidades (producto sin stock)
        ProductoDeposito.objects.create(
            producto=self.producto_yogur,
            deposito=self.deposito_central,
            cantidad=0,
            cantidad_minima=5
        )
    
    def test_visualizar_stock_total_vista_productos(self):
        """
        CA1: El administrador puede visualizar el stock total de cada producto 
        desde la vista de "Productos".
        """
        url = reverse('producto-list-create')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        productos = response.data['results']
        
        # Verificar que todos los productos están presentes
        nombres_productos = [p['nombre'] for p in productos]
        self.assertIn('Agua Mineral 1L', nombres_productos)
        self.assertIn('Leche Entera 1L', nombres_productos)
        self.assertIn('Detergente 500ml', nombres_productos)
        self.assertIn('Yogur Natural 200g', nombres_productos)
        
        # Verificar stock total para cada producto
        for producto in productos:
            if producto['nombre'] == 'Agua Mineral 1L':
                self.assertEqual(producto['stock_total'], 150)
                self.assertIn('categoria_nombre', producto)
                self.assertEqual(producto['categoria_nombre'], 'Bebidas')
            elif producto['nombre'] == 'Leche Entera 1L':
                self.assertEqual(producto['stock_total'], 80)
                self.assertEqual(producto['categoria_nombre'], 'Lácteos')
            elif producto['nombre'] == 'Detergente 500ml':
                self.assertEqual(producto['stock_total'], 20)
                self.assertEqual(producto['categoria_nombre'], 'Limpieza')
            elif producto['nombre'] == 'Yogur Natural 200g':
                self.assertEqual(producto['stock_total'], 0)
                self.assertEqual(producto['categoria_nombre'], 'Lácteos')
        
        # Verificar que se incluye información de depósitos
        for producto in productos:
            self.assertIn('depositos_count', producto)
    
    def test_visualizar_detalle_producto_con_stock_completo(self):
        """
        CA1 (detallado): Verificar que en el detalle de un producto se muestre 
        el stock total y el desglose por depósito.
        """
        url = reverse('producto-detail', kwargs={'pk': self.producto_agua.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        producto = response.data
        
        # Verificar información básica
        self.assertEqual(producto['nombre'], 'Agua Mineral 1L')
        self.assertEqual(producto['categoria_nombre'], 'Bebidas')
        self.assertEqual(producto['stock_total'], 150)
        
        # Verificar desglose por depósito
        self.assertIn('stocks', producto)
        stocks = producto['stocks']
        self.assertEqual(len(stocks), 3)  # Tres depósitos
        
        # Verificar stock en cada depósito
        stocks_por_deposito = {stock['deposito_nombre']: stock for stock in stocks}
        
        self.assertIn('Depósito Central', stocks_por_deposito)
        self.assertEqual(stocks_por_deposito['Depósito Central']['cantidad'], 50)
        self.assertTrue(stocks_por_deposito['Depósito Central']['tiene_stock'])
        
        self.assertIn('Depósito Norte', stocks_por_deposito)
        self.assertEqual(stocks_por_deposito['Depósito Norte']['cantidad'], 75)
        self.assertTrue(stocks_por_deposito['Depósito Norte']['tiene_stock'])
        
        self.assertIn('Depósito Sur', stocks_por_deposito)
        self.assertEqual(stocks_por_deposito['Depósito Sur']['cantidad'], 25)
        self.assertTrue(stocks_por_deposito['Depósito Sur']['tiene_stock'])
    
    def test_visualizar_stock_por_deposito_central(self):
        """
        CA2: El administrador puede ver el stock de cada depósito 
        desde la vista "Gestionar mis Depósitos" - Depósito Central.
        """
        url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_central.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar información del depósito
        self.assertIn('deposito', response.data)
        deposito_info = response.data['deposito']
        self.assertEqual(deposito_info['nombre'], 'Depósito Central')
        self.assertEqual(deposito_info['direccion'], 'Av. Principal 123')
        
        # Verificar productos en el depósito
        self.assertIn('productos', response.data)
        productos = response.data['productos']
        
        # Debe haber 4 productos (todos tienen stock o registro en este depósito)
        self.assertEqual(len(productos), 4)
        
        # Verificar cada producto y su stock
        productos_por_nombre = {p['nombre']: p for p in productos}
        
        # Agua Mineral
        self.assertIn('Agua Mineral 1L', productos_por_nombre)
        agua = productos_por_nombre['Agua Mineral 1L']
        self.assertEqual(agua['cantidad'], 50)
        self.assertEqual(agua['categoria'], 'Bebidas')
        self.assertTrue(agua['tiene_stock'])
        self.assertFalse(agua['stock_bajo'])  # 50 > 10 (cantidad_minima)
        
        # Leche
        self.assertIn('Leche Entera 1L', productos_por_nombre)
        leche = productos_por_nombre['Leche Entera 1L']
        self.assertEqual(leche['cantidad'], 30)
        self.assertEqual(leche['categoria'], 'Lácteos')
        self.assertTrue(leche['tiene_stock'])
        
        # Detergente
        self.assertIn('Detergente 500ml', productos_por_nombre)
        detergente = productos_por_nombre['Detergente 500ml']
        self.assertEqual(detergente['cantidad'], 20)
        self.assertEqual(detergente['categoria'], 'Limpieza')
        self.assertTrue(detergente['tiene_stock'])
        
        # Yogur (sin stock)
        self.assertIn('Yogur Natural 200g', productos_por_nombre)
        yogur = productos_por_nombre['Yogur Natural 200g']
        self.assertEqual(yogur['cantidad'], 0)
        self.assertEqual(yogur['categoria'], 'Lácteos')
        self.assertFalse(yogur['tiene_stock'])
        self.assertTrue(yogur['stock_bajo'])  # 0 <= 5 (cantidad_minima)
    
    def test_visualizar_stock_por_deposito_norte(self):
        """
        CA2: El administrador puede ver el stock del Depósito Norte.
        """
        url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_norte.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        deposito_info = response.data['deposito']
        self.assertEqual(deposito_info['nombre'], 'Depósito Norte')
        
        productos = response.data['productos']
        self.assertEqual(len(productos), 2)  # Solo Agua y Leche
        
        productos_por_nombre = {p['nombre']: p for p in productos}
        
        # Agua Mineral
        self.assertIn('Agua Mineral 1L', productos_por_nombre)
        agua = productos_por_nombre['Agua Mineral 1L']
        self.assertEqual(agua['cantidad'], 75)
        self.assertTrue(agua['tiene_stock'])
        
        # Leche
        self.assertIn('Leche Entera 1L', productos_por_nombre)
        leche = productos_por_nombre['Leche Entera 1L']
        self.assertEqual(leche['cantidad'], 50)
        self.assertTrue(leche['tiene_stock'])
        
        # No debe tener Detergente ni Yogur
        self.assertNotIn('Detergente 500ml', productos_por_nombre)
        self.assertNotIn('Yogur Natural 200g', productos_por_nombre)
    
    def test_visualizar_stock_por_deposito_sur(self):
        """
        CA2: El administrador puede ver el stock del Depósito Sur.
        """
        url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_sur.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        deposito_info = response.data['deposito']
        self.assertEqual(deposito_info['nombre'], 'Depósito Sur')
        
        productos = response.data['productos']
        self.assertEqual(len(productos), 1)  # Solo Agua
        
        productos_por_nombre = {p['nombre']: p for p in productos}
        
        # Solo Agua Mineral
        self.assertIn('Agua Mineral 1L', productos_por_nombre)
        agua = productos_por_nombre['Agua Mineral 1L']
        self.assertEqual(agua['cantidad'], 25)
        self.assertTrue(agua['tiene_stock'])
        
        # No debe tener otros productos
        self.assertNotIn('Leche Entera 1L', productos_por_nombre)
        self.assertNotIn('Detergente 500ml', productos_por_nombre)
        self.assertNotIn('Yogur Natural 200g', productos_por_nombre)
    
    def test_lista_productos_incluye_nombre_y_stock(self):
        """
        CA3: En la vista de productos se despliega lista con nombre del producto y su stock total.
        """
        url = reverse('producto-list-create')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos = response.data['results']
        
        for producto in productos:
            # Verificar que cada producto tiene los campos requeridos
            self.assertIn('nombre', producto)
            self.assertIn('stock_total', producto)
            
            # Verificar que el nombre no está vacío
            self.assertIsNotNone(producto['nombre'])
            self.assertGreater(len(producto['nombre']), 0)
            
            # Verificar que stock_total es un número
            self.assertIsInstance(producto['stock_total'], int)
            self.assertGreaterEqual(producto['stock_total'], 0)
    
    def test_lista_productos_por_deposito_incluye_nombre_y_stock(self):
        """
        CA3: En la vista por depósito se despliega lista con nombre del producto y su stock por depósito.
        """
        url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_central.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos = response.data['productos']
        
        for producto in productos:
            # Verificar que cada producto tiene los campos requeridos
            self.assertIn('nombre', producto)
            self.assertIn('cantidad', producto)
            
            # Verificar que el nombre no está vacío
            self.assertIsNotNone(producto['nombre'])
            self.assertGreater(len(producto['nombre']), 0)
            
            # Verificar que cantidad es un número
            self.assertIsInstance(producto['cantidad'], int)
            self.assertGreaterEqual(producto['cantidad'], 0)
            
            # Verificar información adicional útil
            self.assertIn('categoria', producto)
            self.assertIn('precio', producto)
            self.assertIn('tiene_stock', producto)
            self.assertIn('stock_bajo', producto)
    
    def test_filtrar_productos_por_deposito(self):
        """
        Verificar que se puede filtrar la vista de productos por depósito específico.
        """
        url = reverse('producto-list-create')
        
        # Filtrar por Depósito Central
        response_central = self.client.get(url, {'deposito': self.deposito_central.id})
        self.assertEqual(response_central.status_code, status.HTTP_200_OK)
        productos_central = [p['nombre'] for p in response_central.data['results']]
        
        # Debe incluir todos los productos que tienen stock en central
        self.assertIn('Agua Mineral 1L', productos_central)
        self.assertIn('Leche Entera 1L', productos_central)
        self.assertIn('Detergente 500ml', productos_central)
        self.assertIn('Yogur Natural 200g', productos_central)
        
        # Filtrar por Depósito Norte
        response_norte = self.client.get(url, {'deposito': self.deposito_norte.id})
        self.assertEqual(response_norte.status_code, status.HTTP_200_OK)
        productos_norte = [p['nombre'] for p in response_norte.data['results']]
        
        # Solo debe incluir productos con stock en norte
        self.assertIn('Agua Mineral 1L', productos_norte)
        self.assertIn('Leche Entera 1L', productos_norte)
        self.assertNotIn('Detergente 500ml', productos_norte)
        self.assertNotIn('Yogur Natural 200g', productos_norte)
        
        # Filtrar por Depósito Sur
        response_sur = self.client.get(url, {'deposito': self.deposito_sur.id})
        self.assertEqual(response_sur.status_code, status.HTTP_200_OK)
        productos_sur = [p['nombre'] for p in response_sur.data['results']]
        
        # Solo debe incluir agua
        self.assertIn('Agua Mineral 1L', productos_sur)
        self.assertNotIn('Leche Entera 1L', productos_sur)
        self.assertNotIn('Detergente 500ml', productos_sur)
        self.assertNotIn('Yogur Natural 200g', productos_sur)
    
    def test_deposito_inexistente(self):
        """
        Verificar manejo de error cuando se consulta un depósito que no existe.
        """
        url = reverse('productos-por-deposito', kwargs={'deposito_id': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_estadisticas_productos_stock_total(self):
        """
        Verificar que las estadísticas incluyen información de stock.
        """
        url = reverse('estadisticas-productos')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        stats = response.data
        
        # Verificar estadísticas básicas
        self.assertIn('total_productos', stats)
        self.assertEqual(stats['total_productos'], 4)
        
        self.assertIn('productos_sin_stock', stats)
        self.assertEqual(stats['productos_sin_stock'], 1)  # Solo yogur
        
        # Verificar stock por categoría
        self.assertIn('stock_por_categoria', stats)
        stock_por_cat = {cat['categoria']: cat for cat in stats['stock_por_categoria']}
        
        self.assertIn('Bebidas', stock_por_cat)
        self.assertEqual(stock_por_cat['Bebidas']['stock_total'], 150)  # Solo agua
        
        self.assertIn('Lácteos', stock_por_cat)
        self.assertEqual(stock_por_cat['Lácteos']['stock_total'], 80)  # Leche: 80, Yogur: 0
        
        self.assertIn('Limpieza', stock_por_cat)
        self.assertEqual(stock_por_cat['Limpieza']['stock_total'], 20)  # Solo detergente
    
    def test_autenticacion_requerida(self):
        """
        Verificar que se requiere autenticación para acceder a las vistas de stock.
        """
        self.client.force_authenticate(user=None)
        
        # Vista de productos
        url_productos = reverse('producto-list-create')
        response = self.client.get(url_productos)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Vista de productos por depósito
        url_deposito = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_central.id})
        response = self.client.get(url_deposito)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Vista de estadísticas
        url_stats = reverse('estadisticas-productos')
        response = self.client.get(url_stats)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StockVisualizationEdgeCasesTestCase(TestCase):
    """Tests para casos edge de visualización de stock"""
    
    def setUp(self):
        """Configuración básica"""
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            email='admin@edge.com',
            username='admin_edge',
            password='StrongPass1!',
            nombre_supermercado='EdgeSuper',
            cuil='20111111111',
            provincia='Buenos Aires',
            localidad='La Plata',
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.categoria = Categoria.objects.create(nombre='Test Category')
        self.deposito = Deposito.objects.create(
            nombre='Test Deposito',
            direccion='Test Address',
            supermercado=self.admin_user
        )
    
    def test_producto_sin_stock_en_ningun_deposito(self):
        """
        Verificar comportamiento con producto que no tiene stock en ningún depósito.
        """
        producto = Producto.objects.create(
            nombre='Producto Sin Stock',
            categoria=self.categoria,
            precio=Decimal('100.00')
        )
        
        # Ver en lista de productos
        url = reverse('producto-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos = response.data['results']
        
        producto_encontrado = next((p for p in productos if p['nombre'] == 'Producto Sin Stock'), None)
        self.assertIsNotNone(producto_encontrado)
        self.assertEqual(producto_encontrado['stock_total'], 0)
        self.assertEqual(producto_encontrado['depositos_count'], 0)
    
    def test_deposito_sin_productos(self):
        """
        Verificar comportamiento con depósito que no tiene productos.
        """
        deposito_vacio = Deposito.objects.create(
            nombre='Depósito Vacío',
            direccion='Sin productos',
            supermercado=self.admin_user
        )
        
        url = reverse('productos-por-deposito', kwargs={'deposito_id': deposito_vacio.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('productos', response.data)
        self.assertEqual(len(response.data['productos']), 0)
        
        deposito_info = response.data['deposito']
        self.assertEqual(deposito_info['nombre'], 'Depósito Vacío')
    
    def test_producto_inactivo_no_aparece_en_deposito(self):
        """
        Verificar que productos inactivos no aparecen en vista por depósito.
        """
        producto_activo = Producto.objects.create(
            nombre='Producto Activo',
            categoria=self.categoria,
            precio=Decimal('100.00'),
            activo=True
        )
        producto_inactivo = Producto.objects.create(
            nombre='Producto Inactivo',
            categoria=self.categoria,
            precio=Decimal('100.00'),
            activo=False
        )
        
        # Crear stock para ambos
        ProductoDeposito.objects.create(
            producto=producto_activo,
            deposito=self.deposito,
            cantidad=10
        )
        ProductoDeposito.objects.create(
            producto=producto_inactivo,
            deposito=self.deposito,
            cantidad=5
        )
        
        url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos = response.data['productos']
        
        nombres = [p['nombre'] for p in productos]
        self.assertIn('Producto Activo', nombres)
        self.assertNotIn('Producto Inactivo', nombres)
    
    def test_stock_con_cantidades_grandes(self):
        """
        Verificar manejo de cantidades de stock grandes.
        """
        producto = Producto.objects.create(
            nombre='Producto Gran Stock',
            categoria=self.categoria,
            precio=Decimal('50.00')
        )
        
        # Stock muy grande
        ProductoDeposito.objects.create(
            producto=producto,
            deposito=self.deposito,
            cantidad=999999,
            cantidad_minima=1000
        )
        
        # Ver detalle del producto
        url = reverse('producto-detail', kwargs={'pk': producto.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stock_total'], 999999)
        
        # Ver por depósito
        url_deposito = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito.id})
        response = self.client.get(url_deposito)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos = response.data['productos']
        
        producto_encontrado = next((p for p in productos if p['nombre'] == 'Producto Gran Stock'), None)
        self.assertIsNotNone(producto_encontrado)
        self.assertEqual(producto_encontrado['cantidad'], 999999)
        self.assertTrue(producto_encontrado['tiene_stock'])
        self.assertFalse(producto_encontrado['stock_bajo'])  # 999999 > 1000


class StockVisualizationSecurityTestCase(TestCase):
    """Tests de seguridad para visualización de stock"""
    
    def setUp(self):
        """Configuración para tests de seguridad"""
        self.client = APIClient()
        
        # Crear dos usuarios diferentes
        self.admin_user1 = User.objects.create_user(
            email='admin1@security.com',
            username='admin_security1',
            password='StrongPass1!',
            nombre_supermercado='Super Security 1',
            cuil='20111111111',
            provincia='Buenos Aires',
            localidad='La Plata',
        )
        
        self.admin_user2 = User.objects.create_user(
            email='admin2@security.com',
            username='admin_security2',
            password='StrongPass1!',
            nombre_supermercado='Super Security 2',
            cuil='20222222222',
            provincia='Buenos Aires',
            localidad='La Plata',
        )
        
        # Crear depósitos para cada usuario
        self.deposito_user1 = Deposito.objects.create(
            nombre='Depósito User 1',
            direccion='Direccion User 1',
            supermercado=self.admin_user1
        )
        
        self.deposito_user2 = Deposito.objects.create(
            nombre='Depósito User 2',
            direccion='Direccion User 2',
            supermercado=self.admin_user2
        )
        
        # Crear categoría y producto
        self.categoria = Categoria.objects.create(nombre='Security Test')
        self.producto = Producto.objects.create(
            nombre='Producto Security',
            categoria=self.categoria,
            precio=Decimal('100.00')
        )
        
        # Crear stock en depósito del user2
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito_user2,
            cantidad=50,
            cantidad_minima=10
        )
    
    def test_acceso_solo_depositos_propios(self):
        """
        NOTA: Este test identifica una vulnerabilidad de seguridad potencial.
        El administrador debe poder ver SOLO los depósitos de su propio supermercado.
        
        COMPORTAMIENTO ESPERADO: 404 cuando se intenta acceder a depósito ajeno
        IMPLEMENTACIÓN ACTUAL: Puede que permita acceso (vulnerabilidad)
        """
        # Autenticar como user1
        self.client.force_authenticate(user=self.admin_user1)
        
        # Intentar acceder al depósito del user2
        url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_user2.id})
        response = self.client.get(url)
        
        # COMPORTAMIENTO ESPERADO: Debe devolver 404
        # Si devuelve 200, hay una vulnerabilidad de seguridad
        if response.status_code == status.HTTP_200_OK:
            self.fail(
                "VULNERABILIDAD DE SEGURIDAD DETECTADA: "
                "El usuario puede acceder a depósitos de otros supermercados. "
                "Se requiere corrección en la vista productos_por_deposito para "
                "filtrar por supermercado=request.user"
            )
        else:
            # Comportamiento esperado - seguridad correcta
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_listado_productos_solo_muestra_stock_propio(self):
        """
        Verificar que en el listado de productos, el stock mostrado corresponde
        solo a los depósitos del usuario autenticado.
        """
        # Crear stock en depósito del user1 también
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito_user1,
            cantidad=30,
            cantidad_minima=5
        )
        
        # Autenticar como user1
        self.client.force_authenticate(user=self.admin_user1)
        
        url = reverse('producto-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos = response.data['results']
        
        producto_encontrado = next((p for p in productos if p['nombre'] == 'Producto Security'), None)
        self.assertIsNotNone(producto_encontrado)
        
        # El stock_total debe ser solo el del user1 (30), no el total global (80)
        # NOTA: Si muestra 80, significa que está calculando stock de todos los supermercados
        if producto_encontrado['stock_total'] != 30:
            self.fail(
                f"POSIBLE VULNERABILIDAD: El stock_total muestra {producto_encontrado['stock_total']} "
                f"pero debería mostrar solo 30 (del propio supermercado). "
                "Verificar que el cálculo de stock se filtre por supermercado."
            )


class StockVisualizationIntegrationTestCase(TestCase):
    """Tests de integración para visualización de stock"""
    
    def setUp(self):
        """Configuración para tests de integración"""
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            email='admin@integration.com',
            username='admin_integration',
            password='StrongPass1!',
            nombre_supermercado='Integration Super',
            cuil='20333333333',
            provincia='Buenos Aires',
            localidad='La Plata',
        )
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear datos completos para testing integral
        self.categoria1 = Categoria.objects.create(nombre='Categoría 1')
        self.categoria2 = Categoria.objects.create(nombre='Categoría 2')
        
        self.deposito1 = Deposito.objects.create(
            nombre='Depósito 1', direccion='Dir 1', supermercado=self.admin_user
        )
        self.deposito2 = Deposito.objects.create(
            nombre='Depósito 2', direccion='Dir 2', supermercado=self.admin_user
        )
        
        # Productos con diferentes patrones de stock
        self.producto_multi_deposito = Producto.objects.create(
            nombre='Multi Depósito', categoria=self.categoria1, precio=Decimal('100.00')
        )
        self.producto_un_deposito = Producto.objects.create(
            nombre='Un Depósito', categoria=self.categoria1, precio=Decimal('200.00')
        )
        self.producto_sin_stock = Producto.objects.create(
            nombre='Sin Stock', categoria=self.categoria2, precio=Decimal('300.00')
        )
        
        # Stocks
        ProductoDeposito.objects.create(
            producto=self.producto_multi_deposito, deposito=self.deposito1, cantidad=100
        )
        ProductoDeposito.objects.create(
            producto=self.producto_multi_deposito, deposito=self.deposito2, cantidad=50
        )
        ProductoDeposito.objects.create(
            producto=self.producto_un_deposito, deposito=self.deposito1, cantidad=25
        )
        ProductoDeposito.objects.create(
            producto=self.producto_sin_stock, deposito=self.deposito1, cantidad=0
        )
    
    def test_flujo_completo_visualizacion_stock(self):
        """
        Test de integración que simula el flujo completo de un administrador
        consultando stock desde diferentes vistas.
        """
        # 1. Ver lista general de productos
        url_productos = reverse('producto-list-create')
        response = self.client.get(url_productos)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos = response.data['results']
        self.assertEqual(len(productos), 3)
        
        # Verificar stocks calculados correctamente
        productos_dict = {p['nombre']: p for p in productos}
        self.assertEqual(productos_dict['Multi Depósito']['stock_total'], 150)  # 100 + 50
        self.assertEqual(productos_dict['Un Depósito']['stock_total'], 25)
        self.assertEqual(productos_dict['Sin Stock']['stock_total'], 0)
        
        # 2. Ver detalle de producto específico
        url_detalle = reverse('producto-detail', kwargs={'pk': self.producto_multi_deposito.id})
        response = self.client.get(url_detalle)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        detalle = response.data
        self.assertEqual(detalle['stock_total'], 150)
        self.assertEqual(len(detalle['stocks']), 2)  # En 2 depósitos
        
        # 3. Ver stock por depósito 1
        url_dep1 = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito1.id})
        response = self.client.get(url_dep1)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos_dep1 = {p['nombre']: p for p in response.data['productos']}
        
        self.assertEqual(productos_dep1['Multi Depósito']['cantidad'], 100)
        self.assertEqual(productos_dep1['Un Depósito']['cantidad'], 25)
        self.assertEqual(productos_dep1['Sin Stock']['cantidad'], 0)
        
        # 4. Ver stock por depósito 2
        url_dep2 = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito2.id})
        response = self.client.get(url_dep2)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        productos_dep2 = response.data['productos']
        
        # Solo debe tener 1 producto (Multi Depósito)
        self.assertEqual(len(productos_dep2), 1)
        self.assertEqual(productos_dep2[0]['nombre'], 'Multi Depósito')
        self.assertEqual(productos_dep2[0]['cantidad'], 50)
        
        # 5. Ver estadísticas generales
        url_stats = reverse('estadisticas-productos')
        response = self.client.get(url_stats)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.data
        
        self.assertEqual(stats['total_productos'], 3)
        self.assertEqual(stats['productos_sin_stock'], 1)  # Solo "Sin Stock"
        
        stock_por_cat = {cat['categoria']: cat for cat in stats['stock_por_categoria']}
        self.assertEqual(stock_por_cat['Categoría 1']['stock_total'], 175)  # 150 + 25
        self.assertEqual(stock_por_cat['Categoría 2']['stock_total'], 0)    # Sin stock