"""
Tests para la Historia de Usuario: Gestión de Empleados

Como administrador quiero registrar a mis empleados, diferenciar roles, 
y definir en qué depósito trabaja cada empleado
"""

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from authentication.models import User, EmpleadoUser
from inventario.models import Deposito
import tempfile


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    MEDIA_ROOT=tempfile.gettempdir(),
)
class EmpleadoCreationTests(TestCase):
    """Tests para la creación de empleados"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        
        # Crear administrador
        self.admin_user = User.objects.create_user(
            username='admin_super',
            email='admin@super.com',
            password='AdminPass123!',
            nombre_supermercado='Mi Supermercado',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        # Crear depósito
        self.deposito = Deposito.objects.create(
            nombre='Depósito Central',
            direccion='Calle Principal 123',
            descripcion='Depósito principal',
            supermercado=self.admin_user
        )
        
        # Autenticar como admin
        self.client.force_authenticate(user=self.admin_user)
        self.url = reverse('empleado_list_create')
    
    def _valid_empleado_payload(self, **overrides):
        """Payload válido para crear un empleado"""
        data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan@test.com',
            'dni': '12345678',
            'puesto': 'CAJERO',
            'deposito': self.deposito.id,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        data.update(overrides)
        return data
    
    def test_CA1_crear_empleado_exitoso(self):
        """CA1: El administrador puede crear un nuevo empleado ingresando todos los datos correctamente"""
        payload = self._valid_empleado_payload()
        response = self.client.post(self.url, data=payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Juan')
        self.assertEqual(response.data['apellido'], 'Pérez')
        self.assertEqual(response.data['email'], 'juan@test.com')
        self.assertEqual(response.data['puesto'], 'CAJERO')
        
        # Verificar que el empleado se guardó en BD
        empleado = EmpleadoUser.objects.get(email='juan@test.com')
        self.assertEqual(empleado.supermercado, self.admin_user)
        self.assertEqual(empleado.deposito, self.deposito)
    
    def test_CA2_validar_campos_obligatorios(self):
        """CA2: El sistema valida que los campos obligatorios estén completos"""
        # Falta nombre
        payload = self._valid_empleado_payload(nombre='')
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', response.data)
    
    def test_CA2_validar_email_duplicado(self):
        """CA2: El sistema rechaza emails duplicados"""
        # Crear primer empleado
        payload1 = self._valid_empleado_payload(email='juan@test.com')
        response1 = self.client.post(self.url, data=payload1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Intentar crear otro con mismo email
        payload2 = self._valid_empleado_payload(
            email='juan@test.com',
            dni='87654321'
        )
        response2 = self.client.post(self.url, data=payload2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response2.data)
    
    def test_CA3_asignar_puesto_cajero(self):
        """CA3: El administrador puede asignar el puesto CAJERO"""
        payload = self._valid_empleado_payload(puesto='CAJERO')
        response = self.client.post(self.url, data=payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['puesto'], 'CAJERO')
        
        empleado = EmpleadoUser.objects.get(email='juan@test.com')
        self.assertEqual(empleado.puesto, 'CAJERO')
    
    def test_CA3_asignar_puesto_reponedor(self):
        """CA3: El administrador puede asignar el puesto REPONEDOR"""
        payload = self._valid_empleado_payload(puesto='REPONEDOR')
        response = self.client.post(self.url, data=payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['puesto'], 'REPONEDOR')
        
        empleado = EmpleadoUser.objects.get(email='juan@test.com')
        self.assertEqual(empleado.puesto, 'REPONEDOR')
    
    def test_CA5_asignar_deposito(self):
        """CA5: El administrador puede asignar un depósito al empleado"""
        payload = self._valid_empleado_payload(deposito=self.deposito.id)
        response = self.client.post(self.url, data=payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['deposito_id'], self.deposito.id)
        
        empleado = EmpleadoUser.objects.get(email='juan@test.com')
        self.assertEqual(empleado.deposito, self.deposito)
    
    def test_CA5_deposito_no_existe(self):
        """CA5: El sistema rechaza depósitos inexistentes"""
        payload = self._valid_empleado_payload(deposito=9999)
        response = self.client.post(self.url, data=payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('deposito', response.data)
    
    def test_validar_dni_formato(self):
        """Validación: El DNI debe tener 7-8 dígitos"""
        # DNI muy corto
        payload = self._valid_empleado_payload(dni='123456')
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('dni', response.data)
        
        # DNI muy largo
        payload = self._valid_empleado_payload(dni='123456789')
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_validar_contrasenas_coincidan(self):
        """Validación: Las contraseñas deben coincidir"""
        payload = self._valid_empleado_payload(password_confirm='OtraPass123!')
        response = self.client.post(self.url, data=payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    MEDIA_ROOT=tempfile.gettempdir(),
)
class EmpleadoListadoTests(TestCase):
    """Tests para listar empleados"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        
        # Crear dos supermercados
        self.admin1 = User.objects.create_user(
            username='admin1',
            email='admin1@super.com',
            password='AdminPass123!',
            nombre_supermercado='Super 1',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        self.admin2 = User.objects.create_user(
            username='admin2',
            email='admin2@super.com',
            password='AdminPass123!',
            nombre_supermercado='Super 2',
            cuil='20987654321',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        # Crear depósitos
        self.deposito1 = Deposito.objects.create(
            nombre='Depósito 1',
            direccion='Calle 1',
            supermercado=self.admin1
        )
        
        self.deposito2 = Deposito.objects.create(
            nombre='Depósito 2',
            direccion='Calle 2',
            supermercado=self.admin1
        )
        
        # Crear empleados para admin1
        self.emp1 = EmpleadoUser.objects.create_user(
            username='emp1',
            email='emp1@test.com',
            password='Pass123!',
            nombre='Juan',
            apellido='Pérez',
            dni='12345678',
            puesto='CAJERO',
            supermercado=self.admin1,
            deposito=self.deposito1
        )
        
        self.emp2 = EmpleadoUser.objects.create_user(
            username='emp2',
            email='emp2@test.com',
            password='Pass123!',
            nombre='María',
            apellido='González',
            dni='87654321',
            puesto='REPONEDOR',
            supermercado=self.admin1,
            deposito=self.deposito2
        )
        
        # Crear empleado para admin2 (no debe verse en listado de admin1)
        self.emp3 = EmpleadoUser.objects.create_user(
            username='emp3',
            email='emp3@test.com',
            password='Pass123!',
            nombre='Carlos',
            apellido='López',
            dni='11111111',
            puesto='CAJERO',
            supermercado=self.admin2,
            deposito=Deposito.objects.create(
                nombre='Depósito 3',
                direccion='Calle 3',
                supermercado=self.admin2
            )
        )
        
        self.url = reverse('empleado-list-create')
    
    def test_CA9_listar_empleados(self):
        """CA9: El administrador puede ver un listado con los empleados registrados"""
        self.client.force_authenticate(user=self.admin1)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Solo 2 empleados del admin1
    
    def test_CA9_listar_muestra_campos_requeridos(self):
        """CA9: El listado muestra nombre, rol, y depósito asignado"""
        self.client.force_authenticate(user=self.admin1)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        empleado = response.data[0]
        self.assertIn('nombre', empleado)
        self.assertIn('apellido', empleado)
        self.assertIn('puesto', empleado)
        self.assertIn('deposito', empleado)
        self.assertIn('nombre_completo', empleado)
    
    def test_listar_solo_empleados_propios(self):
        """El administrador solo ve sus propios empleados"""
        self.client.force_authenticate(user=self.admin1)
        response = self.client.get(self.url)
        
        # Admin1 solo debe ver sus 2 empleados
        self.assertEqual(len(response.data), 2)
        
        emails = [emp['email'] for emp in response.data]
        self.assertIn('emp1@test.com', emails)
        self.assertIn('emp2@test.com', emails)
        self.assertNotIn('emp3@test.com', emails)


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    MEDIA_ROOT=tempfile.gettempdir(),
)
class EmpleadoFiltradoTests(TestCase):
    """Tests para filtrado de empleados"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        
        # Crear supermercado
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@super.com',
            password='AdminPass123!',
            nombre_supermercado='Mi Super',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        # Crear depósitos
        self.deposito1 = Deposito.objects.create(
            nombre='Depósito 1',
            direccion='Calle 1',
            supermercado=self.admin
        )
        
        self.deposito2 = Deposito.objects.create(
            nombre='Depósito 2',
            direccion='Calle 2',
            supermercado=self.admin
        )
        
        # Crear empleados con diferentes puestos
        self.cajero1 = EmpleadoUser.objects.create_user(
            username='cajero1',
            email='cajero1@test.com',
            password='Pass123!',
            nombre='Juan',
            apellido='Pérez',
            dni='12345678',
            puesto='CAJERO',
            supermercado=self.admin,
            deposito=self.deposito1
        )
        
        self.cajero2 = EmpleadoUser.objects.create_user(
            username='cajero2',
            email='cajero2@test.com',
            password='Pass123!',
            nombre='Ana',
            apellido='García',
            dni='22222222',
            puesto='CAJERO',
            supermercado=self.admin,
            deposito=self.deposito2
        )
        
        self.reponedor1 = EmpleadoUser.objects.create_user(
            username='repo1',
            email='repo1@test.com',
            password='Pass123!',
            nombre='Carlos',
            apellido='López',
            dni='33333333',
            puesto='REPONEDOR',
            supermercado=self.admin,
            deposito=self.deposito1
        )
        
        self.reponedor2 = EmpleadoUser.objects.create_user(
            username='repo2',
            email='repo2@test.com',
            password='Pass123!',
            nombre='María',
            apellido='Rodríguez',
            dni='44444444',
            puesto='REPONEDOR',
            supermercado=self.admin,
            deposito=self.deposito2
        )
        
        self.client.force_authenticate(user=self.admin)
        self.url = reverse('empleado_list_create')
    
    def test_CA10_filtrar_por_rol_cajero(self):
        """CA10: Filtrar empleados por rol CAJERO"""
        response = self.client.get(self.url, {'puesto': 'CAJERO'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        for emp in response.data:
            self.assertEqual(emp['puesto'], 'CAJERO')
    
    def test_CA10_filtrar_por_rol_reponedor(self):
        """CA10: Filtrar empleados por rol REPONEDOR"""
        response = self.client.get(self.url, {'puesto': 'REPONEDOR'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        for emp in response.data:
            self.assertEqual(emp['puesto'], 'REPONEDOR')
    
    def test_CA10_filtrar_por_deposito(self):
        """CA10: Filtrar empleados por depósito"""
        response = self.client.get(self.url, {'deposito': self.deposito1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        for emp in response.data:
            self.assertEqual(emp['deposito'], self.deposito1.id)
    
    def test_CA10_filtrar_por_rol_y_deposito(self):
        """CA10: Filtrar empleados por rol y depósito simultáneamente"""
        response = self.client.get(self.url, {
            'puesto': 'CAJERO',
            'deposito': self.deposito1.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Juan')


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    MEDIA_ROOT=tempfile.gettempdir(),
)
class EmpleadoActualizacionTests(TestCase):
    """Tests para actualizar empleados"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        
        # Crear supermercado
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@super.com',
            password='AdminPass123!',
            nombre_supermercado='Mi Super',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        # Crear depósitos
        self.deposito1 = Deposito.objects.create(
            nombre='Depósito 1',
            direccion='Calle 1',
            supermercado=self.admin
        )
        
        self.deposito2 = Deposito.objects.create(
            nombre='Depósito 2',
            direccion='Calle 2',
            supermercado=self.admin
        )
        
        # Crear empleado
        self.empleado = EmpleadoUser.objects.create_user(
            username='emp1',
            email='emp1@test.com',
            password='Pass123!',
            nombre='Juan',
            apellido='Pérez',
            dni='12345678',
            puesto='CAJERO',
            supermercado=self.admin,
            deposito=self.deposito1
        )
        
        self.client.force_authenticate(user=self.admin)
        self.url = reverse('empleado_detail', kwargs={'pk': self.empleado.id})
    
    def test_CA7_modificar_datos_empleado(self):
        """CA7: El administrador puede modificar los datos de un empleado"""
        data = {
            'nombre': 'Juan',
            'apellido': 'García',
            'email': 'juan.garcia@test.com',
            'dni': '12345678',
            'puesto': 'CAJERO',
            'deposito': self.deposito1.id
        }
        
        response = self.client.put(self.url, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['apellido'], 'García')
        self.assertEqual(response.data['email'], 'juan.garcia@test.com')
    
    def test_CA7_modificar_rol(self):
        """CA7: El administrador puede modificar el rol del empleado"""
        data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'emp1@test.com',
            'dni': '12345678',
            'puesto': 'REPONEDOR',
            'deposito': self.deposito1.id
        }
        
        response = self.client.put(self.url, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puesto'], 'REPONEDOR')
        
        empleado = EmpleadoUser.objects.get(id=self.empleado.id)
        self.assertEqual(empleado.puesto, 'REPONEDOR')
    
    def test_CA7_modificar_deposito(self):
        """CA7: El administrador puede modificar el depósito asignado"""
        data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'emp1@test.com',
            'dni': '12345678',
            'puesto': 'CAJERO',
            'deposito': self.deposito2.id
        }
        
        response = self.client.put(self.url, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deposito'], self.deposito2.id)
        
        empleado = EmpleadoUser.objects.get(id=self.empleado.id)
        self.assertEqual(empleado.deposito, self.deposito2)


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    MEDIA_ROOT=tempfile.gettempdir(),
)
class EmpleadoEliminacionTests(TestCase):
    """Tests para eliminar empleados"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        
        # Crear supermercado
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@super.com',
            password='AdminPass123!',
            nombre_supermercado='Mi Super',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        # Crear depósito
        self.deposito = Deposito.objects.create(
            nombre='Depósito 1',
            direccion='Calle 1',
            supermercado=self.admin
        )
        
        # Crear empleado
        self.empleado = EmpleadoUser.objects.create_user(
            username='emp1',
            email='emp1@test.com',
            password='Pass123!',
            nombre='Juan',
            apellido='Pérez',
            dni='12345678',
            puesto='CAJERO',
            supermercado=self.admin,
            deposito=self.deposito
        )
        
        self.client.force_authenticate(user=self.admin)
        self.url = reverse('empleado_detail', kwargs={'pk': self.empleado.id})
    
    def test_CA8_eliminar_empleado(self):
        """CA8: El administrador puede eliminar un empleado del sistema"""
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que el empleado fue eliminado
        with self.assertRaises(EmpleadoUser.DoesNotExist):
            EmpleadoUser.objects.get(id=self.empleado.id)
