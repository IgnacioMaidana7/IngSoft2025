"""
Tests para la Historia de Usuario: ABM de Ofertas
Criterios de Aceptación:
1. Crear oferta con todos los campos requeridos
2. Validar campos obligatorios y fechas válidas
3. Editar oferta existente
4. No modificar ofertas expiradas
5. Eliminar oferta con confirmación
6. Listar ofertas con estado (activa, próxima, expirada)
7. Botones Editar, Activar/Desactivar, Eliminar
8. Filtrar por estado
9. Mensajes de confirmación al guardar
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


class OfertaCreacionTestCase(APITestCase):
    """Tests para creación de ofertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_ofertas',
            password='admin123',
            email='admin_ofertas@super.com',
            nombre_supermercado='Supermercado Ofertas'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_crear_oferta_porcentual(self):
        """Test CA1: Crear oferta con descuento porcentual"""
        url = reverse('ofertas-list')
        
        ahora = timezone.now()
        data = {
            'nombre': 'Descuento 20% Bebidas',
            'descripcion': 'Promoción en todas las bebidas',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '20.00',
            'fecha_inicio': (ahora + timedelta(days=1)).isoformat(),
            'fecha_fin': (ahora + timedelta(days=8)).isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Oferta creada correctamente.')
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['nombre'], 'Descuento 20% Bebidas')
    
    def test_crear_oferta_monto_fijo(self):
        """Test CA1: Crear oferta con monto fijo"""
        url = reverse('ofertas-list')
        
        ahora = timezone.now()
        data = {
            'nombre': '$50 de descuento',
            'descripcion': 'Descuento fijo de $50',
            'tipo_descuento': 'monto_fijo',
            'valor_descuento': '50.00',
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': (ahora + timedelta(days=5)).isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['tipo_descuento'], 'monto_fijo')
        self.assertEqual(Decimal(response.data['data']['valor_descuento']), Decimal('50.00'))
    
    def test_todos_los_campos_obligatorios(self):
        """Test CA1: Verificar que se ingresen todos los campos requeridos"""
        url = reverse('ofertas-list')
        
        # Crear oferta con todos los campos
        ahora = timezone.now()
        data = {
            'nombre': 'Oferta Completa',
            'descripcion': 'Con todos los campos',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '15.00',
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': (ahora + timedelta(days=7)).isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que los campos se guardaron
        oferta = Oferta.objects.get(id=response.data['data']['id'])
        self.assertEqual(oferta.nombre, 'Oferta Completa')
        self.assertEqual(oferta.tipo_descuento, 'porcentaje')
        self.assertEqual(oferta.valor_descuento, Decimal('15.00'))


class OfertaValidacionTestCase(APITestCase):
    """Tests para validaciones de ofertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_valid',
            password='admin123',
            email='admin_valid@super.com',
            nombre_supermercado='Super Valid'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_validar_campo_nombre_obligatorio(self):
        """Test CA2: El nombre es obligatorio"""
        url = reverse('ofertas-list')
        
        ahora = timezone.now()
        data = {
            # Sin nombre
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '10.00',
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': (ahora + timedelta(days=7)).isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', response.data)
    
    def test_validar_fecha_fin_posterior_a_inicio(self):
        """Test CA2: La fecha de fin debe ser posterior a la de inicio"""
        url = reverse('ofertas-list')
        
        ahora = timezone.now()
        data = {
            'nombre': 'Oferta Inválida',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '10.00',
            'fecha_inicio': (ahora + timedelta(days=7)).isoformat(),
            'fecha_fin': ahora.isoformat(),  # Anterior a inicio
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_fin', response.data)
    
    def test_validar_porcentaje_maximo_100(self):
        """Test CA2: El descuento porcentual no puede superar 100%"""
        url = reverse('ofertas-list')
        
        ahora = timezone.now()
        data = {
            'nombre': 'Descuento Imposible',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '150.00',  # Mayor a 100
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': (ahora + timedelta(days=7)).isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('valor_descuento', response.data)
    
    def test_validar_valor_positivo(self):
        """Test CA2: El valor del descuento debe ser positivo"""
        url = reverse('ofertas-list')
        
        ahora = timezone.now()
        data = {
            'nombre': 'Descuento Negativo',
            'tipo_descuento': 'monto_fijo',
            'valor_descuento': '-10.00',  # Negativo
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': (ahora + timedelta(days=7)).isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfertaEdicionTestCase(APITestCase):
    """Tests para edición de ofertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_edit',
            password='admin123',
            email='admin_edit@super.com',
            nombre_supermercado='Super Edit'
        )
        
        ahora = timezone.now()
        self.oferta_activa = Oferta.objects.create(
            nombre='Oferta Activa',
            descripcion='Oferta en curso',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=6),
            activo=True
        )
        
        self.oferta_proxima = Oferta.objects.create(
            nombre='Oferta Próxima',
            descripcion='Oferta futura',
            tipo_descuento='monto_fijo',
            valor_descuento=Decimal('100.00'),
            fecha_inicio=ahora + timedelta(days=3),
            fecha_fin=ahora + timedelta(days=10),
            activo=True
        )
        
        self.oferta_expirada = Oferta.objects.create(
            nombre='Oferta Expirada',
            descripcion='Oferta vencida',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('25.00'),
            fecha_inicio=ahora - timedelta(days=10),
            fecha_fin=ahora - timedelta(days=3),
            activo=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_editar_oferta_activa(self):
        """Test CA3: El admin puede editar una oferta activa"""
        url = reverse('ofertas-detail', kwargs={'pk': self.oferta_activa.id})
        
        data = {
            'nombre': 'Oferta Activa Modificada',
            'descripcion': 'Descripción actualizada',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '20.00',
            'fecha_inicio': self.oferta_activa.fecha_inicio.isoformat(),
            'fecha_fin': self.oferta_activa.fecha_fin.isoformat(),
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Oferta actualizada correctamente.')
        
        self.oferta_activa.refresh_from_db()
        self.assertEqual(self.oferta_activa.nombre, 'Oferta Activa Modificada')
        self.assertEqual(self.oferta_activa.valor_descuento, Decimal('20.00'))
    
    def test_editar_oferta_proxima(self):
        """Test CA3: El admin puede editar una oferta próxima"""
        url = reverse('ofertas-detail', kwargs={'pk': self.oferta_proxima.id})
        
        data = {
            'nombre': 'Oferta Futura Editada',
            'descripcion': self.oferta_proxima.descripcion,
            'tipo_descuento': self.oferta_proxima.tipo_descuento,
            'valor_descuento': '150.00',
            'fecha_inicio': self.oferta_proxima.fecha_inicio.isoformat(),
            'fecha_fin': self.oferta_proxima.fecha_fin.isoformat(),
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.oferta_proxima.refresh_from_db()
        self.assertEqual(self.oferta_proxima.valor_descuento, Decimal('150.00'))
    
    def test_no_editar_oferta_expirada(self):
        """Test CA4: No se puede modificar una oferta expirada"""
        url = reverse('ofertas-detail', kwargs={'pk': self.oferta_expirada.id})
        
        data = {
            'nombre': 'Intento de Edición',
            'descripcion': self.oferta_expirada.descripcion,
            'tipo_descuento': self.oferta_expirada.tipo_descuento,
            'valor_descuento': '30.00',
            'fecha_inicio': self.oferta_expirada.fecha_inicio.isoformat(),
            'fecha_fin': self.oferta_expirada.fecha_fin.isoformat(),
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('expirado', response.data['error'].lower())


class OfertaEliminacionTestCase(APITestCase):
    """Tests para eliminación de ofertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_del',
            password='admin123',
            email='admin_del@super.com',
            nombre_supermercado='Super Del'
        )
        
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Oferta a Eliminar',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=ahora,
            fecha_fin=ahora + timedelta(days=7)
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_eliminar_oferta(self):
        """Test CA5: El admin puede eliminar una oferta"""
        url = reverse('ofertas-detail', kwargs={'pk': self.oferta.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('eliminada', response.data['message'].lower())
        
        # Verificar que fue eliminada
        self.assertEqual(Oferta.objects.filter(id=self.oferta.id).count(), 0)
    
    def test_mensaje_confirmacion_eliminacion(self):
        """Test CA5: Mensaje de confirmación al eliminar"""
        url = reverse('ofertas-detail', kwargs={'pk': self.oferta.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Oferta eliminada correctamente.')


class OfertaListadoTestCase(APITestCase):
    """Tests para listado de ofertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_list',
            password='admin123',
            email='admin_list@super.com',
            nombre_supermercado='Super List'
        )
        
        ahora = timezone.now()
        
        # Crear ofertas en diferentes estados
        self.oferta_activa = Oferta.objects.create(
            nombre='Oferta Activa',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=6),
            activo=True
        )
        
        self.oferta_proxima = Oferta.objects.create(
            nombre='Oferta Próxima',
            tipo_descuento='monto_fijo',
            valor_descuento=Decimal('50.00'),
            fecha_inicio=ahora + timedelta(days=2),
            fecha_fin=ahora + timedelta(days=9),
            activo=True
        )
        
        self.oferta_expirada = Oferta.objects.create(
            nombre='Oferta Expirada',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('20.00'),
            fecha_inicio=ahora - timedelta(days=10),
            fecha_fin=ahora - timedelta(days=3),
            activo=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_listar_todas_ofertas(self):
        """Test CA6: Listar todas las ofertas registradas"""
        url = reverse('ofertas-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta está paginada
        self.assertIn('results', response.data)
        # Verificar que al menos están las 3 ofertas creadas
        self.assertGreaterEqual(len(response.data['results']), 3)
    
    def test_listado_muestra_campos_requeridos(self):
        """Test CA6: El listado muestra nombre, tipo, valor y estado"""
        url = reverse('ofertas-list')
        
        response = self.client.get(url)
        
        # Encontrar una de nuestras ofertas en results
        oferta_data = None
        for o in response.data['results']:
            if o['id'] == self.oferta_activa.id:
                oferta_data = o
                break
        
        self.assertIsNotNone(oferta_data)
        self.assertIn('nombre', oferta_data)
        self.assertIn('tipo_descuento', oferta_data)
        self.assertIn('valor_descuento', oferta_data)
        self.assertIn('estado', oferta_data)
    
    def test_estados_calculados_correctamente(self):
        """Test CA6: Los estados se calculan correctamente"""
        url = reverse('ofertas-list')
        
        response = self.client.get(url)
        
        # Buscar cada oferta en la respuesta (results)
        ofertas_dict = {o['id']: o for o in response.data['results']}
        
        self.assertIn(self.oferta_activa.id, ofertas_dict)
        self.assertEqual(ofertas_dict[self.oferta_activa.id]['estado'], 'activa')
        self.assertEqual(ofertas_dict[self.oferta_proxima.id]['estado'], 'proxima')
        self.assertEqual(ofertas_dict[self.oferta_expirada.id]['estado'], 'expirada')


class OfertaAccionesTestCase(APITestCase):
    """Tests para acciones en ofertas (botones)"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_acc',
            password='admin123',
            email='admin_acc@super.com',
            nombre_supermercado='Super Acc'
        )
        
        ahora = timezone.now()
        self.oferta = Oferta.objects.create(
            nombre='Oferta Test',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=ahora,
            fecha_fin=ahora + timedelta(days=7),
            activo=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_boton_editar_disponible(self):
        """Test CA7: Cada oferta tiene botón Editar (endpoint disponible)"""
        url = reverse('ofertas-detail', kwargs={'pk': self.oferta.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # El endpoint de edición está disponible
    
    def test_boton_activar_desactivar(self):
        """Test CA7: Botón Activar/Desactivar funciona"""
        url = reverse('ofertas-activar-desactivar', kwargs={'pk': self.oferta.id})
        
        # Desactivar
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertFalse(response.data['activo'])
        
        self.oferta.refresh_from_db()
        self.assertFalse(self.oferta.activo)
        
        # Activar
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['activo'])
        
        self.oferta.refresh_from_db()
        self.assertTrue(self.oferta.activo)
    
    def test_boton_eliminar_disponible(self):
        """Test CA7: Botón Eliminar funciona"""
        url = reverse('ofertas-detail', kwargs={'pk': self.oferta.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('eliminada', response.data['message'].lower())


class OfertaFiltradoTestCase(APITestCase):
    """Tests para filtrado de ofertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_filt',
            password='admin123',
            email='admin_filt@super.com',
            nombre_supermercado='Super Filt'
        )
        
        ahora = timezone.now()
        
        self.oferta_activa_1 = Oferta.objects.create(
            nombre='Activa 1',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(days=5),
            activo=True
        )
        
        self.oferta_activa_2 = Oferta.objects.create(
            nombre='Activa 2',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=ahora - timedelta(hours=2),
            fecha_fin=ahora + timedelta(days=3),
            activo=True
        )
        
        self.oferta_proxima = Oferta.objects.create(
            nombre='Próxima',
            tipo_descuento='monto_fijo',
            valor_descuento=Decimal('50.00'),
            fecha_inicio=ahora + timedelta(days=1),
            fecha_fin=ahora + timedelta(days=8),
            activo=True
        )
        
        self.oferta_expirada = Oferta.objects.create(
            nombre='Expirada',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('25.00'),
            fecha_inicio=ahora - timedelta(days=10),
            fecha_fin=ahora - timedelta(days=3),
            activo=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_filtrar_ofertas_activas(self):
        """Test CA8: Filtrar por ofertas activas"""
        url = reverse('ofertas-list') + '?estado=activa'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta está paginada
        results = response.data['results']
        # Debe haber al menos 2 activas
        self.assertGreaterEqual(len(results), 2)
        
        # Verificar que todas son activas
        for oferta in results:
            self.assertEqual(oferta['estado'], 'activa')
    
    def test_filtrar_ofertas_proximas(self):
        """Test CA8: Filtrar por ofertas próximas"""
        url = reverse('ofertas-list') + '?estado=proxima'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta está paginada
        results = response.data['results']
        # Debe haber al menos 1 próxima
        self.assertGreaterEqual(len(results), 1)
        
        # Verificar que todas son próximas
        for oferta in results:
            self.assertEqual(oferta['estado'], 'proxima')
    
    def test_filtrar_ofertas_expiradas(self):
        """Test CA8: Filtrar por ofertas expiradas"""
        url = reverse('ofertas-list') + '?estado=expirada'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta está paginada
        results = response.data['results']
        # Debe haber al menos 1 expirada
        self.assertGreaterEqual(len(results), 1)
        
        # Verificar que todas son expiradas
        for oferta in results:
            self.assertEqual(oferta['estado'], 'expirada')


class OfertaMensajesTestCase(APITestCase):
    """Tests para mensajes de confirmación"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_msg',
            password='admin123',
            email='admin_msg@super.com',
            nombre_supermercado='Super Msg'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_mensaje_confirmacion_crear(self):
        """Test CA9: Mensaje de confirmación al crear oferta"""
        url = reverse('ofertas-list')
        
        ahora = timezone.now()
        data = {
            'nombre': 'Nueva Oferta',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '10.00',
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': (ahora + timedelta(days=7)).isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Oferta creada correctamente.')
    
    def test_mensaje_confirmacion_editar(self):
        """Test CA9: Mensaje de confirmación al editar oferta"""
        ahora = timezone.now()
        oferta = Oferta.objects.create(
            nombre='Oferta Original',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=ahora,
            fecha_fin=ahora + timedelta(days=7)
        )
        
        url = reverse('ofertas-detail', kwargs={'pk': oferta.id})
        data = {
            'nombre': 'Oferta Modificada',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '15.00',
            'fecha_inicio': oferta.fecha_inicio.isoformat(),
            'fecha_fin': oferta.fecha_fin.isoformat(),
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Oferta actualizada correctamente.')


class OfertaAutenticacionTestCase(APITestCase):
    """Tests para autenticación y permisos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_auth_oferta',
            password='admin123',
            email='admin_auth_oferta@super.com',
            nombre_supermercado='Super Auth Oferta'
        )
        
        self.client = APIClient()
    
    def test_requiere_autenticacion(self):
        """Test: Se requiere autenticación para gestionar ofertas"""
        url = reverse('ofertas-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_admin_puede_crear_ofertas(self):
        """Test: Administradores pueden crear ofertas"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('ofertas-list')
        ahora = timezone.now()
        data = {
            'nombre': 'Oferta Admin',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '10.00',
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': (ahora + timedelta(days=7)).isoformat(),
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
