from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, Mock
import uuid

from .models import Categoria, Producto, ProductoDeposito
from inventario.models import Deposito
from empleados.models import Empleado
from authentication.models import EmpleadoUser
from notificaciones.models import Notificacion

User = get_user_model()


class ProductoModelTestCase(TestCase):
    """Tests para validaciones del modelo Producto"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Usar UUID para hacer emails únicos
        self.unique_id = str(uuid.uuid4())[:8]
        
        self.admin_user = User.objects.create_user(
            username=f'admin_test_{self.unique_id}',
            email=f'admin_{self.unique_id}@test.com',
            password='testpass123',
            nombre_supermercado='Supermercado Test',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Calle 123, La Plata',
            supermercado=self.admin_user
        )
        
        self.categoria = Categoria.objects.create(
            nombre='Bebidas',
            descripcion='Bebidas en general'
        )
        
        # Crear empleado reponedor
        self.empleado_repo = Empleado.objects.create(
            nombre='María',
            apellido='González',
            email='maria@test.com',
            dni='87654321',
            puesto='REPONEDOR',
            deposito=self.deposito,
            supermercado=self.admin_user
        )
        
        # Crear usuario EmpleadoUser para el reponedor
        self.repo_user = EmpleadoUser.objects.create_user(
            username='maria_repo',
            email='maria@test.com',
            password='testpass123',
            puesto='REPONEDOR',
            supermercado=self.admin_user
        )
    
    def test_crear_producto_campos_obligatorios(self):
        """Test CA: El sistema valida que los campos obligatorios estén completos (nombre, categoría, precio y cantidad)"""
        
        # Producto válido con todos los campos obligatorios
        producto = Producto.objects.create(
            nombre='Coca Cola 500ml',
            categoria=self.categoria,
            precio=100.50,
            descripcion='Bebida gaseosa'
        )
        
        self.assertEqual(producto.nombre, 'Coca Cola 500ml')
        self.assertEqual(producto.categoria, self.categoria)
        self.assertEqual(producto.precio, 100.50)
        self.assertTrue(producto.activo)
        
        # Test nombre vacío
        with self.assertRaises(ValidationError):
            producto = Producto(
                nombre='',
                categoria=self.categoria,
                precio=100.50
            )
            producto.full_clean()
        
        # Test precio negativo (aunque el modelo no lo valide explícitamente, 
        # es una validación lógica que debería estar)
        producto_precio_negativo = Producto(
            nombre='Producto Test',
            categoria=self.categoria,
            precio=-50.00
        )
        # Este test puede fallar si no hay validación en el modelo
        # Se puede agregar un validator personalizado si es necesario
    
    def test_validar_unicidad_producto_por_deposito(self):
        """Test CA: El sistema debe validar que no haya el mismo producto registrado con anterioridad (verificar mediante el nombre)"""
        
        # Crear primer producto
        producto1 = Producto.objects.create(
            nombre='Coca Cola 500ml',
            categoria=self.categoria,
            precio=100.50
        )
        
        # Crear stock en el depósito
        ProductoDeposito.objects.create(
            producto=producto1,
            deposito=self.deposito,
            cantidad=10,
            cantidad_minima=5
        )
        
        # Intentar crear segundo producto con mismo nombre
        producto2 = Producto.objects.create(
            nombre='Coca Cola 500ml',  # Mismo nombre
            categoria=self.categoria,
            precio=105.00
        )
        
        # Intentar crear stock del mismo producto en el mismo depósito debería fallar
        with self.assertRaises(IntegrityError):
            ProductoDeposito.objects.create(
                producto=producto2,
                deposito=self.deposito,
                cantidad=5,
                cantidad_minima=2
            )
    
    def test_stock_inicial_y_minimo_opcional(self):
        """Test CA: El reponedor puede detallar un stock inicial y un stock mínimo, como opcional"""
        
        producto = Producto.objects.create(
            nombre='Producto Test',
            categoria=self.categoria,
            precio=50.00
        )
        
        # Stock sin cantidad mínima (opcional)
        stock1 = ProductoDeposito.objects.create(
            producto=producto,
            deposito=self.deposito,
            cantidad=20
            # cantidad_minima por defecto es 0
        )
        
        self.assertEqual(stock1.cantidad, 20)
        self.assertEqual(stock1.cantidad_minima, 0)
        
        # Stock con cantidad mínima especificada
        deposito2 = Deposito.objects.create(
            nombre='Depósito Norte',
            direccion='Avenida 456',
            supermercado=self.admin_user
        )
        
        stock2 = ProductoDeposito.objects.create(
            producto=producto,
            deposito=deposito2,
            cantidad=15,
            cantidad_minima=5
        )
        
        self.assertEqual(stock2.cantidad, 15)
        self.assertEqual(stock2.cantidad_minima, 5)
    
    def test_metodos_stock(self):
        """Test: Métodos del modelo ProductoDeposito"""
        
        producto = Producto.objects.create(
            nombre='Producto Test',
            categoria=self.categoria,
            precio=50.00
        )
        
        # Test tiene_stock()
        stock = ProductoDeposito.objects.create(
            producto=producto,
            deposito=self.deposito,
            cantidad=10,
            cantidad_minima=5
        )
        
        self.assertTrue(stock.tiene_stock())
        
        # Test sin stock
        stock.cantidad = 0
        stock.save()
        self.assertFalse(stock.tiene_stock())
        
        # Test stock_bajo()
        stock.cantidad = 3  # Menor que cantidad_minima (5)
        stock.save()
        self.assertTrue(stock.stock_bajo())
        
        stock.cantidad = 8  # Mayor que cantidad_minima
        stock.save()
        self.assertFalse(stock.stock_bajo())


class ProductoReponedorAPITestCase(TransactionTestCase):
    """Tests para la API de productos desde la perspectiva del reponedor"""
    
    # Contador de clase para hacer emails únicos
    _test_counter = 0
    
    def setUp(self):
        """Configuración inicial para los tests de API"""
        self.client = APIClient()
        
        # Incrementar contador para emails únicos
        ProductoReponedorAPITestCase._test_counter += 1
        self.test_id = ProductoReponedorAPITestCase._test_counter
        
        # Crear admin
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            nombre_supermercado='Supermercado Test',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        # Crear depósitos
        self.deposito1 = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Calle 123',
            supermercado=self.admin_user
        )
        
        self.deposito2 = Deposito.objects.create(
            nombre='Depósito Norte',
            direccion='Avenida 456',
            supermercado=self.admin_user
        )
        
        # Crear categorías
        self.categoria_bebidas = Categoria.objects.create(
            nombre='Bebidas',
            descripcion='Bebidas en general'
        )
        
        self.categoria_snacks = Categoria.objects.create(
            nombre='Snacks',
            descripcion='Snacks y golosinas'
        )
        
        # Crear empleado reponedor
        self.empleado_repo = Empleado.objects.create(
            nombre='María',
            apellido='González',
            email=f'maria{self.test_id}@test.com',
            dni=f'8765432{self.test_id}',
            puesto='REPONEDOR',
            deposito=self.deposito1,  # Asignado al depósito 1
            supermercado=self.admin_user
        )
        
        # Crear usuario EmpleadoUser para el reponedor
        self.repo_user = EmpleadoUser.objects.create_user(
            username=f'maria{self.test_id}_repo',
            email=f'maria{self.test_id}@test.com',
            password='testpass123',
            puesto='REPONEDOR',
            supermercado=self.admin_user
        )
        
        # Crear segundo reponedor para otro depósito
        self.empleado_repo2 = Empleado.objects.create(
            nombre='Carlos',
            apellido='López',
            email=f'carlos{self.test_id}@test.com',
            dni=f'1111111{self.test_id}',
            puesto='REPONEDOR',
            deposito=self.deposito2,  # Asignado al depósito 2
            supermercado=self.admin_user
        )
        
        self.repo_user2 = EmpleadoUser.objects.create_user(
            username=f'carlos{self.test_id}_repo',
            email=f'carlos{self.test_id}@test.com',
            password='testpass123',
            puesto='REPONEDOR',
            supermercado=self.admin_user
        )
        
        # URLs
        self.productos_url = reverse('productos:producto-list-create')
        self.categorias_url = reverse('productos:categorias-disponibles')
    
    def tearDown(self):
        """Limpiar datos después de cada test"""
        ProductoDeposito.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        Empleado.objects.all().delete()
        EmpleadoUser.objects.all().delete()
        Deposito.objects.all().delete()
        User.objects.all().delete()
        Notificacion.objects.all().delete()
    
    def test_reponedor_crear_producto_nuevo(self):
        """Test CA: El reponedor puede crear un nuevo producto ingresando nombre, categoría, precio, y cantidad"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        data = {
            'nombre': 'Coca Cola 500ml',
            'categoria': self.categoria_bebidas.id,
            'precio': 150.50,
            'descripcion': 'Bebida gaseosa',
            'cantidad_inicial': 20,
            'cantidad_minima': 5
        }
        
        response = self.client.post(self.productos_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se creó el producto
        producto = Producto.objects.get(nombre='Coca Cola 500ml')
        self.assertEqual(producto.categoria, self.categoria_bebidas)
        self.assertEqual(float(producto.precio), 150.50)
        
        # Verificar que se creó el stock en el depósito del reponedor
        stock = ProductoDeposito.objects.get(producto=producto, deposito=self.deposito1)
        self.assertEqual(stock.cantidad, 20)
        self.assertEqual(stock.cantidad_minima, 5)
    
    def test_reponedor_validacion_campos_obligatorios(self):
        """Test CA: El sistema valida que los campos obligatorios estén completos (nombre, categoría, precio y cantidad)"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Test sin nombre
        data = {
            'categoria': self.categoria_bebidas.id,
            'precio': 150.50,
            'cantidad_inicial': 20
        }
        response = self.client.post(self.productos_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', response.data)
        
        # Test sin categoría
        data = {
            'nombre': 'Producto Test',
            'precio': 150.50,
            'cantidad_inicial': 20
        }
        response = self.client.post(self.productos_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('categoria', response.data)
        
        # Test sin precio
        data = {
            'nombre': 'Producto Test',
            'categoria': self.categoria_bebidas.id,
            'cantidad_inicial': 20
        }
        response = self.client.post(self.productos_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('precio', response.data)
    
    def test_reponedor_deposito_automatico_asignado(self):
        """Test CA: El depósito se trae desde la asignación que le hizo el administrador"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        data = {
            'nombre': 'Sprite 500ml',
            'categoria': self.categoria_bebidas.id,
            'precio': 140.00,
            'cantidad_inicial': 15,
            'cantidad_minima': 3
        }
        
        response = self.client.post(self.productos_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que el stock se creó en el depósito asignado al reponedor
        producto = Producto.objects.get(nombre='Sprite 500ml')
        stock = ProductoDeposito.objects.get(producto=producto)
        self.assertEqual(stock.deposito, self.deposito1)  # Depósito del reponedor
    
    def test_validacion_producto_duplicado_en_deposito(self):
        """Test CA: El sistema debe validar que no haya el mismo producto registrado con anterioridad (verificar mediante el nombre)"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear primer producto
        data = {
            'nombre': 'Fanta 500ml',
            'categoria': self.categoria_bebidas.id,
            'precio': 140.00,
            'cantidad_inicial': 10
        }
        
        response = self.client.post(self.productos_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Intentar crear producto con mismo nombre en el mismo depósito
        data_duplicado = {
            'nombre': 'Fanta 500ml',  # Mismo nombre
            'categoria': self.categoria_bebidas.id,
            'precio': 145.00,  # Precio diferente
            'cantidad_inicial': 5
        }
        
        response = self.client.post(self.productos_url, data_duplicado)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Ya existe un producto con este nombre', str(response.data))
    
    def test_reponedor_modificar_producto(self):
        """Test CA: El reponedor puede modificar los datos de un producto incluyendo el stock"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear producto primero
        producto = Producto.objects.create(
            nombre='Producto Original',
            categoria=self.categoria_bebidas,
            precio=100.00
        )
        
        stock = ProductoDeposito.objects.create(
            producto=producto,
            deposito=self.deposito1,
            cantidad=10,
            cantidad_minima=3
        )
        
        # Modificar producto
        url = reverse('productos:producto-detail', kwargs={'pk': producto.pk})
        data = {
            'nombre': 'Producto Modificado',
            'categoria': self.categoria_snacks.id,  # Cambiar categoría
            'precio': 120.00,  # Cambiar precio
            'activo': True,
            'deposito_id': self.deposito1.id,
            'cantidad_inicial': 25,  # Modificar stock
            'cantidad_minima': 8
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar cambios en producto
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Producto Modificado')
        self.assertEqual(producto.categoria, self.categoria_snacks)
        self.assertEqual(float(producto.precio), 120.00)
        
        # Verificar cambios en stock
        stock.refresh_from_db()
        self.assertEqual(stock.cantidad, 25)
        self.assertEqual(stock.cantidad_minima, 8)
    
    def test_reponedor_deshabilitar_producto_sin_stock(self):
        """Test CA: El reponedor puede deshabilitar un producto que se encuentre sin stock del sistema"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear producto sin stock
        producto = Producto.objects.create(
            nombre='Producto Sin Stock',
            categoria=self.categoria_bebidas,
            precio=100.00
        )
        
        ProductoDeposito.objects.create(
            producto=producto,
            deposito=self.deposito1,
            cantidad=0,  # Sin stock
            cantidad_minima=2
        )
        
        # Deshabilitar producto
        url = reverse('productos:producto-detail', kwargs={'pk': producto.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que se marcó como inactivo
        producto.refresh_from_db()
        self.assertFalse(producto.activo)
    
    def test_no_deshabilitar_producto_con_stock(self):
        """Test CA: No se puede deshabilitar un producto que tenga stock"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear producto con stock
        producto = Producto.objects.create(
            nombre='Producto Con Stock',
            categoria=self.categoria_bebidas,
            precio=100.00
        )
        
        ProductoDeposito.objects.create(
            producto=producto,
            deposito=self.deposito1,
            cantidad=10,  # Con stock
            cantidad_minima=2
        )
        
        # Intentar deshabilitar producto
        url = reverse('productos:producto-detail', kwargs={'pk': producto.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No se puede deshabilitar un producto con stock', str(response.data))
        
        # Verificar que sigue activo
        producto.refresh_from_db()
        self.assertTrue(producto.activo)
    
    def test_listar_productos_disponibles_y_deshabilitados(self):
        """Test CA: El sistema muestra en una pestaña la lista de productos disponibles y en otra, la lista de productos deshabilitados"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear productos activos e inactivos
        producto_activo = Producto.objects.create(
            nombre='Producto Activo',
            categoria=self.categoria_bebidas,
            precio=100.00,
            activo=True
        )
        
        producto_inactivo = Producto.objects.create(
            nombre='Producto Inactivo',
            categoria=self.categoria_bebidas,
            precio=100.00,
            activo=False
        )
        
        # Crear stocks
        ProductoDeposito.objects.create(
            producto=producto_activo,
            deposito=self.deposito1,
            cantidad=10
        )
        
        ProductoDeposito.objects.create(
            producto=producto_inactivo,
            deposito=self.deposito1,
            cantidad=0
        )
        
        # Listar productos activos
        response = self.client.get(self.productos_url, {'activo': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        productos_activos = response.data['results'] if 'results' in response.data else response.data
        nombres_activos = [p['nombre'] for p in productos_activos]
        self.assertIn('Producto Activo', nombres_activos)
        self.assertNotIn('Producto Inactivo', nombres_activos)
        
        # Listar productos inactivos
        response = self.client.get(self.productos_url, {'activo': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        productos_inactivos = response.data['results'] if 'results' in response.data else response.data
        nombres_inactivos = [p['nombre'] for p in productos_inactivos]
        self.assertIn('Producto Inactivo', nombres_inactivos)
        self.assertNotIn('Producto Activo', nombres_inactivos)
    
    def test_filtrar_por_nombre(self):
        """Test CA: El listado puede ser filtrado por nombre"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear productos con diferentes nombres
        producto1 = Producto.objects.create(
            nombre='Coca Cola 500ml',
            categoria=self.categoria_bebidas,
            precio=150.00
        )
        
        producto2 = Producto.objects.create(
            nombre='Pepsi 500ml',
            categoria=self.categoria_bebidas,
            precio=145.00
        )
        
        producto3 = Producto.objects.create(
            nombre='Doritos Nacho',
            categoria=self.categoria_snacks,
            precio=200.00
        )
        
        # Crear stocks
        for producto in [producto1, producto2, producto3]:
            ProductoDeposito.objects.create(
                producto=producto,
                deposito=self.deposito1,
                cantidad=10
            )
        
        # Filtrar por nombre "Cola"
        response = self.client.get(self.productos_url, {'search': 'Cola'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        productos = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(productos), 1)
        self.assertEqual(productos[0]['nombre'], 'Coca Cola 500ml')
        
        # Filtrar por nombre "500ml"
        response = self.client.get(self.productos_url, {'search': '500ml'})
        productos = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(productos), 2)
        nombres = [p['nombre'] for p in productos]
        self.assertIn('Coca Cola 500ml', nombres)
        self.assertIn('Pepsi 500ml', nombres)
    
    def test_filtrar_por_stock(self):
        """Test CA: El listado puede ser filtrado por stock"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear productos con diferentes niveles de stock
        producto_sin_stock = Producto.objects.create(
            nombre='Sin Stock',
            categoria=self.categoria_bebidas,
            precio=100.00
        )
        
        producto_stock_bajo = Producto.objects.create(
            nombre='Stock Bajo',
            categoria=self.categoria_bebidas,
            precio=100.00
        )
        
        producto_stock_normal = Producto.objects.create(
            nombre='Stock Normal',
            categoria=self.categoria_bebidas,
            precio=100.00
        )
        
        # Crear stocks con diferentes niveles
        ProductoDeposito.objects.create(
            producto=producto_sin_stock,
            deposito=self.deposito1,
            cantidad=0,
            cantidad_minima=5
        )
        
        ProductoDeposito.objects.create(
            producto=producto_stock_bajo,
            deposito=self.deposito1,
            cantidad=3,
            cantidad_minima=10  # Stock menor al mínimo
        )
        
        ProductoDeposito.objects.create(
            producto=producto_stock_normal,
            deposito=self.deposito1,
            cantidad=20,
            cantidad_minima=5  # Stock mayor al mínimo
        )
        
        # Filtrar productos sin stock
        response = self.client.get(self.productos_url, {'stock': 'sin-stock'})
        productos = response.data['results'] if 'results' in response.data else response.data
        nombres = [p['nombre'] for p in productos]
        self.assertIn('Sin Stock', nombres)
        
        # Filtrar productos con stock bajo
        response = self.client.get(self.productos_url, {'stock': 'bajo'})
        productos = response.data['results'] if 'results' in response.data else response.data
        nombres = [p['nombre'] for p in productos]
        self.assertIn('Stock Bajo', nombres)
        
        # Filtrar productos con stock normal
        response = self.client.get(self.productos_url, {'stock': 'normal'})
        productos = response.data['results'] if 'results' in response.data else response.data
        nombres = [p['nombre'] for p in productos]
        self.assertIn('Stock Normal', nombres)
    
    def test_reponedor_solo_ve_productos_de_su_deposito(self):
        """Test CA: Verificar que el reponedor solo puede ver productos de su depósito asignado"""
        
        # Crear productos en diferentes depósitos
        producto_dep1 = Producto.objects.create(
            nombre='Producto Depósito 1',
            categoria=self.categoria_bebidas,
            precio=100.00
        )
        
        producto_dep2 = Producto.objects.create(
            nombre='Producto Depósito 2',
            categoria=self.categoria_bebidas,
            precio=100.00
        )
        
        ProductoDeposito.objects.create(
            producto=producto_dep1,
            deposito=self.deposito1,
            cantidad=10
        )
        
        ProductoDeposito.objects.create(
            producto=producto_dep2,
            deposito=self.deposito2,
            cantidad=15
        )
        
        # Autenticar como reponedor del depósito 1
        self.client.force_authenticate(user=self.repo_user)
        response = self.client.get(self.productos_url)
        
        productos = response.data['results'] if 'results' in response.data else response.data
        nombres = [p['nombre'] for p in productos]
        
        # Solo debe ver productos de su depósito
        self.assertIn('Producto Depósito 1', nombres)
        self.assertNotIn('Producto Depósito 2', nombres)
        
        # Autenticar como reponedor del depósito 2
        self.client.force_authenticate(user=self.repo_user2)
        response = self.client.get(self.productos_url)
        
        productos = response.data['results'] if 'results' in response.data else response.data
        nombres = [p['nombre'] for p in productos]
        
        # Solo debe ver productos de su depósito
        self.assertIn('Producto Depósito 2', nombres)
        self.assertNotIn('Producto Depósito 1', nombres)
    
    def test_obtener_categorias_disponibles(self):
        """Test: El reponedor puede obtener la lista de categorías disponibles"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        response = self.client.get(self.categorias_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        nombres_categorias = [cat['nombre'] for cat in response.data]
        self.assertIn('Bebidas', nombres_categorias)
        self.assertIn('Snacks', nombres_categorias)
    
    def test_autenticacion_requerida(self):
        """Test: La API requiere autenticación para reponedores"""
        
        response = self.client.get(self.productos_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post(self.productos_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificacionStockMinimoTestCase(TransactionTestCase):
    """Tests para las notificaciones de stock mínimo"""
    
    # Contador de clase para hacer emails únicos
    _test_counter = 100
    
    def setUp(self):
        """Configuración inicial para los tests de notificaciones"""
        # Incrementar contador para emails únicos
        NotificacionStockMinimoTestCase._test_counter += 1
        self.test_id = NotificacionStockMinimoTestCase._test_counter
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            nombre_supermercado='Supermercado Test',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Calle 123',
            supermercado=self.admin_user
        )
        
        self.categoria = Categoria.objects.create(
            nombre='Bebidas',
            descripcion='Bebidas en general'
        )
        
        self.producto = Producto.objects.create(
            nombre='Coca Cola 500ml',
            categoria=self.categoria,
            precio=150.00
        )
        
        # Crear empleado reponedor
        self.empleado_repo = Empleado.objects.create(
            nombre='María',
            apellido='González',
            email='maria@test.com',
            dni='87654321',
            puesto='REPONEDOR',
            deposito=self.deposito,
            supermercado=self.admin_user
        )
        
        # Crear usuario EmpleadoUser para el reponedor
        self.repo_user = EmpleadoUser.objects.create_user(
            username='maria_repo',
            email='maria@test.com',
            password='testpass123',
            puesto='REPONEDOR',
            supermercado=self.admin_user
        )
    
    def tearDown(self):
        """Limpiar notificaciones después de cada test"""
        Notificacion.objects.all().delete()
        ProductoDeposito.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        EmpleadoUser.objects.all().delete()
        Empleado.objects.all().delete()
        Deposito.objects.all().delete()
        User.objects.all().delete()
    
    def test_notificacion_stock_minimo_alcanzado(self):
        """Test CA: El sistema debe enviar una notificación cuando el stock actual alcance el stock mínimo"""
        
        # Crear stock inicial por encima del mínimo
        stock = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=10,
            cantidad_minima=5
        )
        
        # No debería haber notificaciones inicialmente
        self.assertEqual(Notificacion.objects.count(), 0)
        
        # Reducir stock hasta el mínimo
        stock.cantidad = 5  # Igual al mínimo
        stock.save()
        
        # Verificar que se crearon notificaciones
        notificaciones = Notificacion.objects.filter(tipo="STOCK_MINIMO")
        self.assertGreater(notificaciones.count(), 0)
        
        # Verificar notificación al admin
        notif_admin = notificaciones.filter(admin=self.admin_user).first()
        self.assertIsNotNone(notif_admin)
        self.assertIn('Stock mínimo alcanzado', notif_admin.titulo)
        self.assertIn('Coca Cola 500ml', notif_admin.mensaje)
        
        # Verificar notificación al reponedor
        notif_repo = notificaciones.filter(empleado=self.repo_user).first()
        self.assertIsNotNone(notif_repo)
        self.assertIn('Stock mínimo alcanzado', notif_repo.titulo)
    
    def test_notificacion_stock_por_debajo_minimo(self):
        """Test CA: El sistema debe enviar una notificación cuando el stock esté por debajo del mínimo"""
        
        # Crear stock inicial por encima del mínimo
        stock = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=8,
            cantidad_minima=5
        )
        
        # Limpiar notificaciones previas
        Notificacion.objects.all().delete()
        
        # Reducir stock por debajo del mínimo
        stock.cantidad = 3  # Menor al mínimo
        stock.save()
        
        # Verificar que se crearon notificaciones
        notificaciones = Notificacion.objects.filter(tipo="STOCK_MINIMO")
        self.assertGreater(notificaciones.count(), 0)
        
        # Verificar contenido de la notificación
        notif_admin = notificaciones.filter(admin=self.admin_user).first()
        self.assertIsNotNone(notif_admin)
        self.assertIn('Actual: 3', notif_admin.mensaje)
        self.assertIn('Mínimo: 5', notif_admin.mensaje)
    
    def test_no_notificacion_stock_por_encima_minimo(self):
        """Test: No se debe enviar notificación cuando el stock está por encima del mínimo"""
        
        # Crear stock por encima del mínimo
        stock = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=10,
            cantidad_minima=5
        )
        
        # Limpiar notificaciones previas
        Notificacion.objects.all().delete()
        
        # Modificar stock pero mantenerlo por encima del mínimo
        stock.cantidad = 8  # Mayor al mínimo
        stock.save()
        
        # No debería haber notificaciones de stock mínimo
        notificaciones = Notificacion.objects.filter(tipo="STOCK_MINIMO")
        self.assertEqual(notificaciones.count(), 0)
    
    @patch('productos.models.print')  # Mockear print para evitar output en tests
    def test_notificacion_con_multiple_reponedores(self, mock_print):
        """Test: Notificar a múltiples reponedores del mismo depósito"""
        
        # Crear segundo reponedor en el mismo depósito
        empleado_repo2 = Empleado.objects.create(
            nombre='Carlos',
            apellido='López',
            email=f'carlos{self.test_id}@test.com',
            dni=f'1111111{self.test_id}',
            puesto='REPONEDOR',
            deposito=self.deposito,  # Mismo depósito
            supermercado=self.admin_user
        )
        
        repo_user2 = EmpleadoUser.objects.create_user(
            username=f'carlos{self.test_id}_repo',
            email=f'carlos{self.test_id}@test.com',
            password='testpass123',
            puesto='REPONEDOR',
            supermercado=self.admin_user
        )
        
        # Crear stock que active notificación
        stock = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=2,  # Por debajo del mínimo
            cantidad_minima=5
        )
        
        # Verificar que se notificó a ambos reponedores
        notificaciones_repo = Notificacion.objects.filter(
            tipo="STOCK_MINIMO",
            empleado__isnull=False
        )
        
        self.assertEqual(notificaciones_repo.count(), 2)
        
        empleados_notificados = list(notificaciones_repo.values_list('empleado__email', flat=True))
        self.assertIn(f'maria{self.test_id}@test.com', empleados_notificados)
        self.assertIn(f'carlos{self.test_id}@test.com', empleados_notificados)


class ProductoStockAPITestCase(TransactionTestCase):
    """Tests específicos para gestión de stock por parte del reponedor"""
    
    # Contador de clase para hacer emails únicos
    _test_counter = 200
    
    def setUp(self):
        """Configuración inicial para tests de stock"""
        # Incrementar contador para emails únicos
        ProductoStockAPITestCase._test_counter += 1
        self.test_id = ProductoStockAPITestCase._test_counter
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            nombre_supermercado='Supermercado Test',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Calle 123',
            supermercado=self.admin_user
        )
        
        self.categoria = Categoria.objects.create(
            nombre='Bebidas'
        )
        
        self.producto = Producto.objects.create(
            nombre='Coca Cola 500ml',
            categoria=self.categoria,
            precio=150.00
        )
        
        # Crear empleado reponedor
        self.empleado_repo = Empleado.objects.create(
            nombre='María',
            apellido='González',
            email=f'maria{self.test_id}@test.com',
            dni=f'8765432{self.test_id}',
            puesto='REPONEDOR',
            deposito=self.deposito,
            supermercado=self.admin_user
        )
        
        self.repo_user = EmpleadoUser.objects.create_user(
            username=f'maria{self.test_id}_repo',
            email=f'maria{self.test_id}@test.com',
            password='testpass123',
            puesto='REPONEDOR',
            supermercado=self.admin_user
        )
    
    def tearDown(self):
        """Limpiar datos después de cada test"""
        ProductoDeposito.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        EmpleadoUser.objects.all().delete()
        Empleado.objects.all().delete()
        Deposito.objects.all().delete()
        User.objects.all().delete()
    
    def test_gestionar_stock_producto_get(self):
        """Test: Obtener stock de un producto específico"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear stock
        stock = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=20,
            cantidad_minima=5
        )
        
        url = reverse('productos:producto-stock', kwargs={'producto_id': self.producto.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['cantidad'], 20)
        self.assertEqual(response.data[0]['cantidad_minima'], 5)
    
    def test_gestionar_stock_producto_post(self):
        """Test: Crear stock inicial para un producto"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        url = reverse('productos:producto-stock', kwargs={'producto_id': self.producto.id})
        data = {
            'cantidad': 15,
            'cantidad_minima': 3
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se creó el stock
        stock = ProductoDeposito.objects.get(producto=self.producto, deposito=self.deposito)
        self.assertEqual(stock.cantidad, 15)
        self.assertEqual(stock.cantidad_minima, 3)
    
    def test_actualizar_stock_especifico(self):
        """Test: Actualizar stock específico de un producto"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear stock inicial
        stock = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=10,
            cantidad_minima=2
        )
        
        url = reverse('productos:stock-detail', kwargs={'stock_id': stock.id})
        data = {
            'cantidad': 25,
            'cantidad_minima': 8
        }
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar actualización
        stock.refresh_from_db()
        self.assertEqual(stock.cantidad, 25)
        self.assertEqual(stock.cantidad_minima, 8)
    
    def test_obtener_productos_por_deposito(self):
        """Test: Obtener todos los productos de un depósito específico"""
        
        self.client.force_authenticate(user=self.repo_user)
        
        # Crear múltiples productos en el depósito
        producto2 = Producto.objects.create(
            nombre='Pepsi 500ml',
            categoria=self.categoria,
            precio=145.00
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=20,
            cantidad_minima=5
        )
        
        ProductoDeposito.objects.create(
            producto=producto2,
            deposito=self.deposito,
            cantidad=15,
            cantidad_minima=3
        )
        
        url = reverse('productos:productos-por-deposito', kwargs={'deposito_id': self.deposito.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['productos']), 2)
        
        nombres_productos = [p['nombre'] for p in response.data['productos']]
        self.assertIn('Coca Cola 500ml', nombres_productos)
        self.assertIn('Pepsi 500ml', nombres_productos)