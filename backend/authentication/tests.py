from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
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
class RegistrationTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.url = reverse('register')

	def _valid_payload(self, **overrides):
		data = {
			'username': 'supermarket',
			'email': 'market1@example.com',
			'password': 'StrongPass1!',
			'password_confirm': 'StrongPass1!',
			'nombre_supermercado': 'Mi Super',
			'cuil': '20123456789',
			'provincia': 'Buenos Aires',
			'localidad': 'La Plata',
		}
		data.update(overrides)
		return data

	def test_registro_exitoso(self):
		payload = self._valid_payload()
		response = self.client.post(self.url, data=payload, format='json')

		self.assertEqual(response.status_code, 201)
		self.assertIn('message', response.data)
		self.assertEqual(response.data['message'], 'Registro exitoso. Ahora puede iniciar sesión.')
		self.assertIn('user', response.data)
		self.assertEqual(response.data['user']['email'], 'market1@example.com')

	def test_registro_fallido_email_invalido(self):
		payload = self._valid_payload(
			email='correo-invalido',
			username='supermarket2',
		)
		response = self.client.post(self.url, data=payload, format='json')

		self.assertEqual(response.status_code, 400)
		self.assertIn('errors', response.data)
		# Valida que hay error de email y el mensaje sea el esperado o el de DRF
		self.assertIn('email', response.data['errors'])
		email_msg = str(response.data['errors']['email'])
		self.assertTrue(
			(
				'Revise si el dato Email ha sido ingresado correctamente' in email_msg
			)
			or (
				'correo electrónico válida' in email_msg  # Mensaje por defecto de DRF
			),
			f"Mensaje de email inesperado: {email_msg}"
		)

	def test_registro_fallido_cuil_invalido(self):
		# CUIL inválido por longitud (10 dígitos)
		payload = self._valid_payload(
			email='market2@example.com',
			cuil='2012345678',
			username='supermarket3',
		)
		response = self.client.post(self.url, data=payload, format='json')

		self.assertEqual(response.status_code, 400)
		self.assertIn('errors', response.data)
		# Valida que hay error de CUIL y el mensaje sea el esperado o el del validador del modelo
		self.assertIn('cuil', response.data['errors'])
		cuil_msg = str(response.data['errors']['cuil'])
		self.assertTrue(
			(
				'Revisa si el dato CUIL ha sido ingresado correctamente' in cuil_msg
			)
			or (
				'El CUIL debe tener exactamente 11 dígitos' in cuil_msg
			),
			f"Mensaje de CUIL inesperado: {cuil_msg}"
		)

	def test_registro_fallido_email_y_cuil_invalidos(self):
		payload = self._valid_payload(
			email='correo-invalido',
			cuil='2012345678',
			username='supermarket4',
		)
		response = self.client.post(self.url, data=payload, format='json')

		self.assertEqual(response.status_code, 400)
		self.assertIn('errors', response.data)
		# Acepta dos variantes:
		# - Mensaje combinado en non_field_errors (si el serializer lo emite)
		# - Errores individuales en email y cuil
		errors = response.data['errors']
		if 'non_field_errors' in errors:
			combined_msg = str(errors['non_field_errors'])
			self.assertIn('Email', combined_msg)
			self.assertIn('CUIL', combined_msg)
		else:
			self.assertIn('email', errors)
			self.assertIn('cuil', errors)

