"""
Tests para la Historia de Usuario: Como cajero quiero realizar ventas

Criterios de aceptación a testear:
1. El cajero puede realizar una venta agregando los productos que el cliente quiere con su respectiva cantidad.
2. El cajero puede editar la cantidad (eliminar o agregar unidades) del producto elegido o eliminar el producto.
3. El cajero puede ingresar el número de teléfono del cliente, en caso de que él mismo quiera.
4. El sistema debe mostrar la lista con el precio unitario del producto y la cantidad y el total de la venta.
5. El sistema debe generar un pdf en formato de ticket y puede enviarlo al whatsapp del cliente.
6. Una vez finalizada la venta, se debe realizar el ajuste de stock y limpiar la pantalla de "Ventas" para realizar una nueva venta.
"""

import pytest
import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

# Importar modelos necesarios
from ventas.models import Venta, ItemVenta
from productos.models import Producto, Categoria, ProductoDeposito
from inventario.models import Deposito
from authentication.models import EmpleadoUser

User = get_user_model()


class VentasCajeroTestCase(TestCase):
    """
    Test case para la historia de usuario de ventas del cajero
    """
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        # Crear usuario admin (supermercado)
        self.admin_user = User.objects.create_user(
            username='admin_super',
            email='admin@supermercado.com',
            password='admin123',
            first_name='Admin',
            last_name='Supermercado',
            nombre_supermercado='Supermercado Test',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='CABA'
        )
        
        # Crear empleado cajero
        self.cajero = EmpleadoUser.objects.create_user(
            username='cajero001',
            email='cajero@supermercado.com',
            password='cajero123',
            nombre='Juan',
            apellido='Pérez',
            dni='12345678',
            supermercado=self.admin_user,
            puesto='CAJERO',
            is_active=True
        )
        
        # Crear depósito
        self.deposito = Deposito.objects.create(
            nombre='Depósito Principal',
            direccion='Calle Principal 123',
            supermercado=self.admin_user,
            activo=True
        )
        
        # Crear categoría
        self.categoria = Categoria.objects.create(
            nombre='Alimentos',
            descripcion='Productos alimenticios'
        )
        
        # Crear productos
        self.producto1 = Producto.objects.create(
            nombre='Arroz 1kg',
            categoria=self.categoria,
            precio=Decimal('2.50'),
            descripcion='Arroz grano largo',
            activo=True
        )
        
        self.producto2 = Producto.objects.create(
            nombre='Aceite 900ml',
            categoria=self.categoria,
            precio=Decimal('4.75'),
            descripcion='Aceite de girasol',
            activo=True
        )
        
        self.producto3 = Producto.objects.create(
            nombre='Pan integral',
            categoria=self.categoria,
            precio=Decimal('1.20'),
            descripcion='Pan integral artesanal',
            activo=True
        )
        
        # Crear stock para los productos
        self.stock1 = ProductoDeposito.objects.create(
            producto=self.producto1,
            deposito=self.deposito,
            cantidad=100,
            cantidad_minima=10
        )
        
        self.stock2 = ProductoDeposito.objects.create(
            producto=self.producto2,
            deposito=self.deposito,
            cantidad=50,
            cantidad_minima=5
        )
        
        self.stock3 = ProductoDeposito.objects.create(
            producto=self.producto3,
            deposito=self.deposito,
            cantidad=25,
            cantidad_minima=3
        )
        
        # Configurar cliente API
        self.client = APIClient()
        
    def test_cajero_puede_crear_venta_vacia(self):
        """
        Test: El cajero puede crear una nueva venta vacía
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta
        url = reverse('venta-list')
        data = {
            'observaciones': 'Venta de prueba'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['estado'], 'PENDIENTE')
        self.assertEqual(response.data['total'], '0.00')
        self.assertEqual(response.data['subtotal'], '0.00')
        self.assertIsNotNone(response.data['numero_venta'])
        
        # Verificar en base de datos
        venta = Venta.objects.get(id=response.data['id'])
        self.assertEqual(venta.cajero, self.admin_user)  # El cajero empleado está asociado al admin
        self.assertEqual(venta.empleado_cajero, self.cajero)
        self.assertEqual(venta.estado, 'PENDIENTE')
        
    def test_cajero_puede_agregar_producto_a_venta(self):
        """
        Test: El cajero puede agregar productos con cantidad a una venta
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        # Agregar producto a la venta
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        data = {
            'producto_id': self.producto1.id,
            'cantidad': 3
        }
        
        response = self.client.post(agregar_url, data, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('item', response.data)
        self.assertIn('venta', response.data)
        
        # Verificar datos del item
        item_data = response.data['item']
        self.assertEqual(item_data['cantidad'], 3)
        self.assertEqual(Decimal(item_data['precio_unitario']), self.producto1.precio)
        self.assertEqual(Decimal(item_data['subtotal']), Decimal('7.50'))  # 3 * 2.50
        
        # Verificar datos de la venta
        venta_data = response.data['venta']
        self.assertEqual(venta_data['estado'], 'PROCESANDO')
        self.assertEqual(Decimal(venta_data['subtotal']), Decimal('7.50'))
        self.assertEqual(Decimal(venta_data['total']), Decimal('7.50'))
        
    def test_cajero_puede_agregar_multiple_productos(self):
        """
        Test: El cajero puede agregar múltiples productos diferentes a una venta
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        # Agregar primer producto
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        response1 = self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 2
        }, format='json')
        
        # Agregar segundo producto
        response2 = self.client.post(agregar_url, {
            'producto_id': self.producto2.id,
            'cantidad': 1
        }, format='json')
        
        # Verificaciones
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verificar total de la venta
        venta_data = response2.data['venta']
        expected_total = (2 * self.producto1.precio) + (1 * self.producto2.precio)  # 5.00 + 4.75 = 9.75
        self.assertEqual(Decimal(venta_data['total']), expected_total)
        
        # Verificar que hay 2 items en la venta
        venta = Venta.objects.get(id=venta_id)
        self.assertEqual(venta.items.count(), 2)
        
    def test_cajero_puede_modificar_cantidad_producto(self):
        """
        Test: El cajero puede editar la cantidad de un producto en la venta
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar producto
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        agregar_response = self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 2
        }, format='json')
        
        item_id = agregar_response.data['item']['id']
        
        # Modificar cantidad del item
        actualizar_url = reverse('venta-actualizar-item', kwargs={'pk': venta_id})
        data = {
            'item_id': item_id,
            'cantidad': 5
        }
        
        response = self.client.patch(actualizar_url, data, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar nueva cantidad y subtotal
        item_data = response.data['item']
        self.assertEqual(item_data['cantidad'], 5)
        self.assertEqual(Decimal(item_data['subtotal']), Decimal('12.50'))  # 5 * 2.50
        
        # Verificar total actualizado de la venta
        venta_data = response.data['venta']
        self.assertEqual(Decimal(venta_data['total']), Decimal('12.50'))
        
    def test_cajero_puede_eliminar_producto_de_venta(self):
        """
        Test: El cajero puede eliminar un producto de la venta
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar productos
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        
        # Agregar producto 1
        response1 = self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 2
        }, format='json')
        
        # Agregar producto 2
        response2 = self.client.post(agregar_url, {
            'producto_id': self.producto2.id,
            'cantidad': 1
        }, format='json')
        
        item_id = response1.data['item']['id']
        
        # Eliminar primer producto
        eliminar_url = reverse('venta-eliminar-item', kwargs={'pk': venta_id})
        data = {'item_id': item_id}
        
        response = self.client.delete(eliminar_url, data, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el total solo incluye el producto 2
        venta_data = response.data['venta']
        self.assertEqual(Decimal(venta_data['total']), self.producto2.precio)
        
        # Verificar en base de datos
        venta = Venta.objects.get(id=venta_id)
        self.assertEqual(venta.items.count(), 1)
        self.assertFalse(venta.items.filter(id=item_id).exists())
        
    def test_cajero_puede_agregar_telefono_cliente(self):
        """
        Test: El cajero puede ingresar el número de teléfono del cliente
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar producto
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 1
        }, format='json')
        
        # Finalizar venta con teléfono del cliente
        finalizar_url = reverse('venta-finalizar', kwargs={'pk': venta_id})
        data = {
            'cliente_telefono': '+5491123456789',
            'observaciones': 'Cliente frecuente'
        }
        
        response = self.client.post(finalizar_url, data, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar en base de datos
        venta = Venta.objects.get(id=venta_id)
        self.assertEqual(venta.cliente_telefono, '+5491123456789')
        self.assertEqual(venta.observaciones, 'Cliente frecuente')
        self.assertEqual(venta.estado, 'COMPLETADA')
        
    def test_sistema_muestra_precio_unitario_cantidad_y_total(self):
        """
        Test: El sistema debe mostrar la lista con el precio unitario del producto, 
        la cantidad y el total de la venta
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar productos
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        
        # Agregar productos con diferentes cantidades
        self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 3
        }, format='json')
        
        self.client.post(agregar_url, {
            'producto_id': self.producto2.id,
            'cantidad': 2
        }, format='json')
        
        # Obtener detalles de la venta
        detalle_url = reverse('venta-detail', kwargs={'pk': venta_id})
        response = self.client.get(detalle_url)
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        venta_data = response.data
        
        # Verificar que contiene items
        self.assertIn('items', venta_data)
        self.assertEqual(len(venta_data['items']), 2)
        
        # Verificar primer item
        item1 = venta_data['items'][0]
        self.assertIn('precio_unitario', item1)
        self.assertIn('cantidad', item1)
        self.assertIn('subtotal', item1)
        self.assertIn('producto', item1)
        
        # Verificar cálculos
        expected_subtotal = Decimal('7.50')  # 3 * 2.50
        expected_total = Decimal('17.00')  # (3 * 2.50) + (2 * 4.75)
        
        self.assertEqual(Decimal(venta_data['subtotal']), expected_total)
        self.assertEqual(Decimal(venta_data['total']), expected_total)
        
    def test_finalizar_venta_ajusta_stock(self):
        """
        Test: Una vez finalizada la venta, se debe realizar el ajuste de stock
        """
        # Verificar stock inicial
        stock_inicial_1 = self.stock1.cantidad
        stock_inicial_2 = self.stock2.cantidad
        
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar productos
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        
        # Agregar productos
        self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 5
        }, format='json')
        
        self.client.post(agregar_url, {
            'producto_id': self.producto2.id,
            'cantidad': 3
        }, format='json')
        
        # Finalizar venta
        finalizar_url = reverse('venta-finalizar', kwargs={'pk': venta_id})
        response = self.client.post(finalizar_url, {}, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar ajuste de stock
        self.stock1.refresh_from_db()
        self.stock2.refresh_from_db()
        
        self.assertEqual(self.stock1.cantidad, stock_inicial_1 - 5)
        self.assertEqual(self.stock2.cantidad, stock_inicial_2 - 3)
        
        # Verificar estado de la venta
        venta = Venta.objects.get(id=venta_id)
        self.assertEqual(venta.estado, 'COMPLETADA')
        self.assertIsNotNone(venta.fecha_completada)
        
    def test_no_se_puede_finalizar_venta_sin_stock_suficiente(self):
        """
        Test: No se puede finalizar una venta si no hay stock suficiente
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar producto con cantidad mayor al stock
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': self.stock1.cantidad + 10  # Más del stock disponible
        }, format='json')
        
        # Intentar finalizar venta
        finalizar_url = reverse('venta-finalizar', kwargs={'pk': venta_id})
        response = self.client.post(finalizar_url, {}, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Stock insuficiente', response.data['error'])
        
        # Verificar que la venta no se completó
        venta = Venta.objects.get(id=venta_id)
        self.assertNotEqual(venta.estado, 'COMPLETADA')
        
    def test_no_se_puede_finalizar_venta_vacia(self):
        """
        Test: No se puede finalizar una venta sin productos
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta vacía
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        # Intentar finalizar venta vacía
        finalizar_url = reverse('venta-finalizar', kwargs={'pk': venta_id})
        response = self.client.post(finalizar_url, {}, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('sin productos', response.data['error'])
        
    def test_cajero_puede_cancelar_venta(self):
        """
        Test: El cajero puede cancelar una venta
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar producto
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 2
        }, format='json')
        
        # Cancelar venta
        cancelar_url = reverse('venta-cancelar', kwargs={'pk': venta_id})
        response = self.client.post(cancelar_url, {}, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estado de la venta
        venta = Venta.objects.get(id=venta_id)
        self.assertEqual(venta.estado, 'CANCELADA')
        
    def test_no_se_puede_modificar_venta_completada(self):
        """
        Test: No se pueden modificar ventas completadas
        """
        # Crear y completar venta
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar producto
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        agregar_response = self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 2
        }, format='json')
        
        # Finalizar venta
        finalizar_url = reverse('venta-finalizar', kwargs={'pk': venta_id})
        self.client.post(finalizar_url, {}, format='json')
        
        # Intentar agregar producto a venta completada
        response = self.client.post(agregar_url, {
            'producto_id': self.producto2.id,
            'cantidad': 1
        }, format='json')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('completada', response.data['error'])
        
    def test_obtener_productos_disponibles(self):
        """
        Test: El cajero puede obtener la lista de productos disponibles
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Obtener productos disponibles
        url = reverse('productos-disponibles')
        response = self.client.get(url)
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        # Verificar estructura de datos
        producto_data = response.data[0]
        self.assertIn('id', producto_data)
        self.assertIn('nombre', producto_data)
        self.assertIn('precio', producto_data)
        self.assertIn('stock_disponible', producto_data)
        self.assertIn('categoria', producto_data)
        
    def test_buscar_productos(self):
        """
        Test: El cajero puede buscar productos por nombre
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Buscar productos
        url = reverse('buscar-productos')
        response = self.client.get(url, {'q': 'Arroz'})
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Verificar que encuentra el producto correcto
        found = False
        for producto in response.data:
            if 'Arroz' in producto['nombre']:
                found = True
                break
        self.assertTrue(found)
        
        # Test búsqueda muy corta
        response_short = self.client.get(url, {'q': 'A'})
        self.assertEqual(response_short.status_code, status.HTTP_400_BAD_REQUEST)
        
    @pytest.mark.skipif(True, reason="PDF generation requiere ReportLab configurado")
    def test_generar_ticket_pdf(self):
        """
        Test: El sistema debe generar un PDF en formato de ticket
        Nota: Este test está marcado como skip porque requiere configuración adicional de ReportLab
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta completa
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        self.client.post(agregar_url, {
            'producto_id': self.producto1.id,
            'cantidad': 2
        }, format='json')
        
        # Finalizar venta
        finalizar_url = reverse('venta-finalizar', kwargs={'pk': venta_id})
        finalizar_response = self.client.post(finalizar_url, {}, format='json')
        
        # Verificar que se marcó el PDF como generado
        venta = Venta.objects.get(id=venta_id)
        self.assertTrue(venta.ticket_pdf_generado)
        
        # Descargar ticket
        ticket_url = reverse('venta-descargar-ticket', kwargs={'pk': venta_id})
        response = self.client.get(ticket_url)
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
    def test_permisos_cajero(self):
        """
        Test: Verificar que solo usuarios con permisos de cajero pueden acceder
        """
        # Crear usuario sin permisos (otro supermercado)
        user_sin_permisos = User.objects.create_user(
            username='otro_super',
            email='otro@supermercado.com',
            password='cliente123',
            nombre_supermercado='Otro Supermercado',
            cuil='20987654321',
            provincia='Córdoba',
            localidad='Córdoba Capital'
        )
        
        # Intentar acceder sin autenticación
        url = reverse('venta-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Intentar acceder con usuario sin permisos
        self.client.force_authenticate(user=user_sin_permisos)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Acceder con cajero (debe funcionar)
        self.client.force_authenticate(user=self.cajero)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_venta_genera_numero_unico(self):
        """
        Test: Verificar que cada venta genera un número único
        """
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear múltiples ventas
        url = reverse('venta-list')
        response1 = self.client.post(url, {}, format='json')
        response2 = self.client.post(url, {}, format='json')
        response3 = self.client.post(url, {}, format='json')
        
        # Verificar que todas tienen números únicos
        num1 = response1.data['numero_venta']
        num2 = response2.data['numero_venta']
        num3 = response3.data['numero_venta']
        
        self.assertNotEqual(num1, num2)
        self.assertNotEqual(num2, num3)
        self.assertNotEqual(num1, num3)
        
        # Verificar formato de número
        self.assertTrue(len(num1) > 8)  # YYYYMMDD + sufijo
        
    def test_calculos_decimales_precision(self):
        """
        Test: Verificar precisión en cálculos con decimales
        """
        # Crear producto con precio decimal
        producto_decimal = Producto.objects.create(
            nombre='Producto Decimal',
            categoria=self.categoria,
            precio=Decimal('3.33'),
            activo=True
        )
        
        ProductoDeposito.objects.create(
            producto=producto_decimal,
            deposito=self.deposito,
            cantidad=10
        )
        
        # Autenticar como cajero
        self.client.force_authenticate(user=self.cajero)
        
        # Crear venta y agregar producto
        venta_url = reverse('venta-list')
        venta_response = self.client.post(venta_url, {}, format='json')
        venta_id = venta_response.data['id']
        
        agregar_url = reverse('venta-agregar-producto', kwargs={'pk': venta_id})
        response = self.client.post(agregar_url, {
            'producto_id': producto_decimal.id,
            'cantidad': 3
        }, format='json')
        
        # Verificar cálculos precisos
        expected_subtotal = Decimal('9.99')  # 3 * 3.33
        item_data = response.data['item']
        venta_data = response.data['venta']
        
        self.assertEqual(Decimal(item_data['subtotal']), expected_subtotal)
        self.assertEqual(Decimal(venta_data['total']), expected_subtotal)

    def tearDown(self):
        """Limpiar después de cada test"""
        # Limpiar archivos de media de prueba si existen
        import os
        import shutil
        from django.conf import settings
        
        if hasattr(settings, 'MEDIA_ROOT') and os.path.exists(settings.MEDIA_ROOT):
            try:
                shutil.rmtree(settings.MEDIA_ROOT)
            except OSError:
                pass
