from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from authentication.permissions import IsCajeroOrAdmin
import requests
import base64
from django.conf import settings

# URL de la API de reconocimiento
RECOGNITION_API_URL = getattr(settings, 'RECOGNITION_API_URL', 'http://localhost:8080')

@api_view(['POST'])
@permission_classes([IsCajeroOrAdmin])
def reconocer_productos_imagen(request):
    """
    Recibe una imagen del frontend y la envía a la API de reconocimiento.
    Devuelve los productos detectados con sus IDs mapeados de IngSoft2025.
    """
    try:
        # Verificar que se recibió una imagen
        if 'image' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No se recibió ninguna imagen'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Leer y convertir la imagen a base64
        image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Obtener el depósito del usuario (si es cajero)
        deposito_id = None
        if hasattr(request.user, 'supermercado'):
            # Es un empleado cajero
            from empleados.models import Empleado
            empleado = Empleado.objects.filter(
                email=request.user.email,
                supermercado=request.user.supermercado
            ).first()
            if empleado and empleado.deposito:
                deposito_id = empleado.deposito.id
        
        # Preparar payload para la API de reconocimiento
        payload = {
            'image_base64': image_base64,
            'deposito_id': deposito_id,
            'format_for_frontend': True,
            'include_stock_suggestions': True
        }
        
        # Enviar request a la API de reconocimiento
        api_url = f"{RECOGNITION_API_URL}/api/recognize-ingsoft"
        response = requests.post(
            api_url,
            json=payload,
            timeout=30  # 30 segundos de timeout
        )
        
        if response.status_code != 200:
            return Response({
                'success': False,
                'error': 'Error en la API de reconocimiento',
                'details': response.text
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Obtener resultado
        result = response.json()
        
        # Agregar información adicional de productos desde la base de datos
        if result.get('success') and result.get('productos'):
            from productos.models import Producto, ProductoDeposito
            
            productos_enriquecidos = []
            for producto_detectado in result['productos']:
                # ⭐ CLAVE: Obtener el ID de IngSoft mapeado desde la API
                ingsoft_id = producto_detectado.get('ingsoft_product_id')
                
                if ingsoft_id:
                    try:
                        # 🔍 Buscar producto en la base de datos POR ID (más rápido y seguro)
                        producto_db = Producto.objects.get(id=ingsoft_id, activo=True)
                        
                        # Enriquecer con información de la BD
                        producto_detectado['nombre_db'] = producto_db.nombre
                        producto_detectado['categoria_db'] = producto_db.categoria.nombre if producto_db.categoria else 'Sin categoría'
                        producto_detectado['precio_db'] = str(producto_db.precio)
                        producto_detectado['existe_en_bd'] = True
                        
                        # Agregar stock disponible si hay depósito
                        if deposito_id:
                            stock = ProductoDeposito.objects.filter(
                                producto=producto_db,
                                deposito_id=deposito_id
                            ).first()
                            
                            if stock:
                                producto_detectado['stock_disponible'] = stock.cantidad
                                producto_detectado['stock_minimo'] = stock.cantidad_minima
                                producto_detectado['stock_bajo'] = stock.stock_bajo()
                        
                    except Producto.DoesNotExist:
                        producto_detectado['existe_en_bd'] = False
                        producto_detectado['mensaje'] = 'Producto no encontrado en la base de datos'
                else:
                    producto_detectado['existe_en_bd'] = False
                    producto_detectado['mensaje'] = 'Producto no mapeado en el sistema'
                
                productos_enriquecidos.append(producto_detectado)
            
            result['productos'] = productos_enriquecidos
        
        return Response(result, status=status.HTTP_200_OK)
        
    except requests.exceptions.Timeout:
        return Response({
            'success': False,
            'error': 'Timeout al conectar con la API de reconocimiento'
        }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        
    except requests.exceptions.ConnectionError:
        return Response({
            'success': False,
            'error': 'No se pudo conectar con la API de reconocimiento',
            'details': f'Verificar que el servidor esté corriendo en {RECOGNITION_API_URL}'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error procesando la imagen: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsCajeroOrAdmin])
def obtener_catalogo_reconocimiento(request):
    """
    Obtiene el catálogo de productos reconocibles desde la API.
    """
    try:
        api_url = f"{RECOGNITION_API_URL}/api/catalog"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200:
            return Response({
                'success': False,
                'error': 'Error obteniendo catálogo'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(response.json(), status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error obteniendo catálogo: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsCajeroOrAdmin])
def verificar_api_reconocimiento(request):
    """
    Verifica el estado de la API de reconocimiento.
    """
    try:
        api_url = f"{RECOGNITION_API_URL}/health"
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            return Response({
                'success': True,
                'status': 'API de reconocimiento disponible',
                'details': response.json()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'status': 'API de reconocimiento con problemas',
                'details': response.text
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        return Response({
            'success': False,
            'status': 'API de reconocimiento no disponible',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
