import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from inventario.models import Deposito, Transferencia, DetalleTransferencia, HistorialMovimiento
from productos.models import Categoria, Producto, ProductoDeposito
from empleados.models import Empleado
from authentication.models import EmpleadoUser
from notificaciones.models import Notificacion

User = get_user_model()


def create_test_admin(username='admin_test', email='admin@test.com', nombre='Supermercado Test', cuil='20123456789'):
    """Helper function to create test admin users with required fields"""
    return User.objects.create_user(
        username=username,
        email=email,
        password='testpass123',
        nombre_supermercado=nombre,
        cuil=cuil,
        provincia='Buenos Aires',
        localidad='La Plata'
    )


class TestTransferenciaModels(TestCase):
    """Tests para los modelos relacionados con transferencias"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear administrador
        self.admin = create_test_admin()
        
        # Crear depósitos
        self.deposito_origen = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Av. Principal 123',
            descripcion='Depósito principal',
            supermercado=self.admin
        )
        
        self.deposito_destino = Deposito.objects.create(
            nombre='Sucursal Norte',
            direccion='Calle Norte 456',
            descripcion='Sucursal zona norte',
            supermercado=self.admin
        )
        
        # Crear categoría y producto
        self.categoria = Categoria.objects.create(
            nombre='Alimentos',
            descripcion='Productos alimenticios'
        )
        
        self.producto = Producto.objects.create(
            nombre='Arroz Integral',
            categoria=self.categoria,
            precio=Decimal('150.50'),
            descripcion='Arroz integral 1kg'
        )
        
        # Crear stock en depósito origen
        self.stock_origen = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito_origen,
            cantidad=100,
            cantidad_minima=10
        )
    
    def test_crear_deposito_valido(self):
        """Test crear depósito con datos válidos"""
        deposito = Deposito.objects.create(
            nombre='Nuevo Depósito',
            direccion='Nueva Dirección 789',
            descripcion='Descripción del nuevo depósito',
            supermercado=self.admin
        )
        
        self.assertEqual(deposito.nombre, 'Nuevo Depósito')
        self.assertEqual(deposito.direccion, 'Nueva Dirección 789')
        self.assertTrue(deposito.activo)
        self.assertEqual(deposito.supermercado, self.admin)
        self.assertIsNotNone(deposito.fecha_creacion)
    
    def test_deposito_nombre_unico_por_supermercado(self):
        """Test que el nombre del depósito sea único por supermercado"""
        # Crear otro admin
        admin2 = create_test_admin(
            username='admin2',
            email='admin2@test.com',
            nombre='Otro Supermercado',
            cuil='20987654321'
        )
        
        # Debe permitir mismo nombre en diferente supermercado
        deposito2 = Deposito.objects.create(
            nombre='Depósito Central',  # Mismo nombre
            direccion='Otra dirección',
            supermercado=admin2
        )
        
        self.assertEqual(deposito2.nombre, 'Depósito Central')
        self.assertNotEqual(deposito2.supermercado, self.admin)
    
    def test_crear_transferencia_valida(self):
        """Test crear transferencia con datos válidos"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin,
            observaciones='Transferencia de prueba'
        )
        
        self.assertEqual(transferencia.deposito_origen, self.deposito_origen)
        self.assertEqual(transferencia.deposito_destino, self.deposito_destino)
        self.assertEqual(transferencia.administrador, self.admin)
        self.assertEqual(transferencia.estado, 'PENDIENTE')
        self.assertIsNotNone(transferencia.fecha_transferencia)
    
    def test_transferencia_mismo_deposito_origen_destino(self):
        """Test que no se pueda transferir al mismo depósito"""
        with self.assertRaises(ValidationError):
            transferencia = Transferencia(
                deposito_origen=self.deposito_origen,
                deposito_destino=self.deposito_origen,  # Mismo depósito
                administrador=self.admin
            )
            transferencia.clean()
    
    def test_transferencia_depositos_diferente_supermercado(self):
        """Test que los depósitos deben pertenecer al mismo supermercado"""
        # Crear otro admin y depósito
        admin2 = create_test_admin(
            username='admin2',
            email='admin2@test.com',
            nombre='Otro Supermercado',
            cuil='20987654321'
        )
        
        deposito_otro = Deposito.objects.create(
            nombre='Depósito Otro',
            direccion='Dirección Otro',
            supermercado=admin2
        )
        
        with self.assertRaises(ValidationError):
            transferencia = Transferencia(
                deposito_origen=self.deposito_origen,
                deposito_destino=deposito_otro,  # Diferente supermercado
                administrador=self.admin
            )
            transferencia.clean()
    
    def test_crear_detalle_transferencia_valido(self):
        """Test crear detalle de transferencia válido"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        
        detalle = DetalleTransferencia.objects.create(
            transferencia=transferencia,
            producto=self.producto,
            cantidad=50
        )
        
        self.assertEqual(detalle.transferencia, transferencia)
        self.assertEqual(detalle.producto, self.producto)
        self.assertEqual(detalle.cantidad, 50)
    
    def test_detalle_transferencia_cantidad_negativa(self):
        """Test que la cantidad no puede ser negativa o cero"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        
        with self.assertRaises(ValidationError):
            detalle = DetalleTransferencia(
                transferencia=transferencia,
                producto=self.producto,
                cantidad=0  # Cantidad inválida
            )
            detalle.clean()
        
        with self.assertRaises(ValidationError):
            detalle = DetalleTransferencia(
                transferencia=transferencia,
                producto=self.producto,
                cantidad=-10  # Cantidad negativa
            )
            detalle.clean()
    
    def test_detalle_transferencia_stock_insuficiente(self):
        """Test validación de stock insuficiente"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        
        with self.assertRaises(ValidationError):
            detalle = DetalleTransferencia(
                transferencia=transferencia,
                producto=self.producto,
                cantidad=150  # Más que el stock disponible (100)
            )
            detalle.clean()
    
    def test_detalle_transferencia_producto_no_existe_en_deposito(self):
        """Test validación cuando el producto no existe en el depósito origen"""
        # Crear producto sin stock en origen
        producto_sin_stock = Producto.objects.create(
            nombre='Producto Sin Stock',
            categoria=self.categoria,
            precio=Decimal('100.00')
        )
        
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        
        with self.assertRaises(ValidationError):
            detalle = DetalleTransferencia(
                transferencia=transferencia,
                producto=producto_sin_stock,
                cantidad=10
            )
            detalle.clean()
    
    def test_detalle_unico_por_producto_transferencia(self):
        """Test que no se puede duplicar producto en una transferencia"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        
        # Crear primer detalle
        DetalleTransferencia.objects.create(
            transferencia=transferencia,
            producto=self.producto,
            cantidad=30
        )
        
        # Intentar crear segundo detalle con mismo producto
        with self.assertRaises(IntegrityError):
            DetalleTransferencia.objects.create(
                transferencia=transferencia,
                producto=self.producto,  # Mismo producto
                cantidad=20
            )
    
    def test_crear_historial_movimiento(self):
        """Test crear registro de historial de movimiento"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        
        detalle = DetalleTransferencia.objects.create(
            transferencia=transferencia,
            producto=self.producto,
            cantidad=25
        )
        
        movimiento = HistorialMovimiento.objects.create(
            fecha=timezone.now(),
            tipo_movimiento='TRANSFERENCIA',
            producto=self.producto,
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            cantidad=25,
            transferencia=transferencia,
            detalle_transferencia=detalle,
            administrador=self.admin,
            observaciones='Movimiento de prueba'
        )
        
        self.assertEqual(movimiento.tipo_movimiento, 'TRANSFERENCIA')
        self.assertEqual(movimiento.producto, self.producto)
        self.assertEqual(movimiento.cantidad, 25)
        self.assertEqual(movimiento.transferencia, transferencia)
        self.assertEqual(movimiento.detalle_transferencia, detalle)
    
    def test_string_representations(self):
        """Test métodos __str__ de los modelos"""
        # Test Deposito
        deposito_str = str(self.deposito_origen)
        self.assertIn('Depósito Central', deposito_str)
        self.assertIn('Supermercado Test', deposito_str)
        
        # Test Transferencia
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        transferencia_str = str(transferencia)
        self.assertIn('Depósito Central', transferencia_str)
        self.assertIn('Sucursal Norte', transferencia_str)
        
        # Test DetalleTransferencia
        detalle = DetalleTransferencia.objects.create(
            transferencia=transferencia,
            producto=self.producto,
            cantidad=10
        )
        detalle_str = str(detalle)
        self.assertIn('Arroz Integral', detalle_str)
        self.assertIn('10', detalle_str)
        
        # Test HistorialMovimiento
        movimiento = HistorialMovimiento.objects.create(
            tipo_movimiento='TRANSFERENCIA',
            producto=self.producto,
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            cantidad=10,
            administrador=self.admin
        )
        movimiento_str = str(movimiento)
        self.assertIn('Transferencia entre depósitos', movimiento_str)
        self.assertIn('Arroz Integral', movimiento_str)


class TestTransferenciaBusinessLogic(TestCase):
    """Tests para la lógica de negocio de transferencias"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear administrador
        self.admin = create_test_admin()
        
        # Crear depósitos
        self.deposito_origen = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Av. Principal 123',
            supermercado=self.admin
        )
        
        self.deposito_destino = Deposito.objects.create(
            nombre='Sucursal Norte',
            direccion='Calle Norte 456',
            supermercado=self.admin
        )
        
        # Crear empleados reponedores
        self.empleado_origen = Empleado.objects.create(
            nombre='Juan',
            apellido='Pérez',
            email='juan.perez@test.com',
            dni='12345678',
            puesto='REPONEDOR',
            deposito=self.deposito_origen,
            supermercado=self.admin
        )
        
        self.empleado_destino = Empleado.objects.create(
            nombre='María',
            apellido='González',
            email='maria.gonzalez@test.com',
            dni='87654321',
            puesto='REPONEDOR',
            deposito=self.deposito_destino,
            supermercado=self.admin
        )
        
        # Crear EmpleadoUsers
        self.empleado_user_origen = EmpleadoUser.objects.create_user(
            username='juan.perez',
            email='juan.perez@test.com',
            password='empleadopass123',
            nombre='Juan',
            apellido='Pérez',
            dni='12345678',
            puesto='REPONEDOR',
            supermercado=self.admin
        )
        
        self.empleado_user_destino = EmpleadoUser.objects.create_user(
            username='maria.gonzalez',
            email='maria.gonzalez@test.com',
            password='empleadopass123',
            nombre='María',
            apellido='González',
            dni='87654321',
            puesto='REPONEDOR',
            supermercado=self.admin
        )
        
        # Crear categoría y productos
        self.categoria = Categoria.objects.create(
            nombre='Alimentos',
            descripcion='Productos alimenticios'
        )
        
        self.producto1 = Producto.objects.create(
            nombre='Arroz Integral',
            categoria=self.categoria,
            precio=Decimal('150.50')
        )
        
        self.producto2 = Producto.objects.create(
            nombre='Fideos',
            categoria=self.categoria,
            precio=Decimal('89.90')
        )
        
        # Crear stock en origen
        self.stock_origen_1 = ProductoDeposito.objects.create(
            producto=self.producto1,
            deposito=self.deposito_origen,
            cantidad=100,
            cantidad_minima=10
        )
        
        self.stock_origen_2 = ProductoDeposito.objects.create(
            producto=self.producto2,
            deposito=self.deposito_origen,
            cantidad=50,
            cantidad_minima=5
        )
    
    def test_transferencia_multiple_productos(self):
        """Test transferencia con múltiples productos"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        
        # Agregar múltiples productos
        detalle1 = DetalleTransferencia.objects.create(
            transferencia=transferencia,
            producto=self.producto1,
            cantidad=30
        )
        
        detalle2 = DetalleTransferencia.objects.create(
            transferencia=transferencia,
            producto=self.producto2,
            cantidad=20
        )
        
        self.assertEqual(transferencia.detalles.count(), 2)
        self.assertEqual(detalle1.cantidad, 30)
        self.assertEqual(detalle2.cantidad, 20)
    
    def test_estados_transferencia(self):
        """Test cambios de estado de transferencia"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin
        )
        
        # Estado inicial
        self.assertEqual(transferencia.estado, 'PENDIENTE')
        
        # Cambiar a confirmada
        transferencia.estado = 'CONFIRMADA'
        transferencia.save()
        self.assertEqual(transferencia.estado, 'CONFIRMADA')
        
        # Cambiar a cancelada
        transferencia.estado = 'CANCELADA'
        transferencia.save()
        self.assertEqual(transferencia.estado, 'CANCELADA')
    
    def test_ordenamiento_transferencias(self):
        """Test ordenamiento de transferencias por fecha"""
        # Crear transferencias en diferentes fechas
        fecha_1 = timezone.now() - timedelta(days=2)
        fecha_2 = timezone.now() - timedelta(days=1)
        fecha_3 = timezone.now()
        
        transferencia_1 = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin,
            fecha_transferencia=fecha_1
        )
        
        transferencia_2 = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin,
            fecha_transferencia=fecha_2
        )
        
        transferencia_3 = Transferencia.objects.create(
            deposito_origen=self.deposito_origen,
            deposito_destino=self.deposito_destino,
            administrador=self.admin,
            fecha_transferencia=fecha_3
        )
        
        # Verificar orden (más reciente primero)
        transferencias = list(Transferencia.objects.all())
        self.assertEqual(transferencias[0], transferencia_3)
        self.assertEqual(transferencias[1], transferencia_2)
        self.assertEqual(transferencias[2], transferencia_1)
    
    def test_historial_movimiento_tipos(self):
        """Test diferentes tipos de movimientos en el historial"""
        tipos_movimiento = [
            'TRANSFERENCIA',
            'INGRESO',
            'EGRESO',
            'AJUSTE',
            'VENTA'
        ]
        
        for tipo in tipos_movimiento:
            movimiento = HistorialMovimiento.objects.create(
                tipo_movimiento=tipo,
                producto=self.producto1,
                deposito_origen=self.deposito_origen,
                cantidad=10,
                administrador=self.admin,
                observaciones=f'Prueba {tipo}'
            )
            self.assertEqual(movimiento.tipo_movimiento, tipo)
    
    def test_ordenamiento_historial_movimientos(self):
        """Test ordenamiento del historial por fecha"""
        # Crear movimientos en diferentes fechas
        fecha_1 = timezone.now() - timedelta(hours=2)
        fecha_2 = timezone.now() - timedelta(hours=1)
        fecha_3 = timezone.now()
        
        movimiento_1 = HistorialMovimiento.objects.create(
            fecha=fecha_1,
            tipo_movimiento='TRANSFERENCIA',
            producto=self.producto1,
            cantidad=10,
            administrador=self.admin
        )
        
        movimiento_2 = HistorialMovimiento.objects.create(
            fecha=fecha_2,
            tipo_movimiento='INGRESO',
            producto=self.producto1,
            cantidad=5,
            administrador=self.admin
        )
        
        movimiento_3 = HistorialMovimiento.objects.create(
            fecha=fecha_3,
            tipo_movimiento='EGRESO',
            producto=self.producto1,
            cantidad=3,
            administrador=self.admin
        )
        
        # Verificar orden (más reciente primero)
        movimientos = list(HistorialMovimiento.objects.all())
        self.assertEqual(movimientos[0], movimiento_3)
        self.assertEqual(movimientos[1], movimiento_2)
        self.assertEqual(movimientos[2], movimiento_1)


class TestTransferenciaConstraints(TestCase):
    """Tests para constraints y validaciones avanzadas"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.admin = create_test_admin()
        
        self.deposito = Deposito.objects.create(
            nombre='Depósito Test',
            direccion='Dirección Test',
            supermercado=self.admin
        )
        
        self.categoria = Categoria.objects.create(nombre='Test Categoria')
        self.producto = Producto.objects.create(
            nombre='Test Producto',
            categoria=self.categoria,
            precio=Decimal('100.00')
        )
    
    def test_deposito_unique_together(self):
        """Test constraint unique_together para depósitos"""
        # Crear segundo depósito con mismo nombre y dirección debe fallar
        with self.assertRaises(IntegrityError):
            Deposito.objects.create(
                nombre='Depósito Test',  # Mismo nombre
                direccion='Dirección Test',  # Misma dirección
                supermercado=self.admin  # Mismo supermercado
            )
    
    def test_producto_deposito_unique_together(self):
        """Test constraint unique_together para ProductoDeposito"""
        # Crear primer stock
        ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=50
        )
        
        # Intentar crear segundo stock para mismo producto-depósito
        with self.assertRaises(IntegrityError):
            ProductoDeposito.objects.create(
                producto=self.producto,  # Mismo producto
                deposito=self.deposito,  # Mismo depósito
                cantidad=30
            )
    
    def test_campos_requeridos_transferencia(self):
        """Test campos requeridos en Transferencia"""
        with self.assertRaises(IntegrityError):
            # Falta deposito_origen
            Transferencia.objects.create(
                deposito_destino=self.deposito,
                administrador=self.admin
            )
    
    def test_campos_requeridos_detalle_transferencia(self):
        """Test campos requeridos en DetalleTransferencia"""
        transferencia = Transferencia.objects.create(
            deposito_origen=self.deposito,
            deposito_destino=self.deposito,
            administrador=self.admin
        )
        
        with self.assertRaises(IntegrityError):
            # Falta producto
            DetalleTransferencia.objects.create(
                transferencia=transferencia,
                cantidad=10
            )
    
    def test_cantidad_positiva_producto_deposito(self):
        """Test que cantidad debe ser positiva en ProductoDeposito"""
        # Django no valida automáticamente PositiveIntegerField con 0,
        # pero nuestra lógica de negocio debería manejarlo
        stock = ProductoDeposito.objects.create(
            producto=self.producto,
            deposito=self.deposito,
            cantidad=0  # Técnicamente válido para PositiveIntegerField
        )
        self.assertEqual(stock.cantidad, 0)
        self.assertFalse(stock.tiene_stock())