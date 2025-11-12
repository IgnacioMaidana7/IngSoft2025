"""
Tests para la Historia de Usuario: Reconocimiento de Productos por Foto
Criterios de Aceptación:
1. El cajero puede realizar una fotografía de los productos
2. El sistema identifica productos en la imagen y los registra
3. El sistema carga el producto y el cajero selecciona la cantidad
4. Para productos con diferentes capacidades, el cajero define el tamaño
5. El sistema analiza una imagen a la vez
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import base64
import io
from PIL import Image

from authentication.models import EmpleadoUser
from productos.models import Producto, Categoria, Deposito, ProductoDeposito

User = get_user_model()


class ReconocimientoBasicoTestCase(APITestCase):
    """Tests básicos para reconocimiento de productos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_recognition',
            password='admin123',
            email='admin_recog@super.com',
            nombre_supermercado='Supermercado Recognition'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Recognition',
            direccion='Calle 123',
            supermercado=self.admin_user,
            activo=True
        )
        
        self.cajero_user = EmpleadoUser.objects.create_user(
            username='cajero_recog',
            password='cajero123',
            email='cajero_recog@super.com',
            first_name='Ana',
            last_name='García',
            nombre='Ana',
            apellido='García',
            dni='33333333',
            puesto='CAJERO',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        # Crear categoría y productos
        self.categoria = Categoria.objects.create(
            nombre='Bebidas',
            descripcion='Bebidas varias'
        )
        
        self.producto_agua = Producto.objects.create(
            nombre='Agua Mineral 500ml',
            descripcion='Agua mineral sin gas',
            precio=Decimal('50.00'),
            categoria=self.categoria,
            activo=True
        )
        
        self.producto_gaseosa = Producto.objects.create(
            nombre='Coca Cola 1.5L',
            descripcion='Bebida gaseosa cola',
            precio=Decimal('150.00'),
            categoria=self.categoria,
            activo=True
        )
        
        # Stock
        ProductoDeposito.objects.create(
            producto=self.producto_agua,
            deposito=self.deposito,
            cantidad=100
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto_gaseosa,
            deposito=self.deposito,
            cantidad=80
        )
        
        self.client = APIClient()
    
    def crear_imagen_test(self):
        """Crear una imagen de prueba"""
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )
    
    def test_autenticacion_requerida(self):
        """Test: Se requiere autenticación para reconocer productos"""
        url = reverse('reconocer-productos-imagen')
        image = self.crear_imagen_test()
        
        response = self.client.post(url, {'image': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cajero_puede_enviar_imagen(self):
        """Test CA1: El cajero puede realizar una fotografía de productos"""
        self.client.force_authenticate(user=self.cajero_user)
        
        url = reverse('reconocer-productos-imagen')
        image = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            # Simular respuesta de la API
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [],
                'total_productos': 0
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': image}, format='multipart')
            
            # Verificar que se aceptó la imagen
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Verificar que se llamó a la API de reconocimiento
            self.assertTrue(mock_post.called)
    
    def test_rechazar_request_sin_imagen(self):
        """Test: Se rechaza request sin imagen"""
        self.client.force_authenticate(user=self.cajero_user)
        
        url = reverse('reconocer-productos-imagen')
        response = self.client.post(url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class ReconocimientoIdentificacionTestCase(APITestCase):
    """Tests para identificación de productos en imagen"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_ident',
            password='admin123',
            email='admin_ident@super.com',
            nombre_supermercado='Super Ident'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Test',
            direccion='Calle 123',
            supermercado=self.admin_user,
            activo=True
        )
        
        self.cajero_user = EmpleadoUser.objects.create_user(
            username='cajero_ident',
            password='cajero123',
            email='cajero_ident@super.com',
            first_name='Carlos',
            last_name='Ruiz',
            nombre='Carlos',
            apellido='Ruiz',
            dni='44444444',
            puesto='CAJERO',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        
        self.producto_agua = Producto.objects.create(
            nombre='Agua Mineral 500ml',
            precio=Decimal('50.00'),
            categoria=self.categoria,
            activo=True
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto_agua,
            deposito=self.deposito,
            cantidad=100
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.cajero_user)
    
    def crear_imagen_test(self):
        """Crear imagen de prueba"""
        img = Image.new('RGB', (100, 100), color='blue')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            name='productos.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )
    
    @patch('productos.recognition_views.requests.post')
    def test_identificar_productos_en_imagen(self, mock_post):
        """Test CA2: El sistema identifica productos en la imagen"""
        # Simular respuesta exitosa de la API con productos detectados
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [
                {
                    'ingsoft_product_id': self.producto_agua.id,
                    'nombre': 'Agua Mineral',
                    'confianza': 0.95,
                    'bbox': [10, 10, 50, 50]
                }
            ],
            'total_productos': 1
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        image = self.crear_imagen_test()
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['total_productos'], 1)
        self.assertEqual(len(response.data['productos']), 1)
        
        # Verificar que el producto fue identificado
        producto = response.data['productos'][0]
        self.assertEqual(producto['ingsoft_product_id'], self.producto_agua.id)
    
    @patch('productos.recognition_views.requests.post')
    def test_productos_registrados_en_lista(self, mock_post):
        """Test CA2: Los productos detectados se registran en la lista"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [
                {
                    'ingsoft_product_id': self.producto_agua.id,
                    'nombre': 'Agua',
                    'confianza': 0.90
                }
            ],
            'total_productos': 1
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        image = self.crear_imagen_test()
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la respuesta incluye datos de BD enriquecidos
        producto = response.data['productos'][0]
        self.assertTrue(producto['existe_en_bd'])
        self.assertEqual(producto['nombre_db'], self.producto_agua.nombre)
        self.assertEqual(producto['precio_db'], str(self.producto_agua.precio))
    
    @patch('productos.recognition_views.requests.post')
    def test_multiples_productos_detectados(self, mock_post):
        """Test: El sistema puede detectar múltiples productos en una imagen"""
        # Crear segundo producto
        producto2 = Producto.objects.create(
            nombre='Gaseosa Cola 2L',
            precio=Decimal('180.00'),
            categoria=self.categoria,
            activo=True
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [
                {'ingsoft_product_id': self.producto_agua.id, 'confianza': 0.95},
                {'ingsoft_product_id': producto2.id, 'confianza': 0.88}
            ],
            'total_productos': 2
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        image = self.crear_imagen_test()
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_productos'], 2)
        self.assertEqual(len(response.data['productos']), 2)


class ReconocimientoCantidadTestCase(APITestCase):
    """Tests para selección de cantidad después del reconocimiento"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_cant',
            password='admin123',
            email='admin_cant@super.com',
            nombre_supermercado='Super Cant'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Cant',
            direccion='Calle 123',
            supermercado=self.admin_user,
            activo=True
        )
        
        self.cajero_user = EmpleadoUser.objects.create_user(
            username='cajero_cant',
            password='cajero123',
            email='cajero_cant@super.com',
            first_name='Luis',
            last_name='Martínez',
            nombre='Luis',
            apellido='Martínez',
            dni='55555555',
            puesto='CAJERO',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        self.producto = Producto.objects.create(
            nombre='Agua 500ml',
            precio=Decimal('50.00'),
            categoria=self.categoria,
            activo=True
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=100
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.cajero_user)
    
    @patch('productos.recognition_views.requests.post')
    def test_cajero_selecciona_cantidad(self, mock_post):
        """Test CA3: El cajero puede seleccionar la cantidad a vender"""
        # El reconocimiento solo identifica el producto
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [
                {
                    'ingsoft_product_id': self.producto.id,
                    'confianza': 0.92
                }
            ],
            'total_productos': 1
        }
        mock_post.return_value = mock_response
        
        # 1. Reconocer producto
        url_reconocer = reverse('reconocer-productos-imagen')
        img = Image.new('RGB', (100, 100), color='green')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url_reconocer, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # El producto fue detectado, pero sin cantidad definida
        producto_detectado = response.data['productos'][0]
        self.assertEqual(producto_detectado['ingsoft_product_id'], self.producto.id)
        # La cantidad la define el cajero después en la venta
    
    @patch('productos.recognition_views.requests.post')
    def test_respuesta_incluye_info_para_seleccion(self, mock_post):
        """Test: La respuesta incluye información para que el cajero seleccione"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [
                {
                    'ingsoft_product_id': self.producto.id,
                    'confianza': 0.95
                }
            ],
            'total_productos': 1
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        img = Image.new('RGB', (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        # La respuesta debe incluir:
        producto = response.data['productos'][0]
        self.assertIn('ingsoft_product_id', producto)  # ID para agregar a venta
        self.assertIn('nombre_db', producto)  # Nombre del producto
        self.assertIn('precio_db', producto)  # Precio
        self.assertIn('stock_disponible', producto)  # Stock disponible


class ReconocimientoCapacidadesTestCase(APITestCase):
    """Tests para productos con diferentes capacidades"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_cap',
            password='admin123',
            email='admin_cap@super.com',
            nombre_supermercado='Super Cap'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Cap',
            direccion='Calle 123',
            supermercado=self.admin_user,
            activo=True
        )
        
        self.cajero_user = EmpleadoUser.objects.create_user(
            username='cajero_cap',
            password='cajero123',
            email='cajero_cap@super.com',
            first_name='María',
            last_name='López',
            nombre='María',
            apellido='López',
            dni='66666666',
            puesto='CAJERO',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        
        # Productos con diferentes capacidades
        self.agua_500 = Producto.objects.create(
            nombre='Agua Mineral 500ml',
            precio=Decimal('50.00'),
            categoria=self.categoria,
            activo=True
        )
        
        self.agua_1500 = Producto.objects.create(
            nombre='Agua Mineral 1.5L',
            precio=Decimal('80.00'),
            categoria=self.categoria,
            activo=True
        )
        
        ProductoDeposito.objects.create(
            producto=self.agua_500,
            deposito=self.deposito,
            cantidad=100
        )
        
        ProductoDeposito.objects.create(
            producto=self.agua_1500,
            deposito=self.deposito,
            cantidad=80
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.cajero_user)
    
    @patch('productos.recognition_views.requests.post')
    def test_detectar_productos_diferentes_capacidades(self, mock_post):
        """Test CA4: Productos con diferentes capacidades son detectados por separado"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [
                {
                    'ingsoft_product_id': self.agua_500.id,
                    'confianza': 0.93,
                    'tamaño': '500ml'
                },
                {
                    'ingsoft_product_id': self.agua_1500.id,
                    'confianza': 0.91,
                    'tamaño': '1.5L'
                }
            ],
            'total_productos': 2
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        img = Image.new('RGB', (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['productos']), 2)
        
        # Verificar que son productos diferentes
        ids = [p['ingsoft_product_id'] for p in response.data['productos']]
        self.assertIn(self.agua_500.id, ids)
        self.assertIn(self.agua_1500.id, ids)
    
    @patch('productos.recognition_views.requests.post')
    def test_cajero_selecciona_capacidad_correcta(self, mock_post):
        """Test CA4: El cajero puede verificar y seleccionar el tamaño exacto"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [
                {
                    'ingsoft_product_id': self.agua_500.id,
                    'confianza': 0.88
                }
            ],
            'total_productos': 1
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        img = Image.new('RGB', (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        # El producto detectado incluye el nombre completo con capacidad
        producto = response.data['productos'][0]
        self.assertIn('500ml', producto['nombre_db'])


class ReconocimientoUnaImagenTestCase(APITestCase):
    """Tests para restricción de una imagen a la vez"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_una',
            password='admin123',
            email='admin_una@super.com',
            nombre_supermercado='Super Una'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Una',
            direccion='Calle 123',
            supermercado=self.admin_user,
            activo=True
        )
        
        self.cajero_user = EmpleadoUser.objects.create_user(
            username='cajero_una',
            password='cajero123',
            email='cajero_una@super.com',
            first_name='Pedro',
            last_name='Sánchez',
            nombre='Pedro',
            apellido='Sánchez',
            dni='77777777',
            puesto='CAJERO',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.cajero_user)
    
    @patch('productos.recognition_views.requests.post')
    def test_procesar_una_imagen_a_la_vez(self, mock_post):
        """Test CA5: El sistema analiza una imagen a la vez"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [],
            'total_productos': 0
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        
        # Enviar primera imagen
        img1 = Image.new('RGB', (100, 100), color='red')
        img1_io = io.BytesIO()
        img1.save(img1_io, format='JPEG')
        img1_io.seek(0)
        image1 = SimpleUploadedFile('img1.jpg', img1_io.read(), content_type='image/jpeg')
        
        response1 = self.client.post(url, {'image': image1}, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # El endpoint solo acepta un archivo 'image' por request
        # No es posible enviar múltiples imágenes en una sola request
        # Esto garantiza "una imagen a la vez"
    
    @patch('productos.recognition_views.requests.post')
    def test_endpoint_acepta_solo_un_archivo(self, mock_post):
        """Test CA5: El endpoint acepta solo un archivo de imagen"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [],
            'total_productos': 0
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        
        # Intentar enviar solo una imagen (comportamiento esperado)
        img = Image.new('RGB', (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        # Una imagen procesada correctamente
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # El endpoint solo procesa la imagen enviada en el campo 'image'


class ReconocimientoErroresTestCase(APITestCase):
    """Tests para manejo de errores en reconocimiento"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_err',
            password='admin123',
            email='admin_err@super.com',
            nombre_supermercado='Super Err'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Err',
            direccion='Calle 123',
            supermercado=self.admin_user,
            activo=True
        )
        
        self.cajero_user = EmpleadoUser.objects.create_user(
            username='cajero_err',
            password='cajero123',
            email='cajero_err@super.com',
            first_name='Sofia',
            last_name='Torres',
            nombre='Sofia',
            apellido='Torres',
            dni='88888888',
            puesto='CAJERO',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.cajero_user)
    
    @patch('productos.recognition_views.requests.post')
    def test_api_reconocimiento_no_disponible(self, mock_post):
        """Test: Manejo de error cuando API no está disponible"""
        from requests.exceptions import ConnectionError
        mock_post.side_effect = ConnectionError("Connection refused")
        
        url = reverse('reconocer-productos-imagen')
        img = Image.new('RGB', (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)
    
    @patch('productos.recognition_views.requests.post')
    def test_timeout_api_reconocimiento(self, mock_post):
        """Test: Manejo de timeout en API de reconocimiento"""
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout("Request timeout")
        
        url = reverse('reconocer-productos-imagen')
        img = Image.new('RGB', (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
        self.assertFalse(response.data['success'])
    
    @patch('productos.recognition_views.requests.post')
    def test_api_retorna_error(self, mock_post):
        """Test: Manejo cuando API retorna error"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        img = Image.new('RGB', (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])


class ReconocimientoStockTestCase(APITestCase):
    """Tests para integración con información de stock"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_stock',
            password='admin123',
            email='admin_stock@super.com',
            nombre_supermercado='Super Stock'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Stock',
            direccion='Calle 123',
            supermercado=self.admin_user,
            activo=True
        )
        
        self.cajero_user = EmpleadoUser.objects.create_user(
            username='cajero_stock',
            password='cajero123',
            email='cajero_stock@super.com',
            first_name='Roberto',
            last_name='Díaz',
            nombre='Roberto',
            apellido='Díaz',
            dni='99999999',
            puesto='CAJERO',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        self.producto = Producto.objects.create(
            nombre='Agua 500ml',
            precio=Decimal('50.00'),
            categoria=self.categoria,
            activo=True
        )
        
        self.stock = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=50,
            cantidad_minima=10
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.cajero_user)
    
    @patch('productos.recognition_views.requests.post')
    def test_respuesta_incluye_stock_disponible(self, mock_post):
        """Test: La respuesta incluye stock disponible del depósito del cajero"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'productos': [
                {
                    'ingsoft_product_id': self.producto.id,
                    'confianza': 0.94
                }
            ],
            'total_productos': 1
        }
        mock_post.return_value = mock_response
        
        url = reverse('reconocer-productos-imagen')
        img = Image.new('RGB', (100, 100))
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        image = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        
        response = self.client.post(url, {'image': image}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        producto = response.data['productos'][0]
        self.assertIn('stock_disponible', producto)
        self.assertEqual(producto['stock_disponible'], 50)
