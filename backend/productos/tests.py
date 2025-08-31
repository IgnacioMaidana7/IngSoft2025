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

