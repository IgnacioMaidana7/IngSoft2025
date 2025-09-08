from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import Deposito
from productos.models import ProductoDeposito, Producto, Categoria

User = get_user_model()


class DepositoDebugTestCase(APITestCase):
    """Test para debuggear el formato de respuesta"""
    
    def setUp(self):
        """Configuración inicial para debug"""
        self.user = User.objects.create_user(
            username='debug_user',
            email='debug@test.com',
            password='testpass123',
            nombre_supermercado='Debug Super',
            cuil='20333333333',
            provincia='Buenos Aires',
            localidad='La Plata'
        )
        
        self.client.force_authenticate(user=self.user)
        
        Deposito.objects.create(
            nombre='Debug Deposito',
            direccion='Debug Address',
            descripcion='Debug desc',
            supermercado=self.user
        )
    
    def test_debug_response_format(self):
        """Debug del formato de respuesta"""
        url = reverse('deposito-list-create')
        response = self.client.get(url)
        
        print(f"Status: {response.status_code}")
        print(f"Type of response.data: {type(response.data)}")
        print(f"Response data: {response.data}")
        
        if hasattr(response.data, '__iter__'):
            for i, item in enumerate(response.data):
                print(f"Item {i}: {item}, type: {type(item)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
