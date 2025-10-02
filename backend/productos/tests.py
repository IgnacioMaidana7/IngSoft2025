from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from productos.models import Categoria, Producto, ProductoDeposito
from inventario.models import Deposito


class ProductosABMTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()
		self.user = User.objects.create_user(
			email='admin@example.com',
			username='admin',
			password='StrongPass1!',
			nombre_supermercado='Mi Super',
			cuil='20123456789',
			provincia='Buenos Aires',
			localidad='La Plata',
		)
		self.client.force_authenticate(user=self.user)

		# Datos base
		self.cat_bebidas = Categoria.objects.create(nombre='Bebidas')
		self.cat_limpieza = Categoria.objects.create(nombre='Limpieza')
		self.deposito = Deposito.objects.create(
			nombre='Depósito Central', direccion='Calle 123', supermercado=self.user
		)

		# URLs
		self.url_productos = reverse('producto-list-create')
		self.url_categorias_disponibles = reverse('categorias-disponibles')

	def test_crear_producto_exitoso(self):
		payload = {
			'nombre': 'Agua Mineral',
			'categoria': self.cat_bebidas.id,
			'precio': '150.50',
			'deposito_id': self.deposito.id,
			'cantidad_inicial': 25,
			'cantidad_minima': 5,
		}
		resp = self.client.post(self.url_productos, data=payload, format='json')
		self.assertEqual(resp.status_code, 201, resp.data)
		prod_id = resp.data.get('id')
		self.assertIsNotNone(prod_id)

		# Verificar existencia en DB y stock en depósito
		prod = Producto.objects.get(id=prod_id)
		self.assertEqual(prod.nombre, 'Agua Mineral')
		stock = ProductoDeposito.objects.get(producto=prod, deposito=self.deposito)
		self.assertEqual(stock.cantidad, 25)

	def test_validacion_campos_obligatorios(self):
		# Faltan nombre/categoria/precio
		payload = {
			'deposito_id': self.deposito.id,
			'cantidad_inicial': 10,
		}
		resp = self.client.post(self.url_productos, data=payload, format='json')
		self.assertEqual(resp.status_code, 400)
		self.assertTrue(any(k in resp.data for k in ['nombre', 'categoria', 'precio']))

	def test_asignar_categoria_en_creacion_y_edicion(self):
		# Crear con una categoría
		resp = self.client.post(self.url_productos, data={
			'nombre': 'Detergente',
			'categoria': self.cat_limpieza.id,
			'precio': '200.00',
		}, format='json')
		self.assertEqual(resp.status_code, 201, resp.data)
		prod_id = resp.data['id']

		# Editar cambiando categoría
		url_detail = reverse('producto-detail', kwargs={'pk': prod_id})
		resp2 = self.client.patch(url_detail, data={
			'categoria': self.cat_bebidas.id,
		}, format='json')
		self.assertIn(resp2.status_code, [200, 202, 204])
		self.assertEqual(Producto.objects.get(id=prod_id).categoria_id, self.cat_bebidas.id)

	def test_listar_categorias_desplegable(self):
		resp = self.client.get(self.url_categorias_disponibles)
		self.assertEqual(resp.status_code, 200)
		self.assertIsInstance(resp.data, list)
		self.assertTrue(any(c['nombre'] == 'Bebidas' for c in resp.data))

	def test_listar_productos_registrados_y_filtrar(self):
		# Crear dos productos
		p1 = Producto.objects.create(nombre='Jugo', categoria=self.cat_bebidas, precio=300)
		p2 = Producto.objects.create(nombre='Lavandina', categoria=self.cat_limpieza, precio=250)
		ProductoDeposito.objects.create(producto=p1, deposito=self.deposito, cantidad=7)

		# Listado general
		resp = self.client.get(self.url_productos)
		self.assertEqual(resp.status_code, 200)
		# Paginado: results
		self.assertIn('results', resp.data)
		nombres = [r['nombre'] for r in resp.data['results']]
		self.assertIn('Jugo', nombres)
		self.assertIn('Lavandina', nombres)

		# Filtro por categoría
		resp_cat = self.client.get(self.url_productos, {'categoria': self.cat_bebidas.id})
		self.assertEqual(resp_cat.status_code, 200)
		self.assertTrue(all(r['categoria_nombre'] == 'Bebidas' for r in resp_cat.data['results']))

		# Filtro por depósito
		resp_dep = self.client.get(self.url_productos, {'deposito': self.deposito.id})
		self.assertEqual(resp_dep.status_code, 200)
		# Debe incluir al menos Jugo
		nombres_dep = [r['nombre'] for r in resp_dep.data['results']]
		self.assertIn('Jugo', nombres_dep)

	def test_ver_productos_por_deposito(self):
		p = Producto.objects.create(nombre='Soda', categoria=self.cat_bebidas, precio=180)
		ProductoDeposito.objects.create(producto=p, deposito=self.deposito, cantidad=12)

		url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito.id})
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertIn('productos', resp.data)
		item = next((x for x in resp.data['productos'] if x['nombre'] == 'Soda'), None)
		self.assertIsNotNone(item)
		self.assertEqual(item['cantidad'], 12)

	def test_modificar_datos_y_stock_de_producto(self):
		# Crear producto
		resp = self.client.post(self.url_productos, data={
			'nombre': 'Cerveza',
			'categoria': self.cat_bebidas.id,
			'precio': '500.00',
		}, format='json')
		self.assertEqual(resp.status_code, 201, resp.data)
		prod_id = resp.data['id']
		url_detail = reverse('producto-detail', kwargs={'pk': prod_id})

		# Actualizar precio y stock en el depósito seleccionado
		resp2 = self.client.put(url_detail, data={
			'nombre': 'Cerveza',
			'categoria': self.cat_bebidas.id,
			'precio': '550.00',
			'deposito_id': self.deposito.id,
			'cantidad_inicial': 9,
			'cantidad_minima': 3,
		}, format='json')
		self.assertIn(resp2.status_code, [200, 202])
		# Verificar stock
		stock = ProductoDeposito.objects.get(producto_id=prod_id, deposito=self.deposito)
		self.assertEqual(stock.cantidad, 9)

	def test_eliminar_producto_con_y_sin_stock(self):
		# Con stock > 0 → 400
		p1 = Producto.objects.create(nombre='Aceite', categoria=self.cat_bebidas, precio=800)
		ProductoDeposito.objects.create(producto=p1, deposito=self.deposito, cantidad=2)
		url1 = reverse('producto-detail', kwargs={'pk': p1.id})
		resp1 = self.client.delete(url1)
		self.assertEqual(resp1.status_code, 400)

		# Sin stock → 204 (soft delete: activo=False)
		p2 = Producto.objects.create(nombre='Sal', categoria=self.cat_limpieza, precio=100)
		url2 = reverse('producto-detail', kwargs={'pk': p2.id})
		resp2 = self.client.delete(url2)
		self.assertEqual(resp2.status_code, 204)
		p2.refresh_from_db()
		self.assertFalse(p2.activo)


# ==========================================
# TESTS PARA HISTORIA DE USUARIO: 
# "Como administrador quiero visualizar el stock total y de cada depósito"
# ==========================================

from rest_framework import status
from decimal import Decimal


class StockVisualizationTestCase(TestCase):
	"""Tests para visualización de stock total y por depósito - HU Stock"""
	
	def setUp(self):
		"""Configuración inicial para los tests de visualización de stock"""
		self.client = APIClient()
		
		# Crear usuario administrador
		User = get_user_model()
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
		
		# Crear productos con stocks estratégicos
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


class StockVisualizationSecurityTestCase(TestCase):
	"""Tests de seguridad para visualización de stock - HU Stock"""
	
	def setUp(self):
		"""Configuración para tests de seguridad"""
		self.client = APIClient()
		User = get_user_model()
		
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
	
	def test_administrador_puede_ver_todos_los_depositos(self):
		"""
		COMPORTAMIENTO CORRECTO: El administrador único puede ver todos los depósitos.
		
		Como solo hay un administrador en el sistema, debe poder acceder a 
		cualquier depósito para gestionar el stock completo del negocio.
		"""
		# Autenticar como user1
		self.client.force_authenticate(user=self.admin_user1)
		
		# Debe poder acceder al depósito del user2 (comportamiento correcto)
		url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_user2.id})
		response = self.client.get(url)
		
		# COMPORTAMIENTO ESPERADO: Debe devolver 200 (acceso permitido)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		
		# Verificar que obtiene información del depósito
		self.assertIn('deposito', response.data)
		self.assertIn('productos', response.data)
		
		deposito_info = response.data['deposito']
		self.assertEqual(deposito_info['nombre'], 'Depósito User 2')
		
		# Verificar que puede ver los productos del depósito
		productos = response.data['productos']
		if len(productos) > 0:
			producto = productos[0]
			self.assertIn('nombre', producto)
			self.assertIn('cantidad', producto)
			self.assertEqual(producto['nombre'], 'Producto Security')
	
	def test_acceso_con_usuario_autenticado(self):
		"""
		COMPORTAMIENTO ACTUAL: Cualquier usuario autenticado puede acceder.
		
		En el sistema solo habrá un administrador único, por lo que la 
		autenticación básica es suficiente. No se requieren permisos especiales
		adicionales para las vistas de stock.
		"""
		# Crear usuario adicional para simular múltiples usuarios
		User = get_user_model()
		usuario_adicional = User.objects.create_user(
			username='usuario_adicional',
			email='adicional@test.com',
			password='testpass123',
			nombre_supermercado='Supermercado Adicional',
			cuil='20333333333',
			provincia='Buenos Aires',
			localidad='La Plata'
		)
		
		self.client.force_authenticate(user=usuario_adicional)
		
		# Con autenticación válida, debe poder acceder (comportamiento actual)
		url = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_user1.id})
		response = self.client.get(url)
		
		# COMPORTAMIENTO ACTUAL: Cualquier usuario autenticado puede acceder
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		
		# Verificar que obtiene datos válidos
		self.assertIn('deposito', response.data)
		self.assertIn('productos', response.data)
	
	def test_autenticacion_requerida_stock_views(self):
		"""
		Verificar que se requiere autenticación para acceder a las vistas de stock.
		"""
		self.client.force_authenticate(user=None)
		
		# Vista de productos
		url_productos = reverse('producto-list-create')
		response = self.client.get(url_productos)
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
		
		# Vista de productos por depósito
		url_deposito = reverse('productos-por-deposito', kwargs={'deposito_id': self.deposito_user1.id})
		response = self.client.get(url_deposito)
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
		
		# Vista de estadísticas
		url_stats = reverse('estadisticas-productos')
		response = self.client.get(url_stats)
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

