from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import Empleado
from inventario.models import Deposito

User = get_user_model()


class EmpleadoModelTestCase(TestCase):
    """Tests para el modelo Empleado"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
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
            direccion='Calle 123, La Plata',
            supermercado=self.user
        )
        
        self.empleado_data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan.perez@test.com',
            'dni': '12345678',
            'puesto': 'CAJERO',
            'deposito': self.deposito,
            'supermercado': self.user
        }
    
    def test_crear_empleado_exitoso(self):
        """Test CA: El administrador puede crear un nuevo empleado con todos los campos obligatorios"""
        empleado = Empleado.objects.create(**self.empleado_data)
        
        self.assertEqual(empleado.nombre, 'Juan')
        self.assertEqual(empleado.apellido, 'Pérez')
        self.assertEqual(empleado.email, 'juan.perez@test.com')
        self.assertEqual(empleado.dni, '12345678')
        self.assertEqual(empleado.puesto, 'CAJERO')
        self.assertEqual(empleado.deposito, self.deposito)
        self.assertEqual(empleado.supermercado, self.user)
        self.assertTrue(empleado.activo)
    
    def test_validar_campos_obligatorios(self):
        """Test CA: El sistema valida que los campos obligatorios estén completos"""
        # Test nombre vacío
        with self.assertRaises(ValidationError):
            empleado = Empleado(
                nombre='',
                apellido='Pérez',
                email='test@test.com',
                dni='12345678',
                puesto='CAJERO',
                deposito=self.deposito,
                supermercado=self.user
            )
            empleado.full_clean()
        
        # Test apellido vacío
        with self.assertRaises(ValidationError):
            empleado = Empleado(
                nombre='Juan',
                apellido='',
                email='test@test.com',
                dni='12345678',
                puesto='CAJERO',
                deposito=self.deposito,
                supermercado=self.user
            )
            empleado.full_clean()
        
        # Test email vacío
        with self.assertRaises(ValidationError):
            empleado = Empleado(
                nombre='Juan',
                apellido='Pérez',
                email='',
                dni='12345678',
                puesto='CAJERO',
                deposito=self.deposito,
                supermercado=self.user
            )
            empleado.full_clean()
    
    def test_email_duplicado(self):
        """Test CA: El sistema valida que el correo no esté duplicado"""
        # Crear primer empleado
        Empleado.objects.create(**self.empleado_data)
        
        # Intentar crear segundo empleado con mismo email
        empleado_data_duplicado = self.empleado_data.copy()
        empleado_data_duplicado['nombre'] = 'María'
        empleado_data_duplicado['dni'] = '87654321'
        
        with self.assertRaises(ValidationError):
            empleado = Empleado(**empleado_data_duplicado)
            empleado.full_clean()
    
    def test_roles_disponibles(self):
        """Test CA: El sistema debe mostrar roles disponibles: Cajero y Reponedor"""
        roles_disponibles = [choice[0] for choice in Empleado.ROLES_CHOICES]
        
        self.assertIn('CAJERO', roles_disponibles)
        self.assertIn('REPONEDOR', roles_disponibles)
        self.assertEqual(len(roles_disponibles), 2)
    
    def test_asignar_rol_cajero(self):
        """Test CA: Al registrar empleado, se puede asignar puesto Cajero"""
        empleado_data = self.empleado_data.copy()
        empleado_data['puesto'] = 'CAJERO'
        
        empleado = Empleado.objects.create(**empleado_data)
        self.assertEqual(empleado.puesto, 'CAJERO')
    
    def test_asignar_rol_reponedor(self):
        """Test CA: Al registrar empleado, se puede asignar puesto Reponedor"""
        empleado_data = self.empleado_data.copy()
        empleado_data['puesto'] = 'REPONEDOR'
        
        empleado = Empleado.objects.create(**empleado_data)
        self.assertEqual(empleado.puesto, 'REPONEDOR')
    
    def test_asignar_deposito(self):
        """Test CA: El sistema permite seleccionar a qué depósito pertenece el empleado"""
        # Crear segundo depósito
        deposito2 = Deposito.objects.create(
            nombre='Depósito Norte',
            direccion='Avenida 456, La Plata',
            supermercado=self.user
        )
        
        empleado_data = self.empleado_data.copy()
        empleado_data['deposito'] = deposito2
        
        empleado = Empleado.objects.create(**empleado_data)
        self.assertEqual(empleado.deposito, deposito2)
    
    def test_validar_deposito_mismo_supermercado(self):
        """Test: El depósito debe pertenecer al mismo supermercado"""
        # Crear otro usuario y depósito
        otro_user = User.objects.create_user(
            username='otro_admin',
            email='otro@test.com',
            password='testpass123',
            nombre_supermercado='Otro Super',
            cuil='20987654321',
            provincia='Córdoba',
            localidad='Córdoba'
        )
        
        deposito_otro = Deposito.objects.create(
            nombre='Depósito Otro',
            direccion='Calle 789',
            supermercado=otro_user
        )
        
        empleado_data = self.empleado_data.copy()
        empleado_data['deposito'] = deposito_otro
        
        with self.assertRaises(ValidationError):
            empleado = Empleado(**empleado_data)
            empleado.full_clean()
    
    def test_dni_validacion(self):
        """Test: Validación de DNI"""
        # DNI válido de 8 dígitos
        empleado_data = self.empleado_data.copy()
        empleado_data['dni'] = '12345678'
        empleado = Empleado(**empleado_data)
        empleado.full_clean()  # No debe lanzar excepción
        
        # DNI válido de 7 dígitos
        empleado_data['dni'] = '1234567'
        empleado = Empleado(**empleado_data)
        empleado.full_clean()  # No debe lanzar excepción
        
        # DNI inválido - muy corto
        empleado_data['dni'] = '123456'
        with self.assertRaises(ValidationError):
            empleado = Empleado(**empleado_data)
            empleado.full_clean()
        
        # DNI inválido - muy largo
        empleado_data['dni'] = '123456789'
        with self.assertRaises(ValidationError):
            empleado = Empleado(**empleado_data)
            empleado.full_clean()
        
        # DNI inválido - contiene letras
        empleado_data['dni'] = '1234567a'
        with self.assertRaises(ValidationError):
            empleado = Empleado(**empleado_data)
            empleado.full_clean()
    
    def test_nombre_completo(self):
        """Test: Método get_nombre_completo"""
        empleado = Empleado.objects.create(**self.empleado_data)
        nombre_completo = empleado.get_nombre_completo()
        self.assertEqual(nombre_completo, 'Juan Pérez')
    
    def test_str_representation(self):
        """Test: Representación string del modelo"""
        empleado = Empleado.objects.create(**self.empleado_data)
        expected_str = f"Juan Pérez - CAJERO ({self.user.nombre_supermercado})"
        self.assertEqual(str(empleado), expected_str)


class EmpleadoAPITestCase(TransactionTestCase):
    """Tests para las vistas/API de empleados"""
    
    def setUp(self):
        """Configuración inicial para los tests de API"""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            nombre_supermercado='Supermercado Test',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        self.deposito1 = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Calle 123',
            supermercado=self.user
        )
        
        self.deposito2 = Deposito.objects.create(
            nombre='Depósito Norte',
            direccion='Avenida 456',
            supermercado=self.user
        )
        
        # Autenticar al usuario
        self.client.force_authenticate(user=self.user)
        
        # URLs
        self.empleados_url = reverse('empleados:empleado-list-create')
    
    def tearDown(self):
        """Limpiar datos después de cada test"""
        Empleado.objects.all().delete()
        Deposito.objects.all().delete()
        User.objects.all().delete()
    
    def _crear_empleados_prueba(self):
        """Método auxiliar para crear empleados de prueba"""
        self.empleado1 = Empleado.objects.create(
            nombre='Juan',
            apellido='Pérez',
            email='juan@test.com',
            dni='12345678',
            puesto='CAJERO',
            deposito=self.deposito1,
            supermercado=self.user
        )
        
        self.empleado2 = Empleado.objects.create(
            nombre='María',
            apellido='González',
            email='maria@test.com',
            dni='87654321',
            puesto='REPONEDOR',
            deposito=self.deposito2,
            supermercado=self.user
        )
    
    def _get_response_data(self, response):
        """Método auxiliar para obtener los datos de una respuesta que puede estar paginada"""
        if 'results' in response.data:
            return response.data['results']
        return response.data
    
    def test_crear_empleado_via_api(self):
        """Test CA: El administrador puede crear un nuevo empleado via API"""
        data = {
            'nombre': 'Carlos',
            'apellido': 'López',
            'email': 'carlos@test.com',
            'dni': '11111111',
            'puesto': 'CAJERO',
            'deposito': self.deposito1.id,
            'password': 'password123'
        }
        
        response = self.client.post(self.empleados_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Empleado.objects.filter(email='carlos@test.com').exists())
    
    def test_listar_empleados(self):
        """Test CA: El administrador puede ver un listado con los empleados registrados"""
        self._crear_empleados_prueba()
        
        response = self.client.get(self.empleados_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 2)
        
        # Verificar que se muestran los datos correctos
        empleados_emails = [emp['email'] for emp in empleados_data]
        self.assertIn('juan@test.com', empleados_emails)
        self.assertIn('maria@test.com', empleados_emails)
    
    def test_filtrar_por_rol(self):
        """Test CA: El listado puede ser filtrado por rol"""
        self._crear_empleados_prueba()
        
        # Filtrar por CAJERO
        response = self.client.get(self.empleados_url, {'puesto': 'CAJERO'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 1)
        self.assertEqual(empleados_data[0]['puesto'], 'CAJERO')
        self.assertEqual(empleados_data[0]['email'], 'juan@test.com')
        
        # Filtrar por REPONEDOR
        response = self.client.get(self.empleados_url, {'puesto': 'REPONEDOR'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 1)
        self.assertEqual(empleados_data[0]['puesto'], 'REPONEDOR')
        self.assertEqual(empleados_data[0]['email'], 'maria@test.com')
    
    def test_filtrar_por_deposito(self):
        """Test CA: El listado puede ser filtrado por depósito"""
        self._crear_empleados_prueba()
        
        # Filtrar por depósito 1
        response = self.client.get(self.empleados_url, {'deposito': self.deposito1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 1)
        self.assertEqual(empleados_data[0]['deposito'], self.deposito1.id)
        
        # Filtrar por depósito 2
        response = self.client.get(self.empleados_url, {'deposito': self.deposito2.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 1)
        self.assertEqual(empleados_data[0]['deposito'], self.deposito2.id)
    
    def test_editar_empleado(self):
        """Test CA: El administrador puede modificar los datos de un empleado"""
        self._crear_empleados_prueba()
        
        url = reverse('empleados:empleado-detail', kwargs={'pk': self.empleado1.pk})
        
        data = {
            'nombre': 'Juan Carlos',
            'apellido': 'Pérez',
            'email': 'juan@test.com',
            'dni': '12345678',
            'puesto': 'REPONEDOR',  # Cambiar rol
            'deposito': self.deposito2.id,  # Cambiar depósito
            'activo': True
        }
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se actualizó en la base de datos
        empleado_actualizado = Empleado.objects.get(pk=self.empleado1.pk)
        self.assertEqual(empleado_actualizado.nombre, 'Juan Carlos')
        self.assertEqual(empleado_actualizado.puesto, 'REPONEDOR')
        self.assertEqual(empleado_actualizado.deposito, self.deposito2)
    
    def test_eliminar_empleado(self):
        """Test CA: El administrador puede eliminar un empleado del sistema"""
        self._crear_empleados_prueba()
        
        url = reverse('empleados:empleado-detail', kwargs={'pk': self.empleado1.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Empleado.objects.filter(pk=self.empleado1.pk).exists())
    
    def test_obtener_empleado_detalle(self):
        """Test: Obtener detalles de un empleado específico"""
        self._crear_empleados_prueba()
        
        url = reverse('empleados:empleado-detail', kwargs={'pk': self.empleado1.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'juan@test.com')
        self.assertEqual(response.data['nombre'], 'Juan')
        self.assertEqual(response.data['puesto'], 'CAJERO')
    
    def test_buscar_empleados(self):
        """Test: Búsqueda de empleados por nombre, apellido, email o DNI"""
        self._crear_empleados_prueba()
        
        # Buscar por nombre
        response = self.client.get(self.empleados_url, {'search': 'Juan'})
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 1)
        self.assertEqual(empleados_data[0]['nombre'], 'Juan')
        
        # Buscar por apellido
        response = self.client.get(self.empleados_url, {'search': 'González'})
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 1)
        self.assertEqual(empleados_data[0]['apellido'], 'González')
        
        # Buscar por email
        response = self.client.get(self.empleados_url, {'search': 'maria@test.com'})
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 1)
        self.assertEqual(empleados_data[0]['email'], 'maria@test.com')
        
        # Buscar por DNI
        response = self.client.get(self.empleados_url, {'search': '12345678'})
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 1)
        self.assertEqual(empleados_data[0]['dni'], '12345678')
    
    def test_obtener_roles_disponibles(self):
        """Test CA: El sistema muestra una lista de roles disponibles"""
        url = reverse('empleados:roles-disponibles')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        roles = response.data['roles']
        self.assertEqual(len(roles), 2)
        
        valores_roles = [role['value'] for role in roles]
        self.assertIn('CAJERO', valores_roles)
        self.assertIn('REPONEDOR', valores_roles)
    
    def test_obtener_empleados_por_deposito(self):
        """Test: Obtener empleados de un depósito específico"""
        self._crear_empleados_prueba()
        
        url = reverse('empleados:empleados-por-deposito', kwargs={'deposito_id': self.deposito1.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['empleados']), 1)
        self.assertEqual(response.data['empleados'][0]['email'], 'juan@test.com')
    
    def test_cambiar_estado_empleado(self):
        """Test: Cambiar estado activo/inactivo de un empleado"""
        self._crear_empleados_prueba()
        
        url = reverse('empleados:cambiar-estado', kwargs={'pk': self.empleado1.pk})
        
        # El empleado inicialmente está activo
        self.assertTrue(self.empleado1.activo)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar que cambió el estado
        empleado_actualizado = Empleado.objects.get(pk=self.empleado1.pk)
        self.assertFalse(empleado_actualizado.activo)
    
    def test_estadisticas_empleados(self):
        """Test: Obtener estadísticas de empleados"""
        self._crear_empleados_prueba()
        
        url = reverse('empleados:estadisticas')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        data = response.data['data']
        self.assertEqual(data['total_empleados'], 2)
        self.assertEqual(data['empleados_activos'], 2)
        self.assertEqual(data['empleados_inactivos'], 0)
        
        # Verificar estadísticas por puesto
        puestos = {item['puesto']: item['total'] for item in data['empleados_por_puesto']}
        self.assertEqual(puestos['CAJERO'], 1)
        self.assertEqual(puestos['REPONEDOR'], 1)
    
    def test_validacion_email_duplicado_api(self):
        """Test CA: El sistema valida que el correo no esté duplicado via API"""
        # Crear un empleado primero
        self._crear_empleados_prueba()
        
        data = {
            'nombre': 'Otro',
            'apellido': 'Usuario',
            'email': 'juan@test.com',  # Email ya existe
            'dni': '99999999',
            'puesto': 'REPONEDOR',
            'deposito': self.deposito1.id,
            'password': 'password123'
        }
        
        response = self.client.post(self.empleados_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_autenticacion_requerida(self):
        """Test: La API requiere autenticación"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.empleados_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_empleados_solo_del_supermercado_autenticado(self):
        """Test: Solo se pueden ver empleados del supermercado autenticado"""
        # Crear empleados del supermercado autenticado
        self._crear_empleados_prueba()
        
        # Crear otro usuario y empleado
        otro_user = User.objects.create_user(
            username='otro_admin',
            email='otro@test.com',
            password='testpass123',
            nombre_supermercado='Otro Super',
            cuil='20987654321',
            provincia='Córdoba',
            localidad='Córdoba'
        )
        
        otro_deposito = Deposito.objects.create(
            nombre='Otro Depósito',
            direccion='Otra Calle 789',
            supermercado=otro_user
        )
        
        Empleado.objects.create(
            nombre='Pedro',
            apellido='Martínez',
            email='pedro@otro.com',
            dni='55555555',
            puesto='CAJERO',
            deposito=otro_deposito,
            supermercado=otro_user
        )
        
        # Con el usuario original autenticado, solo debe ver sus empleados
        response = self.client.get(self.empleados_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        empleados_data = self._get_response_data(response)
        self.assertEqual(len(empleados_data), 2)  # Solo los 2 empleados del user original
        
        emails = [emp['email'] for emp in empleados_data]
        self.assertNotIn('pedro@otro.com', emails)
