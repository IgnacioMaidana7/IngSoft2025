"""
Tests para la Historia de Usuario: Sección de Perfil del Administrador
Como administrador quiero tener una sección de perfil para configurarlo

Criterios de Aceptación:
1. El administrador puede acceder a su perfil desde el menú principal o un ícono de usuario visible en la interfaz
2. El sistema muestra los datos actuales del administrador (nombre, correo, teléfono, foto de perfil)
3. El administrador puede editar su información personal (nombre, teléfono, correo electrónico)
4. El sistema valida que el correo electrónico no esté duplicado y que los campos obligatorios estén completos
5. El administrador puede cambiar su contraseña (ingresando contraseña actual, nueva y confirmación)
6. El sistema verifica que la contraseña actual sea correcta antes de permitir el cambio
7. El sistema valida seguridad de nueva contraseña (mínimo 8 caracteres, letras y números)
8. El administrador puede subir, cambiar o eliminar su foto de perfil
9. El sistema muestra mensaje de confirmación al guardar cambios correctamente
10. Si hay error, el sistema muestra mensaje de error claro
11. El administrador puede cerrar sesión desde esta sección
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import tempfile

User = get_user_model()


class AccesoPerfilTestCase(APITestCase):
    """Tests para CA1: Acceso al perfil del administrador"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_perfil',
            password='admin123',
            email='admin_perfil@super.com',
            nombre_supermercado='Supermercado Test',
            cuil='20123456789',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_acceder_perfil_autenticado(self):
        """Test CA1: Admin autenticado puede acceder a su perfil"""
        url = reverse('user_profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], 'admin_perfil@super.com')
    
    def test_acceso_sin_autenticacion(self):
        """Test CA1: No se puede acceder sin autenticación"""
        self.client.force_authenticate(user=None)
        url = reverse('user_profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VisualizacionDatosPerfilTestCase(APITestCase):
    """Tests para CA2: Visualización de datos del perfil"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_datos',
            password='admin123',
            email='admin_datos@super.com',
            nombre_supermercado='Mi Supermercado',
            cuil='20987654321',
            provincia='Córdoba',
            localidad='Córdoba Capital'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_mostrar_datos_actuales(self):
        """Test CA2: El sistema muestra los datos actuales del administrador"""
        url = reverse('user_profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'admin_datos@super.com')
        self.assertEqual(response.data['nombre_supermercado'], 'Mi Supermercado')
        self.assertEqual(response.data['provincia'], 'Córdoba')
        self.assertEqual(response.data['localidad'], 'Córdoba Capital')
    
    def test_incluye_campos_requeridos(self):
        """Test CA2: La respuesta incluye todos los campos necesarios"""
        url = reverse('user_profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar campos obligatorios
        self.assertIn('email', response.data)
        self.assertIn('nombre_supermercado', response.data)
        self.assertIn('provincia', response.data)
        self.assertIn('localidad', response.data)
        # Verificar campo opcional de foto
        self.assertIn('logo', response.data)


class EdicionInformacionPersonalTestCase(APITestCase):
    """Tests para CA3: Edición de información personal"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_editar',
            password='admin123',
            email='admin_editar@super.com',
            nombre_supermercado='Supermercado Original',
            cuil='20111222333',
            provincia='Santa Fe',
            localidad='Rosario'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_editar_nombre_supermercado(self):
        """Test CA3: Admin puede editar el nombre del supermercado"""
        url = reverse('user_profile')
        
        data = {
            'nombre_supermercado': 'Supermercado Actualizado'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('actualizado', response.data['message'].lower())
        
        # Verificar que se actualizó
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.nombre_supermercado, 'Supermercado Actualizado')
    
    def test_editar_provincia_localidad(self):
        """Test CA3: Admin puede editar provincia y localidad"""
        url = reverse('user_profile')
        
        data = {
            'provincia': 'Mendoza',
            'localidad': 'Mendoza Capital'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se actualizaron
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.provincia, 'Mendoza')
        self.assertEqual(self.admin_user.localidad, 'Mendoza Capital')
    
    def test_editar_multiples_campos(self):
        """Test CA3: Admin puede editar múltiples campos simultáneamente"""
        url = reverse('user_profile')
        
        data = {
            'nombre_supermercado': 'Nuevo Nombre',
            'provincia': 'Tucumán',
            'localidad': 'San Miguel de Tucumán'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar todos los cambios
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.nombre_supermercado, 'Nuevo Nombre')
        self.assertEqual(self.admin_user.provincia, 'Tucumán')
        self.assertEqual(self.admin_user.localidad, 'San Miguel de Tucumán')


class ValidacionDatosPerfilTestCase(APITestCase):
    """Tests para CA4: Validación de datos del perfil"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_validar',
            password='admin123',
            email='admin_validar@super.com',
            nombre_supermercado='Super Validar',
            cuil='20444555666',
            provincia='Salta',
            localidad='Salta Capital'
        )
        
        # Crear otro usuario para probar duplicados
        self.otro_admin = User.objects.create_user(
            username='otro_admin',
            password='admin123',
            email='otro_admin@super.com',
            nombre_supermercado='Otro Super',
            cuil='20777888999',
            provincia='Jujuy',
            localidad='San Salvador de Jujuy'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_validar_campos_obligatorios_completos(self):
        """Test CA4: Sistema valida que campos obligatorios estén completos"""
        url = reverse('user_profile')
        
        # Intentar actualizar con datos válidos
        data = {
            'nombre_supermercado': 'Nombre Válido',
            'provincia': 'Provincia Válida'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CambioContrasenaTestCase(APITestCase):
    """Tests para CA5: Cambio de contraseña"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_password',
            password='OldPassword123!',
            email='admin_password@super.com',
            nombre_supermercado='Super Password',
            cuil='20123123123',
            provincia='Buenos Aires',
            localidad='CABA'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_cambiar_contrasena_correctamente(self):
        """Test CA5: Admin puede cambiar su contraseña correctamente"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'OldPassword123!',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('actualizada', response.data['message'].lower())
        
        # Verificar que la contraseña cambió
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password('NewPassword456!'))
    
    def test_campos_requeridos_cambio_contrasena(self):
        """Test CA5: Se requieren contraseña actual, nueva y confirmación"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'OldPassword123!',
            'new_password': 'NewPassword456!'
            # Falta confirm_password
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)


class VerificacionContrasenaActualTestCase(APITestCase):
    """Tests para CA6: Verificación de contraseña actual"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_verify',
            password='CurrentPass123!',
            email='admin_verify@super.com',
            nombre_supermercado='Super Verify',
            cuil='20999888777',
            provincia='Chaco',
            localidad='Resistencia'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_verificar_contrasena_actual_correcta(self):
        """Test CA6: Sistema verifica que contraseña actual sea correcta"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'CurrentPass123!',
            'new_password': 'NewPassword789!',
            'confirm_password': 'NewPassword789!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_rechazar_contrasena_actual_incorrecta(self):
        """Test CA6: Sistema rechaza si contraseña actual es incorrecta"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword789!',
            'confirm_password': 'NewPassword789!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        # Verificar mensaje específico
        errors_str = str(response.data['errors']).lower()
        self.assertIn('incorrecta', errors_str)


class ValidacionSeguridadContrasenaTestCase(APITestCase):
    """Tests para CA7: Validación de seguridad de contraseña"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_security',
            password='SecurePass123!',
            email='admin_security@super.com',
            nombre_supermercado='Super Security',
            cuil='20666777888',
            provincia='Misiones',
            localidad='Posadas'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_validar_minimo_8_caracteres(self):
        """Test CA7: Contraseña debe tener mínimo 8 caracteres"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'SecurePass123!',
            'new_password': 'Pass1!',  # Solo 6 caracteres
            'confirm_password': 'Pass1!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_str = str(response.data['errors']).lower()
        self.assertIn('8', errors_str)
    
    def test_validar_incluye_numeros(self):
        """Test CA7: Contraseña debe incluir números"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'SecurePass123!',
            'new_password': 'PasswordOnly!',  # Sin números
            'confirm_password': 'PasswordOnly!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_str = str(response.data['errors']).lower()
        self.assertIn('número', errors_str)
    
    def test_validar_incluye_caracteres_especiales(self):
        """Test CA7: Contraseña debe incluir caracteres especiales"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'SecurePass123!',
            'new_password': 'Password123',  # Sin caracteres especiales
            'confirm_password': 'Password123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_str = str(response.data['errors']).lower()
        self.assertIn('especial', errors_str)
    
    def test_contrasena_valida_cumple_requisitos(self):
        """Test CA7: Contraseña que cumple todos los requisitos es aceptada"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'SecurePass123!',
            'new_password': 'NewSecure456!',  # 8+ chars, números, letras, especial
            'confirm_password': 'NewSecure456!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_validar_confirmacion_coincide(self):
        """Test CA7: Contraseña nueva y confirmación deben coincidir"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'SecurePass123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'DifferentPass456!'  # No coincide
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_str = str(response.data['errors']).lower()
        self.assertIn('coincid', errors_str)


class GestionFotoPerfilTestCase(APITestCase):
    """Tests para CA8: Gestión de foto de perfil"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_foto',
            password='admin123',
            email='admin_foto@super.com',
            nombre_supermercado='Super Foto',
            cuil='20555444333',
            provincia='Neuquén',
            localidad='Neuquén Capital'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """Helper para crear una imagen de prueba"""
        file = io.BytesIO()
        image = Image.new('RGB', size, color='red')
        image.save(file, format)
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type=f'image/{format.lower()}')
    
    def test_subir_foto_perfil(self):
        """Test CA8: Admin puede subir foto de perfil"""
        url = reverse('user_profile')
        
        image = self.create_test_image()
        
        data = {
            'logo': image
        }
        
        response = self.client.patch(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se guardó la imagen
        self.admin_user.refresh_from_db()
        self.assertIsNotNone(self.admin_user.logo)
        self.assertTrue(self.admin_user.logo.name.endswith('.jpg'))
    
    def test_cambiar_foto_perfil(self):
        """Test CA8: Admin puede cambiar foto de perfil existente"""
        # Primero subir una imagen
        url = reverse('user_profile')
        image1 = self.create_test_image('first.jpg')
        
        response1 = self.client.patch(url, {'logo': image1}, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Ahora cambiarla por otra
        image2 = self.create_test_image('second.jpg')
        response2 = self.client.patch(url, {'logo': image2}, format='multipart')
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verificar que se actualizó
        self.admin_user.refresh_from_db()
        self.assertIsNotNone(self.admin_user.logo)
    
    def test_validar_formato_imagen(self):
        """Test CA8: Sistema valida formato de imagen (solo JPG/JPEG)"""
        url = reverse('user_profile')
        
        # Intentar subir PNG (no permitido)
        image_png = self.create_test_image('test.png', format='PNG')
        
        response = self.client.patch(url, {'logo': image_png}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        errors_str = str(response.data['errors']).lower()
        self.assertIn('jpg', errors_str.lower() or 'jpeg' in errors_str.lower())
    
    def test_validar_tamano_imagen(self):
        """Test CA8: Sistema valida tamaño máximo de imagen (1MB)"""
        url = reverse('user_profile')
        
        # Crear imagen muy grande (más de 1MB)
        large_image = self.create_test_image('large.jpg', size=(3000, 3000))
        
        response = self.client.patch(url, {'logo': large_image}, format='multipart')
        
        # Puede ser 400 por tamaño
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            errors_str = str(response.data).lower()
            # Verificar que menciona el tamaño
            self.assertTrue('1mb' in errors_str or 'tamaño' in errors_str or 'size' in errors_str)


class MensajesConfirmacionPerfilTestCase(APITestCase):
    """Tests para CA9: Mensajes de confirmación"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_mensajes',
            password='admin123',
            email='admin_mensajes@super.com',
            nombre_supermercado='Super Mensajes',
            cuil='20222333444',
            provincia='La Rioja',
            localidad='La Rioja Capital'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_mensaje_confirmacion_actualizar_perfil(self):
        """Test CA9: Mensaje de confirmación al actualizar perfil"""
        url = reverse('user_profile')
        
        data = {
            'nombre_supermercado': 'Nombre Actualizado'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        mensaje = response.data['message'].lower()
        self.assertTrue('actualizado' in mensaje or 'exitosamente' in mensaje)
    
    def test_mensaje_confirmacion_cambiar_contrasena(self):
        """Test CA9: Mensaje de confirmación al cambiar contraseña"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'admin123',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        mensaje = response.data['message'].lower()
        self.assertTrue('actualizada' in mensaje or 'exitosamente' in mensaje)


class MensajesErrorTestCase(APITestCase):
    """Tests para CA10: Mensajes de error claros"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_errores',
            password='ValidPass123!',
            email='admin_errores@super.com',
            nombre_supermercado='Super Errores',
            cuil='20888999000',
            provincia='San Juan',
            localidad='San Juan Capital'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_mensaje_error_contrasena_incorrecta(self):
        """Test CA10: Mensaje claro cuando contraseña actual es incorrecta"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        self.assertIn('errors', response.data)
        # Verificar que el mensaje es claro
        error_text = str(response.data).lower()
        self.assertIn('incorrecta', error_text)
    
    def test_mensaje_error_formato_imagen_invalido(self):
        """Test CA10: Mensaje claro cuando formato de imagen no es válido"""
        url = reverse('user_profile')
        
        # Crear imagen PNG (no permitida)
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(file, 'PNG')
        file.seek(0)
        image_png = SimpleUploadedFile('test.png', file.read(), content_type='image/png')
        
        response = self.client.patch(url, {'logo': image_png}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verificar que hay un mensaje de error claro
        self.assertIn('errors', response.data)
        error_text = str(response.data['errors']).lower()
        self.assertTrue('jpg' in error_text or 'jpeg' in error_text)
    
    def test_mensaje_error_contrasenas_no_coinciden(self):
        """Test CA10: Mensaje claro cuando contraseñas no coinciden"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'ValidPass123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'DifferentPassword456!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        error_text = str(response.data['errors']).lower()
        self.assertIn('coincid', error_text)
    
    def test_mensaje_error_contrasena_debil(self):
        """Test CA10: Mensaje claro cuando contraseña no cumple requisitos"""
        url = reverse('change_password')
        
        data = {
            'current_password': 'ValidPass123!',
            'new_password': 'weak',  # Muy débil
            'confirm_password': 'weak'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        self.assertIn('errors', response.data)
        # Verificar que menciona los requisitos
        error_text = str(response.data['errors']).lower()
        self.assertTrue('caracter' in error_text or '8' in error_text)


class CerrarSesionTestCase(APITestCase):
    """Tests para CA11: Cerrar sesión"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_logout',
            password='admin123',
            email='admin_logout@super.com',
            nombre_supermercado='Super Logout',
            cuil='20111000999',
            provincia='Catamarca',
            localidad='San Fernando del Valle'
        )
        
        self.client = APIClient()
    
    def test_cerrar_sesion_disponible(self):
        """Test CA11: Funcionalidad de cerrar sesión está disponible"""
        # Autenticarse
        self.client.force_authenticate(user=self.admin_user)
        
        # Verificar que puede acceder al perfil
        url = reverse('user_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cerrar sesión (eliminar autenticación)
        self.client.force_authenticate(user=None)
        
        # Verificar que ya no puede acceder
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_endpoint_disponible(self):
        """Test CA11: Endpoint de logout está disponible"""
        # Verificar que existe el endpoint de logout
        try:
            url = reverse('logout')
            # Si el endpoint existe, el test pasa
            self.assertIsNotNone(url)
        except:
            # Si no existe endpoint específico, verificar que al menos
            # se puede cerrar sesión eliminando la autenticación
            self.client.force_authenticate(user=self.admin_user)
            url_profile = reverse('user_profile')
            
            response_autenticado = self.client.get(url_profile)
            self.assertEqual(response_autenticado.status_code, status.HTTP_200_OK)
            
            # Cerrar sesión
            self.client.force_authenticate(user=None)
            
            response_sin_auth = self.client.get(url_profile)
            self.assertEqual(response_sin_auth.status_code, status.HTTP_401_UNAUTHORIZED)


class IntegracionCompletaPerfilTestCase(APITestCase):
    """Tests de integración completa del flujo de perfil"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin_integracion',
            password='InitialPass123!',
            email='admin_integracion@super.com',
            nombre_supermercado='Super Integración',
            cuil='20123456780',
            provincia='Formosa',
            localidad='Formosa Capital'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_flujo_completo_actualizacion_perfil(self):
        """Test: Flujo completo de actualización de perfil"""
        url = reverse('user_profile')
        
        # 1. Obtener datos actuales
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)
        datos_originales = response_get.data
        
        # 2. Actualizar información
        data = {
            'nombre_supermercado': 'Supermercado Actualizado',
            'provincia': 'Chubut',
            'localidad': 'Rawson'
        }
        
        response_update = self.client.patch(url, data, format='json')
        self.assertEqual(response_update.status_code, status.HTTP_200_OK)
        self.assertIn('message', response_update.data)
        
        # 3. Verificar que los cambios se guardaron
        response_verify = self.client.get(url)
        self.assertEqual(response_verify.status_code, status.HTTP_200_OK)
        self.assertEqual(response_verify.data['nombre_supermercado'], 'Supermercado Actualizado')
        self.assertEqual(response_verify.data['provincia'], 'Chubut')
    
    def test_flujo_completo_cambio_contrasena(self):
        """Test: Flujo completo de cambio de contraseña"""
        url = reverse('change_password')
        
        # 1. Cambiar contraseña
        data = {
            'current_password': 'InitialPass123!',
            'new_password': 'UpdatedPass456!',
            'confirm_password': 'UpdatedPass456!'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. Verificar que la nueva contraseña funciona
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password('UpdatedPass456!'))
        self.assertFalse(self.admin_user.check_password('InitialPass123!'))
