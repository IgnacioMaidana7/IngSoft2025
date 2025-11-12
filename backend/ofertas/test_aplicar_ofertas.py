"""
Tests para la Historia de Usuario: Aplicar Ofertas a Productos
Como administrador quiero aplicar las ofertas creadas a productos.

Criterios de Aceptación:
1. El administrador puede seleccionar una oferta existente desde una lista desplegable
2. El sistema muestra un listado de productos disponibles, indicando su nombre, categoría, precio actual y estado de oferta
3. El administrador puede asignar una oferta a uno o varios productos simultáneamente
4. Al aplicar una oferta, el sistema actualiza el precio final del producto según el tipo y valor del descuento definido
5. El administrador puede quitar una oferta de un producto en cualquier momento
6. El sistema debe verificar la validez de la oferta (fecha vigente) antes de aplicarla
7. El sistema muestra una confirmación visual o mensaje de éxito al aplicar o quitar una oferta
8. El listado de productos puede ser filtrado por categoría o por estado de oferta
9. El sistema debe permitir ver qué productos están asociados a cada oferta desde la vista de detalle de la oferta
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from ofertas.models import Oferta, ProductoOferta
from productos.models import Producto, Categoria

User = get_user_model()


class SeleccionarOfertaTestCase(APITestCase):
    """Tests para CA1: Seleccionar oferta desde lista desplegable"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_select',
            password='admin123',
            email='admin_select@super.com',
            nombre_supermercado='Supermercado Select'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear ofertas de prueba
        ahora = timezone.now()
        self.oferta_activa = Oferta.objects.create(
            nombre='Descuento 10%',
            descripcion='Oferta activa',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=6),
            activo=True
        )
        
        self.oferta_proxima = Oferta.objects.create(
            nombre='Descuento futuro 20%',
            descripcion='Oferta próxima',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('20.00'),
            fecha_inicio=ahora + timedelta(days=2),
            fecha_fin=ahora + timedelta(days=9),
            activo=True
        )
    
    def test_listar_ofertas_disponibles(self):
        """Test CA1: Admin puede ver lista de ofertas disponibles"""
        url = reverse('ofertas-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)
    
    def test_obtener_detalle_oferta_para_seleccion(self):
        """Test CA1: Admin puede obtener detalles de una oferta específica"""
        url = reverse('ofertas-detail', kwargs={'pk': self.oferta_activa.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.oferta_activa.id)
        self.assertEqual(response.data['nombre'], 'Descuento 10%')


class ListarProductosDisponiblesTestCase(APITestCase):
    """Tests para CA2: Listar productos con información completa"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_list_prod',
            password='admin123',
            email='admin_list_prod@super.com',
            nombre_supermercado='Supermercado List'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categorías
        self.categoria_bebidas = Categoria.objects.create(nombre='Bebidas')
        self.categoria_snacks = Categoria.objects.create(nombre='Snacks')
        
        # Crear productos
        self.producto_sin_oferta = Producto.objects.create(
            nombre='Coca Cola',
            descripcion='Gaseosa 2L',
            precio=Decimal('150.00'),
            
            categoria=self.categoria_bebidas,
            activo=True
        )
        
        self.producto_con_oferta = Producto.objects.create(
            nombre='Pepsi',
            descripcion='Gaseosa 2L',
            precio=Decimal('140.00'),
            
            categoria=self.categoria_bebidas,
            activo=True
        )
        
        # Crear oferta y asignar a un producto
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Descuento Bebidas',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=5),
            activo=True
        )
        
        ProductoOferta.objects.create(
            producto=self.producto_con_oferta,
            oferta=self.oferta,
            precio_original=self.producto_con_oferta.precio
        )
    
    def test_listar_productos_con_nombre_categoria_precio(self):
        """Test CA2: Listado muestra nombre, categoría y precio"""
        url = reverse('producto-ofertas-productos-con-ofertas')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 2)
        
        # Verificar que tiene los campos requeridos
        for producto in response.data:
            self.assertIn('nombre', producto)
            self.assertIn('categoria', producto)
            self.assertIn('precio', producto)
            self.assertIn('tiene_ofertas_activas', producto)
    
    def test_listado_indica_estado_oferta_con_oferta(self):
        """Test CA2: El listado indica si el producto tiene oferta"""
        url = reverse('producto-ofertas-productos-con-ofertas')
        
        response = self.client.get(url)
        
        # Buscar el producto con oferta
        producto_con_oferta_data = next(
            (p for p in response.data if p['id'] == self.producto_con_oferta.id), 
            None
        )
        
        self.assertIsNotNone(producto_con_oferta_data)
        self.assertTrue(producto_con_oferta_data['tiene_ofertas_activas'])
    
    def test_listado_indica_estado_oferta_sin_oferta(self):
        """Test CA2: El listado indica si el producto NO tiene oferta"""
        url = reverse('producto-ofertas-productos-con-ofertas')
        
        response = self.client.get(url)
        
        # Buscar el producto sin oferta
        producto_sin_oferta_data = next(
            (p for p in response.data if p['id'] == self.producto_sin_oferta.id), 
            None
        )
        
        self.assertIsNotNone(producto_sin_oferta_data)
        self.assertFalse(producto_sin_oferta_data['tiene_ofertas_activas'])


class AsignarOfertaProductosTestCase(APITestCase):
    """Tests para CA3: Asignar oferta a uno o varios productos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_asignar',
            password='admin123',
            email='admin_asignar@super.com',
            nombre_supermercado='Supermercado Asignar'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categoría y productos
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        
        self.producto1 = Producto.objects.create(
            nombre='Producto 1',
            precio=Decimal('100.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        self.producto2 = Producto.objects.create(
            nombre='Producto 2',
            precio=Decimal('200.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        # Crear oferta activa
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Oferta Test',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('20.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=7),
            activo=True
        )
    
    def test_asignar_oferta_a_un_producto(self):
        """Test CA3: Admin puede asignar oferta a un solo producto"""
        url = reverse('ofertas-asignar-productos', kwargs={'pk': self.oferta.id})
        
        data = {
            'productos_ids': [self.producto1.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('1', response.data['message'])
        
        # Verificar que se creó la asignación
        self.assertTrue(
            ProductoOferta.objects.filter(
                producto=self.producto1, 
                oferta=self.oferta
            ).exists()
        )
    
    def test_asignar_oferta_a_varios_productos_simultaneamente(self):
        """Test CA3: Admin puede asignar oferta a múltiples productos simultáneamente"""
        url = reverse('ofertas-asignar-productos', kwargs={'pk': self.oferta.id})
        
        data = {
            'productos_ids': [self.producto1.id, self.producto2.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('2', response.data['message'])
        
        # Verificar que se crearon ambas asignaciones
        self.assertTrue(
            ProductoOferta.objects.filter(
                producto=self.producto1, 
                oferta=self.oferta
            ).exists()
        )
        self.assertTrue(
            ProductoOferta.objects.filter(
                producto=self.producto2, 
                oferta=self.oferta
            ).exists()
        )


class ActualizarPrecioConDescuentoTestCase(APITestCase):
    """Tests para CA4: Actualización automática del precio con descuento"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_precio',
            password='admin123',
            email='admin_precio@super.com',
            nombre_supermercado='Supermercado Precio'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categoría y producto
        self.categoria = Categoria.objects.create(nombre='Alimentos')
        
        self.producto = Producto.objects.create(
            nombre='Producto Test',
            precio=Decimal('100.00'),
            
            categoria=self.categoria,
            activo=True
        )
    
    def test_aplicar_descuento_porcentual_actualiza_precio(self):
        """Test CA4: Al aplicar oferta porcentual, se calcula el precio con descuento"""
        ahora = timezone.now()
        oferta_porcentaje = Oferta.objects.create(
            nombre='20% de descuento',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('20.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=5),
            activo=True
        )
        
        url = reverse('ofertas-asignar-productos', kwargs={'pk': oferta_porcentaje.id})
        data = {'productos_ids': [self.producto.id]}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar el precio con descuento
        producto_oferta = ProductoOferta.objects.get(
            producto=self.producto, 
            oferta=oferta_porcentaje
        )
        
        precio_esperado = Decimal('80.00')  # 100 - 20%
        self.assertEqual(producto_oferta.precio_con_descuento, precio_esperado)
        self.assertEqual(producto_oferta.precio_original, Decimal('100.00'))
    
    def test_aplicar_descuento_monto_fijo_actualiza_precio(self):
        """Test CA4: Al aplicar oferta de monto fijo, se calcula el precio con descuento"""
        ahora = timezone.now()
        oferta_fija = Oferta.objects.create(
            nombre='$30 de descuento',
            tipo_descuento='monto_fijo',
            valor_descuento=Decimal('30.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=5),
            activo=True
        )
        
        url = reverse('ofertas-asignar-productos', kwargs={'pk': oferta_fija.id})
        data = {'productos_ids': [self.producto.id]}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar el precio con descuento
        producto_oferta = ProductoOferta.objects.get(
            producto=self.producto, 
            oferta=oferta_fija
        )
        
        precio_esperado = Decimal('70.00')  # 100 - 30
        self.assertEqual(producto_oferta.precio_con_descuento, precio_esperado)


class QuitarOfertaProductoTestCase(APITestCase):
    """Tests para CA5: Quitar oferta de un producto"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_quitar',
            password='admin123',
            email='admin_quitar@super.com',
            nombre_supermercado='Supermercado Quitar'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categoría y producto
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        
        self.producto = Producto.objects.create(
            nombre='Producto con Oferta',
            precio=Decimal('150.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        # Crear oferta y asignarla al producto
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Oferta a Quitar',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('25.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=5),
            activo=True
        )
        
        ProductoOferta.objects.create(
            producto=self.producto,
            oferta=self.oferta,
            precio_original=self.producto.precio
        )
    
    def test_quitar_oferta_de_producto(self):
        """Test CA5: Admin puede quitar oferta de un producto"""
        # Verificar que la oferta existe
        self.assertTrue(
            ProductoOferta.objects.filter(
                producto=self.producto, 
                oferta=self.oferta
            ).exists()
        )
        
        url = reverse('ofertas-quitar-productos', kwargs={'pk': self.oferta.id})
        data = {'productos_ids': [self.producto.id]}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('1', response.data['message'])
        
        # Verificar que la oferta fue eliminada
        self.assertFalse(
            ProductoOferta.objects.filter(
                producto=self.producto, 
                oferta=self.oferta
            ).exists()
        )
    
    def test_quitar_oferta_de_multiples_productos(self):
        """Test CA5: Admin puede quitar oferta de múltiples productos"""
        # Crear otro producto con la misma oferta
        producto2 = Producto.objects.create(
            nombre='Producto 2 con Oferta',
            precio=Decimal('200.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        ProductoOferta.objects.create(
            producto=producto2,
            oferta=self.oferta,
            precio_original=producto2.precio
        )
        
        url = reverse('ofertas-quitar-productos', kwargs={'pk': self.oferta.id})
        data = {'productos_ids': [self.producto.id, producto2.id]}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('2', response.data['message'])
        
        # Verificar que ambas ofertas fueron eliminadas
        self.assertEqual(
            ProductoOferta.objects.filter(oferta=self.oferta).count(), 
            0
        )


class ValidarVigenciaOfertaTestCase(APITestCase):
    """Tests para CA6: Verificar validez de oferta antes de aplicarla"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_validez',
            password='admin123',
            email='admin_validez@super.com',
            nombre_supermercado='Supermercado Validez'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categoría y producto
        self.categoria = Categoria.objects.create(nombre='Alimentos')
        
        self.producto = Producto.objects.create(
            nombre='Producto Test',
            precio=Decimal('100.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        # Crear oferta expirada
        ahora = timezone.now()
        self.oferta_expirada = Oferta.objects.create(
            nombre='Oferta Expirada',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('30.00'),
            fecha_inicio=ahora - timedelta(days=10),
            fecha_fin=ahora - timedelta(days=3),
            activo=True
        )
    
    def test_no_asignar_oferta_expirada(self):
        """Test CA6: No se puede asignar una oferta expirada a un producto"""
        url = reverse('ofertas-asignar-productos', kwargs={'pk': self.oferta_expirada.id})
        data = {'productos_ids': [self.producto.id]}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('expirada', response.data['error'].lower())
        
        # Verificar que NO se creó la asignación
        self.assertFalse(
            ProductoOferta.objects.filter(
                producto=self.producto, 
                oferta=self.oferta_expirada
            ).exists()
        )
    
    def test_asignar_oferta_vigente(self):
        """Test CA6: Se puede asignar una oferta vigente"""
        ahora = timezone.now()
        oferta_vigente = Oferta.objects.create(
            nombre='Oferta Vigente',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=5),
            activo=True
        )
        
        url = reverse('ofertas-asignar-productos', kwargs={'pk': oferta_vigente.id})
        data = {'productos_ids': [self.producto.id]}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que SÍ se creó la asignación
        self.assertTrue(
            ProductoOferta.objects.filter(
                producto=self.producto, 
                oferta=oferta_vigente
            ).exists()
        )


class MensajesConfirmacionTestCase(APITestCase):
    """Tests para CA7: Mensajes de confirmación al aplicar/quitar ofertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_mensaje',
            password='admin123',
            email='admin_mensaje@super.com',
            nombre_supermercado='Supermercado Mensaje'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categoría y producto
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        
        self.producto = Producto.objects.create(
            nombre='Producto Test',
            precio=Decimal('120.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        # Crear oferta
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Oferta Test',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=6),
            activo=True
        )
    
    def test_mensaje_confirmacion_al_asignar_oferta(self):
        """Test CA7: Mensaje de éxito al asignar oferta"""
        url = reverse('ofertas-asignar-productos', kwargs={'pk': self.oferta.id})
        data = {'productos_ids': [self.producto.id]}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('asignaron', response.data['message'].lower())
    
    def test_mensaje_confirmacion_al_quitar_oferta(self):
        """Test CA7: Mensaje de éxito al quitar oferta"""
        # Primero asignar la oferta
        ProductoOferta.objects.create(
            producto=self.producto,
            oferta=self.oferta,
            precio_original=self.producto.precio
        )
        
        url = reverse('ofertas-quitar-productos', kwargs={'pk': self.oferta.id})
        data = {'productos_ids': [self.producto.id]}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('quitaron', response.data['message'].lower())


class FiltrarProductosTestCase(APITestCase):
    """Tests para CA8: Filtrado de productos por categoría y estado de oferta"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_filtro',
            password='admin123',
            email='admin_filtro@super.com',
            nombre_supermercado='Supermercado Filtro'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categorías
        self.categoria_bebidas = Categoria.objects.create(nombre='Bebidas')
        self.categoria_snacks = Categoria.objects.create(nombre='Snacks')
        
        # Crear productos en diferentes categorías
        self.bebida_con_oferta = Producto.objects.create(
            nombre='Coca Cola',
            precio=Decimal('150.00'),
            
            categoria=self.categoria_bebidas,
            activo=True
        )
        
        self.bebida_sin_oferta = Producto.objects.create(
            nombre='Sprite',
            precio=Decimal('140.00'),
            
            categoria=self.categoria_bebidas,
            activo=True
        )
        
        self.snack_con_oferta = Producto.objects.create(
            nombre='Papas Lays',
            precio=Decimal('80.00'),
            
            categoria=self.categoria_snacks,
            activo=True
        )
        
        # Crear oferta y asignar a algunos productos
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Oferta General',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=5),
            activo=True
        )
        
        ProductoOferta.objects.create(
            producto=self.bebida_con_oferta,
            oferta=self.oferta,
            precio_original=self.bebida_con_oferta.precio
        )
        
        ProductoOferta.objects.create(
            producto=self.snack_con_oferta,
            oferta=self.oferta,
            precio_original=self.snack_con_oferta.precio
        )
    
    def test_filtrar_productos_por_categoria(self):
        """Test CA8: Filtrar productos por categoría"""
        url = reverse('producto-ofertas-productos-con-ofertas') + f'?categoria={self.categoria_bebidas.id}'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que solo hay productos de bebidas
        for producto in response.data:
            self.assertEqual(producto['categoria'], 'Bebidas')
    
    def test_filtrar_productos_con_oferta(self):
        """Test CA8: Filtrar productos que tienen oferta"""
        url = reverse('producto-ofertas-productos-con-ofertas') + '?estado_oferta=con_oferta'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todos tienen ofertas activas
        for producto in response.data:
            self.assertTrue(producto['tiene_ofertas_activas'])
    
    def test_filtrar_productos_sin_oferta(self):
        """Test CA8: Filtrar productos que NO tienen oferta"""
        url = reverse('producto-ofertas-productos-con-ofertas') + '?estado_oferta=sin_oferta'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que ninguno tiene ofertas activas
        for producto in response.data:
            self.assertFalse(producto['tiene_ofertas_activas'])


class VerProductosAsociadosOfertaTestCase(APITestCase):
    """Tests para CA9: Ver productos asociados a una oferta"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_asociados',
            password='admin123',
            email='admin_asociados@super.com',
            nombre_supermercado='Supermercado Asociados'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categoría y productos
        self.categoria = Categoria.objects.create(nombre='Alimentos')
        
        self.producto1 = Producto.objects.create(
            nombre='Producto 1',
            precio=Decimal('100.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        self.producto2 = Producto.objects.create(
            nombre='Producto 2',
            precio=Decimal('150.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        # Crear oferta
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Oferta Especial',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('20.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=7),
            activo=True
        )
        
        # Asignar productos a la oferta
        ProductoOferta.objects.create(
            producto=self.producto1,
            oferta=self.oferta,
            precio_original=self.producto1.precio
        )
        
        ProductoOferta.objects.create(
            producto=self.producto2,
            oferta=self.oferta,
            precio_original=self.producto2.precio
        )
    
    def test_ver_productos_asociados_a_oferta(self):
        """Test CA9: Ver qué productos están asociados a una oferta"""
        url = reverse('ofertas-productos', kwargs={'pk': self.oferta.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)
        
        # Verificar que contiene información de los productos
        productos_ids = [p['producto'] for p in response.data]
        self.assertIn(self.producto1.id, productos_ids)
        self.assertIn(self.producto2.id, productos_ids)
    
    def test_vista_detalle_oferta_muestra_productos(self):
        """Test CA9: La vista de detalle permite acceder a productos asociados"""
        # Primero obtener detalle de la oferta
        url_detalle = reverse('ofertas-detail', kwargs={'pk': self.oferta.id})
        response = self.client.get(url_detalle)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Luego verificar que se pueden obtener los productos asociados
        url_productos = reverse('ofertas-productos', kwargs={'pk': self.oferta.id})
        response_productos = self.client.get(url_productos)
        
        self.assertEqual(response_productos.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response_productos.data), 2)


class ValidacionAsignacionTestCase(APITestCase):
    """Tests adicionales para validaciones en asignación de ofertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_validacion',
            password='admin123',
            email='admin_validacion@super.com',
            nombre_supermercado='Supermercado Validacion'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Crear categoría y producto
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        
        self.producto = Producto.objects.create(
            nombre='Producto Test',
            precio=Decimal('100.00'),
            
            categoria=self.categoria,
            activo=True
        )
        
        # Crear oferta
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Oferta Test',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=5),
            activo=True
        )
    
    def test_no_asignar_productos_vacios(self):
        """Test: No se puede asignar sin seleccionar productos"""
        url = reverse('ofertas-asignar-productos', kwargs={'pk': self.oferta.id})
        data = {'productos_ids': []}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_no_duplicar_asignacion_misma_oferta(self):
        """Test: No se puede asignar la misma oferta dos veces al mismo producto"""
        # Primera asignación
        url = reverse('ofertas-asignar-productos', kwargs={'pk': self.oferta.id})
        data = {'productos_ids': [self.producto.id]}
        
        response1 = self.client.post(url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Segunda asignación (debería indicar que ya existe)
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verificar mensaje de error en la respuesta
        self.assertIn('errores', response2.data)
