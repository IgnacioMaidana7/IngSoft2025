"""
Tests para la Historia de Usuario: Agregar Productos a Transferencia mediante Foto
Como reponedor quiero agregar productos a una transferencia mediante una foto

Criterios de Aceptación:
1. El reponedor puede tomar una foto o subir una imagen desde su dispositivo dentro del formulario de transferencia
2. El sistema procesa la imagen mediante un modelo de IA entrenado para reconocer productos registrados en la BD
3. El sistema identifica automáticamente los productos visibles en la foto y sugiere nombre y posible cantidad detectada
4. Los productos identificados se muestran en una lista previa de confirmación donde el reponedor puede:
   - Confirmar o eliminar productos detectados
   - Editar la cantidad a transferir de cada uno
5. El sistema valida que los productos detectados existan en el inventario del depósito de origen del reponedor
6. Si el modelo no logra identificar un producto, el sistema permite agregarlo manualmente
7. El reponedor puede agregar más fotos si desea detectar más productos antes de confirmar la transferencia
8. Al confirmar, los productos seleccionados se agregan automáticamente al listado de la transferencia
9. El sistema muestra un mensaje de confirmación al completar el proceso correctamente
10. Si ocurre un error (imagen no válida, IA sin respuesta o producto no encontrado), el sistema muestra mensaje de error o advertencia clara
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
from io import BytesIO
from PIL import Image

from inventario.models import Deposito, Transferencia, DetalleTransferencia
from productos.models import Producto, Categoria, ProductoDeposito
from authentication.models import EmpleadoUser

User = get_user_model()


class SubirImagenTransferenciaTestCase(APITestCase):
    """Tests para CA1: Tomar foto o subir imagen desde dispositivo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_img',
            password='admin123',
            email='admin_img@super.com',
            nombre_supermercado='Super Imagen',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Av. Principal 123',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_img',
            email='repo_img@test.com',
            password='repo123',
            nombre='Juan',
            apellido='Pérez',
            dni='12345678',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        # Crear productos de ejemplo
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        self.producto1 = Producto.objects.create(
            nombre='Coca Cola 2L',
            categoria=self.categoria,
            precio=Decimal('150.00')
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto1,
            deposito=self.deposito,
            cantidad=100
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self):
        """Crea una imagen de prueba"""
        img = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            "test_image.jpg",
            img_io.read(),
            content_type="image/jpeg"
        )
    
    def test_reponedor_puede_subir_imagen(self):
        """Test CA1: Reponedor puede subir imagen desde su dispositivo"""
        url = reverse('reconocer-productos-imagen')
        
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            # Simular respuesta exitosa de la API
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [],
                'total_productos': 0
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(mock_post.called)
    
    def test_rechazar_request_sin_imagen(self):
        """Test CA1: Sistema rechaza request sin imagen"""
        url = reverse('reconocer-productos-imagen')
        
        response = self.client.post(url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class ProcesamientoImagenIATestCase(APITestCase):
    """Tests para CA2: Procesamiento de imagen mediante modelo de IA"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_ia',
            password='admin123',
            email='admin_ia@super.com',
            nombre_supermercado='Super IA',
            cuil='20987654321',
            provincia='Córdoba',
            localidad='Córdoba Capital'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito IA',
            direccion='Calle IA 100',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_ia',
            email='repo_ia@test.com',
            password='repo123',
            nombre='María',
            apellido='González',
            dni='87654321',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.categoria = Categoria.objects.create(nombre='Alimentos')
        self.producto = Producto.objects.create(
            nombre='Pan Lactal',
            categoria=self.categoria,
            precio=Decimal('50.00')
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self):
        """Crea una imagen de prueba"""
        img = Image.new('RGB', (100, 100), color='blue')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            "producto.jpg",
            img_io.read(),
            content_type="image/jpeg"
        )
    
    def test_sistema_envia_imagen_a_api_ia(self):
        """Test CA2: Sistema envía imagen a API de reconocimiento"""
        url = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [],
                'total_productos': 0
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Verificar que se llamó a la API
            self.assertTrue(mock_post.called)
            # Verificar que se envió base64
            call_args = mock_post.call_args
            self.assertIn('json', call_args.kwargs)
            self.assertIn('image_base64', call_args.kwargs['json'])


class IdentificacionProductosTestCase(APITestCase):
    """Tests para CA3: Identificación automática de productos y cantidades"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_ident',
            password='admin123',
            email='admin_ident@super.com',
            nombre_supermercado='Super Identificación',
            cuil='20111222333',
            provincia='Santa Fe',
            localidad='Rosario'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Identificación',
            direccion='Dir Ident',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_ident',
            email='repo_ident@test.com',
            password='repo123',
            nombre='Carlos',
            apellido='López',
            dni='11223344',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        self.producto1 = Producto.objects.create(
            nombre='Sprite 1.5L',
            categoria=self.categoria,
            precio=Decimal('120.00')
        )
        self.producto2 = Producto.objects.create(
            nombre='Fanta 2L',
            categoria=self.categoria,
            precio=Decimal('140.00')
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto1,
            deposito=self.deposito,
            cantidad=50
        )
        ProductoDeposito.objects.create(
            producto=self.producto2,
            deposito=self.deposito,
            cantidad=30
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self):
        img = Image.new('RGB', (200, 200), color='green')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile("productos.jpg", img_io.read(), content_type="image/jpeg")
    
    def test_sistema_identifica_productos_en_imagen(self):
        """Test CA3: Sistema identifica productos visibles en la foto"""
        url = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': self.producto1.id,
                        'nombre': 'Sprite 1.5L',
                        'confianza': 0.95,
                        'cantidad_detectada': 2
                    },
                    {
                        'ingsoft_product_id': self.producto2.id,
                        'nombre': 'Fanta 2L',
                        'confianza': 0.88,
                        'cantidad_detectada': 1
                    }
                ],
                'total_productos': 2
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(len(response.data['productos']), 2)
            self.assertEqual(response.data['total_productos'], 2)
    
    def test_sistema_sugiere_nombre_y_cantidad(self):
        """Test CA3: Sistema sugiere nombre y cantidad detectada"""
        url = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': self.producto1.id,
                        'nombre': 'Sprite 1.5L',
                        'confianza': 0.92,
                        'cantidad_detectada': 3
                    }
                ],
                'total_productos': 1
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            producto_detectado = response.data['productos'][0]
            self.assertIn('nombre', producto_detectado)
            self.assertIn('cantidad_detectada', producto_detectado)
            self.assertEqual(producto_detectado['cantidad_detectada'], 3)


class ListaConfirmacionProductosTestCase(APITestCase):
    """Tests para CA4: Lista previa de confirmación con opciones de edición"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_conf',
            password='admin123',
            email='admin_conf@super.com',
            nombre_supermercado='Super Confirmación',
            cuil='20444555666',
            provincia='Mendoza',
            localidad='Mendoza Capital'
        )
        
        self.deposito_origen = Deposito.objects.create(
            nombre='Dep Origen',
            direccion='Dir Origen',
            supermercado=self.admin_user
        )
        
        self.deposito_destino = Deposito.objects.create(
            nombre='Dep Destino',
            direccion='Dir Destino',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_conf',
            email='repo_conf@test.com',
            password='repo123',
            nombre='Ana',
            apellido='Martínez',
            dni='22334455',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito_origen
        )
        
        self.categoria = Categoria.objects.create(nombre='Snacks')
        self.producto = Producto.objects.create(
            nombre='Doritos',
            categoria=self.categoria,
            precio=Decimal('130.00')
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito_origen,
            cantidad=40
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self):
        img = Image.new('RGB', (150, 150), color='yellow')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile("snacks.jpg", img_io.read(), content_type="image/jpeg")
    
    def test_productos_detectados_en_lista_confirmacion(self):
        """Test CA4: Productos identificados se muestran en lista de confirmación"""
        url = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': self.producto.id,
                        'nombre': 'Doritos',
                        'confianza': 0.90,
                        'cantidad_detectada': 5
                    }
                ],
                'total_productos': 1
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('productos', response.data)
            self.assertEqual(len(response.data['productos']), 1)
    
    def test_crear_transferencia_con_productos_confirmados(self):
        """Test CA4: Reponedor puede confirmar y crear transferencia con productos detectados"""
        url_transferencia = reverse('transferencia-list-create')
        
        # Simular que el usuario confirmó productos detectados
        data = {
            'deposito_origen': self.deposito_origen.id,
            'deposito_destino': self.deposito_destino.id,
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 5  # Cantidad editada por el usuario
                }
            ]
        }
        
        response = self.client.post(url_transferencia, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
    
    def test_editar_cantidad_producto_detectado(self):
        """Test CA4: Reponedor puede editar cantidad de producto detectado"""
        url_transferencia = reverse('transferencia-list-create')
        
        # Producto detectado con cantidad 5, usuario cambia a 8
        data = {
            'deposito_origen': self.deposito_origen.id,
            'deposito_destino': self.deposito_destino.id,
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 8  # Cantidad editada diferente a la detectada
                }
            ]
        }
        
        response = self.client.post(url_transferencia, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transferencia = Transferencia.objects.get(id=response.data['id'])
        detalle = transferencia.detalles.first()
        self.assertEqual(detalle.cantidad, 8)


class ValidacionInventarioDepositoTestCase(APITestCase):
    """Tests para CA5: Validación de productos en inventario del depósito de origen"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_val',
            password='admin123',
            email='admin_val@super.com',
            nombre_supermercado='Super Validación',
            cuil='20777888999',
            provincia='Salta',
            localidad='Salta Capital'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Validación',
            direccion='Dir Val',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_val',
            email='repo_val@test.com',
            password='repo123',
            nombre='Pedro',
            apellido='Ramírez',
            dni='33445566',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.categoria = Categoria.objects.create(nombre='Lácteos')
        self.producto_con_stock = Producto.objects.create(
            nombre='Leche Entera',
            categoria=self.categoria,
            precio=Decimal('200.00')
        )
        self.producto_sin_stock = Producto.objects.create(
            nombre='Yogurt',
            categoria=self.categoria,
            precio=Decimal('150.00')
        )
        
        # Solo producto_con_stock tiene stock en el depósito
        ProductoDeposito.objects.create(
            producto=self.producto_con_stock,
            deposito=self.deposito,
            cantidad=75
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self):
        img = Image.new('RGB', (180, 180), color='white')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile("lacteos.jpg", img_io.read(), content_type="image/jpeg")
    
    def test_sistema_valida_producto_existe_en_deposito(self):
        """Test CA5: Sistema valida que productos detectados existan en inventario del depósito"""
        url = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': self.producto_con_stock.id,
                        'nombre': 'Leche Entera',
                        'confianza': 0.93,
                        'cantidad_detectada': 2
                    }
                ],
                'total_productos': 1
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            producto_detectado = response.data['productos'][0]
            # Verificar que se enriqueció con información de stock
            self.assertIn('stock_disponible', producto_detectado)
            self.assertEqual(producto_detectado['stock_disponible'], 75)


class ProductoNoIdentificadoTestCase(APITestCase):
    """Tests para CA6: Permitir agregar productos manualmente si no se identifican"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_manual',
            password='admin123',
            email='admin_manual@super.com',
            nombre_supermercado='Super Manual',
            cuil='20666555444',
            provincia='Jujuy',
            localidad='San Salvador'
        )
        
        self.deposito_origen = Deposito.objects.create(
            nombre='Dep Manual',
            direccion='Dir Manual',
            supermercado=self.admin_user
        )
        
        self.deposito_destino = Deposito.objects.create(
            nombre='Dep Dest Manual',
            direccion='Dir Dest Manual',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_manual',
            email='repo_manual@test.com',
            password='repo123',
            nombre='Luis',
            apellido='Fernández',
            dni='44556677',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito_origen
        )
        
        self.categoria = Categoria.objects.create(nombre='Cereales')
        self.producto = Producto.objects.create(
            nombre='Arroz Integral',
            categoria=self.categoria,
            precio=Decimal('100.00')
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito_origen,
            cantidad=20
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def test_agregar_producto_manualmente_si_ia_no_detecta(self):
        """Test CA6: Sistema permite agregar productos manualmente"""
        url = reverse('transferencia-list-create')
        
        # Usuario agrega producto manualmente (no detectado por IA)
        data = {
            'deposito_origen': self.deposito_origen.id,
            'deposito_destino': self.deposito_destino.id,
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 5
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transferencia = Transferencia.objects.get(id=response.data['id'])
        self.assertEqual(transferencia.detalles.count(), 1)


class MultiplesFotosTestCase(APITestCase):
    """Tests para CA7: Agregar múltiples fotos antes de confirmar transferencia"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_multi',
            password='admin123',
            email='admin_multi@super.com',
            nombre_supermercado='Super Multi',
            cuil='20333222111',
            provincia='Tucumán',
            localidad='San Miguel de Tucumán'
        )
        
        self.deposito_origen = Deposito.objects.create(
            nombre='Dep Multi',
            direccion='Dir Multi',
            supermercado=self.admin_user
        )
        
        self.deposito_destino = Deposito.objects.create(
            nombre='Dep Dest Multi',
            direccion='Dir Dest Multi',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_multi',
            email='repo_multi@test.com',
            password='repo123',
            nombre='Sofía',
            apellido='Torres',
            dni='55667788',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito_origen
        )
        
        self.categoria = Categoria.objects.create(nombre='Frutas')
        self.producto1 = Producto.objects.create(
            nombre='Manzana Roja',
            categoria=self.categoria,
            precio=Decimal('30.00')
        )
        self.producto2 = Producto.objects.create(
            nombre='Banana',
            categoria=self.categoria,
            precio=Decimal('25.00')
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto1,
            deposito=self.deposito_origen,
            cantidad=100
        )
        ProductoDeposito.objects.create(
            producto=self.producto2,
            deposito=self.deposito_origen,
            cantidad=80
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self, name="imagen.jpg"):
        img = Image.new('RGB', (120, 120), color='orange')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(name, img_io.read(), content_type="image/jpeg")
    
    def test_procesar_multiples_imagenes_antes_de_confirmar(self):
        """Test CA7: Reponedor puede agregar múltiples fotos"""
        url = reverse('reconocer-productos-imagen')
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            # Primera imagen
            mock_response1 = MagicMock()
            mock_response1.status_code = 200
            mock_response1.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': self.producto1.id,
                        'nombre': 'Manzana Roja',
                        'cantidad_detectada': 10
                    }
                ],
                'total_productos': 1
            }
            
            # Segunda imagen
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': self.producto2.id,
                        'nombre': 'Banana',
                        'cantidad_detectada': 12
                    }
                ],
                'total_productos': 1
            }
            
            mock_post.side_effect = [mock_response1, mock_response2]
            
            # Procesar primera imagen
            imagen1 = self.crear_imagen_test("foto1.jpg")
            response1 = self.client.post(url, {'image': imagen1}, format='multipart')
            self.assertEqual(response1.status_code, status.HTTP_200_OK)
            
            # Procesar segunda imagen
            imagen2 = self.crear_imagen_test("foto2.jpg")
            response2 = self.client.post(url, {'image': imagen2}, format='multipart')
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            
            # Verificar que se procesaron ambas
            self.assertEqual(mock_post.call_count, 2)


class ConfirmarProductosTransferenciaTestCase(APITestCase):
    """Tests para CA8: Productos seleccionados se agregan al listado de transferencia"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_agregar',
            password='admin123',
            email='admin_agregar@super.com',
            nombre_supermercado='Super Agregar',
            cuil='20888999000',
            provincia='Chaco',
            localidad='Resistencia'
        )
        
        self.deposito_origen = Deposito.objects.create(
            nombre='Dep Agregar',
            direccion='Dir Agregar',
            supermercado=self.admin_user
        )
        
        self.deposito_destino = Deposito.objects.create(
            nombre='Dep Dest Agregar',
            direccion='Dir Dest Agregar',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_agregar',
            email='repo_agregar@test.com',
            password='repo123',
            nombre='Diego',
            apellido='Sánchez',
            dni='66778899',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito_origen
        )
        
        self.categoria = Categoria.objects.create(nombre='Electrónica')
        self.producto = Producto.objects.create(
            nombre='Cable USB',
            categoria=self.categoria,
            precio=Decimal('500.00')
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito_origen,
            cantidad=60
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def test_productos_confirmados_se_agregan_a_transferencia(self):
        """Test CA8: Al confirmar, productos se agregan automáticamente a la transferencia"""
        url = reverse('transferencia-list-create')
        
        data = {
            'deposito_origen': self.deposito_origen.id,
            'deposito_destino': self.deposito_destino.id,
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 15
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('detalles', response.data)
        self.assertEqual(len(response.data['detalles']), 1)
        self.assertEqual(response.data['detalles'][0]['cantidad'], 15)


class MensajeConfirmacionReconocimientoTestCase(APITestCase):
    """Tests para CA9: Mensaje de confirmación al completar proceso"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_msg',
            password='admin123',
            email='admin_msg@super.com',
            nombre_supermercado='Super Mensaje',
            cuil='20111000999',
            provincia='Formosa',
            localidad='Formosa Capital'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Dep Mensaje',
            direccion='Dir Msg',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_msg',
            email='repo_msg@test.com',
            password='repo123',
            nombre='Ricardo',
            apellido='Díaz',
            dni='88990011',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.categoria = Categoria.objects.create(nombre='Útiles')
        self.producto = Producto.objects.create(
            nombre='Cuaderno A4',
            categoria=self.categoria,
            precio=Decimal('80.00')
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=200
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self):
        img = Image.new('RGB', (100, 100), color='purple')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile("test.jpg", img_io.read(), content_type="image/jpeg")
    
    def test_mensaje_confirmacion_reconocimiento_exitoso(self):
        """Test CA9: Sistema muestra mensaje de confirmación al procesar imagen exitosamente"""
        url = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': self.producto.id,
                        'nombre': 'Cuaderno A4',
                        'cantidad_detectada': 5
                    }
                ],
                'total_productos': 1
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertIn('productos', response.data)


class ManejodeErroresReconocimientoTestCase(APITestCase):
    """Tests para CA10: Mensajes de error claros ante problemas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_err',
            password='admin123',
            email='admin_err@super.com',
            nombre_supermercado='Super Error',
            cuil='20222111000',
            provincia='Catamarca',
            localidad='San Fernando'
        )
        
        self.deposito = Deposito.objects.create(
            nombre='Dep Error',
            direccion='Dir Err',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_err',
            email='repo_err@test.com',
            password='repo123',
            nombre='Gabriela',
            apellido='Ruiz',
            dni='99001122',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self):
        img = Image.new('RGB', (100, 100), color='black')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile("error.jpg", img_io.read(), content_type="image/jpeg")
    
    def test_error_imagen_no_valida(self):
        """Test CA10: Mensaje claro cuando imagen no es válida"""
        url = reverse('reconocer-productos-imagen')
        
        # Enviar archivo que no es imagen
        archivo_invalido = SimpleUploadedFile(
            "texto.txt",
            b"Este no es una imagen",
            content_type="text/plain"
        )
        
        response = self.client.post(url, {'image': archivo_invalido}, format='multipart')
        
        # La API podría devolver error al procesar
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])
    
    def test_error_api_ia_sin_respuesta(self):
        """Test CA10: Mensaje claro cuando API de IA no responde"""
        url = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            # Simular timeout
            mock_post.side_effect = Exception("Connection timeout")
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
    
    def test_error_producto_no_encontrado_en_bd(self):
        """Test CA10: Mensaje claro cuando producto detectado no existe en BD"""
        url = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': 99999,  # ID que no existe
                        'nombre': 'Producto Inexistente',
                        'cantidad_detectada': 1
                    }
                ],
                'total_productos': 1
            }
            mock_post.return_value = mock_response
            
            response = self.client.post(url, {'image': imagen}, format='multipart')
            
            # La respuesta puede ser exitosa pero el producto marcado como no encontrado
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            producto = response.data['productos'][0]
            self.assertFalse(producto.get('existe_en_bd', True))


class IntegracionReconocimientoTransferenciaTestCase(APITestCase):
    """Tests de integración completa: Foto → Reconocimiento → Transferencia"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_int',
            password='admin123',
            email='admin_int@super.com',
            nombre_supermercado='Super Integración',
            cuil='20444333222',
            provincia='La Rioja',
            localidad='La Rioja Capital'
        )
        
        self.deposito_origen = Deposito.objects.create(
            nombre='Dep Origen Int',
            direccion='Dir Origen Int',
            supermercado=self.admin_user
        )
        
        self.deposito_destino = Deposito.objects.create(
            nombre='Dep Destino Int',
            direccion='Dir Destino Int',
            supermercado=self.admin_user
        )
        
        self.reponedor = EmpleadoUser.objects.create_user(
            username='repo_int',
            email='repo_int@test.com',
            password='repo123',
            nombre='Alberto',
            apellido='Mendoza',
            dni='22110099',
            puesto='REPONEDOR',
            supermercado=self.admin_user,
            deposito=self.deposito_origen
        )
        
        self.categoria = Categoria.objects.create(nombre='Tecnología')
        self.producto1 = Producto.objects.create(
            nombre='Mouse Inalámbrico',
            categoria=self.categoria,
            precio=Decimal('300.00')
        )
        self.producto2 = Producto.objects.create(
            nombre='Teclado USB',
            categoria=self.categoria,
            precio=Decimal('450.00')
        )
        
        ProductoDeposito.objects.create(
            producto=self.producto1,
            deposito=self.deposito_origen,
            cantidad=50
        )
        ProductoDeposito.objects.create(
            producto=self.producto2,
            deposito=self.deposito_origen,
            cantidad=30
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.reponedor)
    
    def crear_imagen_test(self):
        img = Image.new('RGB', (200, 200), color='cyan')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile("integracion.jpg", img_io.read(), content_type="image/jpeg")
    
    def test_flujo_completo_foto_a_transferencia(self):
        """Test Integración: Flujo completo desde foto hasta transferencia creada"""
        # 1. Subir foto y reconocer productos
        url_reconocimiento = reverse('reconocer-productos-imagen')
        imagen = self.crear_imagen_test()
        
        with patch('productos.recognition_views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'productos': [
                    {
                        'ingsoft_product_id': self.producto1.id,
                        'nombre': 'Mouse Inalámbrico',
                        'cantidad_detectada': 3
                    },
                    {
                        'ingsoft_product_id': self.producto2.id,
                        'nombre': 'Teclado USB',
                        'cantidad_detectada': 2
                    }
                ],
                'total_productos': 2
            }
            mock_post.return_value = mock_response
            
            response_reconocimiento = self.client.post(
                url_reconocimiento,
                {'image': imagen},
                format='multipart'
            )
            
            self.assertEqual(response_reconocimiento.status_code, status.HTTP_200_OK)
            self.assertTrue(response_reconocimiento.data['success'])
            self.assertEqual(len(response_reconocimiento.data['productos']), 2)
        
        # 2. Crear transferencia con productos detectados
        url_transferencia = reverse('transferencia-list-create')
        
        data_transferencia = {
            'deposito_origen': self.deposito_origen.id,
            'deposito_destino': self.deposito_destino.id,
            'detalles': [
                {
                    'producto': self.producto1.id,
                    'cantidad': 3  # Confirmada de la detección
                },
                {
                    'producto': self.producto2.id,
                    'cantidad': 2  # Confirmada de la detección
                }
            ]
        }
        
        response_transferencia = self.client.post(
            url_transferencia,
            data_transferencia,
            format='json'
        )
        
        self.assertEqual(response_transferencia.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response_transferencia.data)
        
        # 3. Verificar transferencia creada
        transferencia_id = response_transferencia.data['id']
        url_detalle = reverse('transferencia-detail', kwargs={'pk': transferencia_id})
        response_detalle = self.client.get(url_detalle)
        
        self.assertEqual(response_detalle.status_code, status.HTTP_200_OK)
        self.assertEqual(response_detalle.data['estado'], 'PENDIENTE')
        self.assertEqual(len(response_detalle.data['detalles']), 2)
