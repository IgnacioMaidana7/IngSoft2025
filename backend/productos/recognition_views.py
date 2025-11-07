from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from authentication.permissions import IsCajeroOrAdmin, IsReponedorOrAdmin
from rest_framework.permissions import IsAuthenticated
import requests
import base64
from django.conf import settings
import logging
import traceback

# Configurar logger
logger = logging.getLogger(__name__)

# URL de la API de reconocimiento
RECOGNITION_API_URL = getattr(settings, 'RECOGNITION_API_URL', 'http://localhost:8080')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reconocer_productos_imagen(request):
    """
    Recibe una imagen del frontend y la envía a la API de reconocimiento.
    Devuelve los productos detectados con sus IDs mapeados de IngSoft2025.
    """
    try:
        logger.info(f"🔍 Iniciando reconocimiento de imagen para usuario: {request.user.email}")
        
        # Verificar que se recibió una imagen
        if 'image' not in request.FILES:
            logger.warning("⚠️ No se recibió imagen en la request")
            return Response({
                'success': False,
                'error': 'No se recibió ninguna imagen'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        logger.info(f"📁 Imagen recibida: {image_file.name}, tamaño: {image_file.size} bytes")
        
        # Leer y convertir la imagen a base64
        try:
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            logger.info(f"✅ Imagen convertida a base64: {len(image_base64)} caracteres")
        except Exception as e:
            logger.error(f"❌ Error convirtiendo imagen a base64: {str(e)}")
            return Response({
                'success': False,
                'error': f'Error procesando la imagen: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el depósito del usuario (si es empleado)
        deposito_id = None
        try:
            from authentication.models import EmpleadoUser
            if isinstance(request.user, EmpleadoUser) and request.user.deposito:
                deposito_id = request.user.deposito.id
                logger.info(f"📦 Depósito del usuario: {deposito_id}")
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo depósito: {str(e)}")
            # No es crítico, continuamos sin depósito
        
        # Preparar payload para la API de reconocimiento
        payload = {
            'image_base64': image_base64,
            'deposito_id': deposito_id,
            'format_for_frontend': True,
            'include_stock_suggestions': True
        }
        
        # Enviar request a la API de reconocimiento
        api_url = f"{RECOGNITION_API_URL}/api/recognize-ingsoft"
        logger.info(f"🚀 Enviando request a: {api_url}")
        
        try:
            response = requests.post(
                api_url,
                json=payload,
                timeout=30  # 30 segundos de timeout
            )
            logger.info(f"📡 Respuesta de API: Status {response.status_code}")
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout al conectar con la API de reconocimiento")
            return Response({
                'success': False,
                'error': 'Timeout al conectar con la API de reconocimiento',
                'details': 'El servidor de reconocimiento tardó más de 30 segundos en responder'
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Error de conexión con API de reconocimiento: {str(e)}")
            return Response({
                'success': False,
                'error': 'No se pudo conectar con la API de reconocimiento',
                'details': f'Verificar que el servidor esté corriendo en {RECOGNITION_API_URL}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if response.status_code != 200:
            logger.error(f"❌ API de reconocimiento retornó status {response.status_code}")
            logger.error(f"Respuesta: {response.text[:500]}")
            return Response({
                'success': False,
                'error': 'Error en la API de reconocimiento',
                'details': response.text[:500]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Obtener resultado
        try:
            result = response.json()
            logger.info(f"✅ Resultado parseado: {result.get('total_productos', 0)} productos detectados")
        except Exception as e:
            logger.error(f"❌ Error parseando respuesta JSON: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error parseando respuesta de la API',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Agregar información adicional de productos desde la base de datos
        if result.get('success') and result.get('productos'):
            from productos.models import Producto, ProductoDeposito
            
            logger.info(f"🔍 Enriqueciendo {len(result['productos'])} productos con info de BD")
            productos_enriquecidos = []
            
            for idx, producto_detectado in enumerate(result['productos']):
                try:
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
                            
                            logger.debug(f"  ✅ Producto {idx+1}: {producto_db.nombre} (ID: {ingsoft_id})")
                            
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
                            logger.warning(f"  ⚠️ Producto {idx+1}: ID {ingsoft_id} no encontrado en BD")
                            producto_detectado['existe_en_bd'] = False
                            producto_detectado['mensaje'] = 'Producto no encontrado en la base de datos'
                    else:
                        logger.warning(f"  ⚠️ Producto {idx+1}: No tiene ingsoft_product_id")
                        producto_detectado['existe_en_bd'] = False
                        producto_detectado['mensaje'] = 'Producto no mapeado en el sistema'
                    
                    productos_enriquecidos.append(producto_detectado)
                    
                except Exception as e:
                    logger.error(f"  ❌ Error procesando producto {idx+1}: {str(e)}")
                    # Agregar el producto sin enriquecer
                    producto_detectado['existe_en_bd'] = False
                    producto_detectado['mensaje'] = f'Error: {str(e)}'
                    productos_enriquecidos.append(producto_detectado)
            
            result['productos'] = productos_enriquecidos
            logger.info(f"✅ Productos enriquecidos: {len(productos_enriquecidos)}")
        
        logger.info("✅ Reconocimiento completado exitosamente")
        return Response(result, status=status.HTTP_200_OK)
        
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout - ya manejado arriba")
        return Response({
            'success': False,
            'error': 'Timeout al conectar con la API de reconocimiento'
        }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ ConnectionError - ya manejado arriba")
        return Response({
            'success': False,
            'error': 'No se pudo conectar con la API de reconocimiento',
            'details': f'Verificar que el servidor esté corriendo en {RECOGNITION_API_URL}'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Error procesando la imagen: {str(e)}',
            'traceback': traceback.format_exc() if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
