from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404

from .models import Categoria, Producto, ProductoDeposito
from .serializers import (
    CategoriaSerializer, CategoriaListSerializer,
    ProductoSerializer, ProductoListSerializer, ProductoCreateUpdateSerializer,
    ProductoDepositoSerializer
)
from inventario.models import Deposito

class ProductoPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# === VISTAS PARA CATEGORÍAS ===

class CategoriaListCreateView(generics.ListCreateAPIView):
    queryset = Categoria.objects.filter(activo=True).order_by('nombre')
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ProductoPagination

class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]
    
    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()
        # Soft delete - marcar como inactivo
        categoria.activo = False
        categoria.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_categorias_disponibles(request):
    """Obtener lista simplificada de categorías para dropdown"""
    categorias = Categoria.objects.filter(activo=True).order_by('nombre')
    serializer = CategoriaListSerializer(categorias, many=True)
    return Response(serializer.data)

# === VISTAS PARA PRODUCTOS ===

class ProductoListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ProductoPagination
    
    def get_queryset(self):
        queryset = Producto.objects.select_related('categoria').prefetch_related('stocks__deposito')
        
        # Filtros
        categoria_id = self.request.query_params.get('categoria', None)
        deposito_id = self.request.query_params.get('deposito', None)
        activo = self.request.query_params.get('activo', None)
        search = self.request.query_params.get('search', None)
        
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        if deposito_id:
            queryset = queryset.filter(stocks__deposito_id=deposito_id)
        
        if activo is not None:
            activo_bool = activo.lower() == 'true'
            queryset = queryset.filter(activo=activo_bool)
        
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(categoria__nombre__icontains=search)
            )
        
        return queryset.distinct().order_by('nombre')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductoCreateUpdateSerializer
        return ProductoListSerializer

class ProductoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Producto.objects.select_related('categoria').prefetch_related('stocks__deposito')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductoCreateUpdateSerializer
        return ProductoSerializer
    
    def destroy(self, request, *args, **kwargs):
        producto = self.get_object()
        
        # Verificar que no tenga stock antes de deshabilitar
        stock_total = sum(stock.cantidad for stock in producto.stocks.all())
        if stock_total > 0:
            return Response({
                'error': 'No se puede deshabilitar un producto con stock disponible',
                'stock_total': stock_total
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete - marcar como inactivo
        producto.activo = False
        producto.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# === VISTAS PARA STOCK DE PRODUCTOS ===

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def gestionar_stock_producto(request, producto_id):
    """Gestionar stock de un producto en diferentes depósitos"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'GET':
        stocks = ProductoDeposito.objects.filter(producto=producto).select_related('deposito')
        serializer = ProductoDepositoSerializer(stocks, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ProductoDepositoSerializer(data=request.data)
        if serializer.is_valid():
            # Verificar que no exista ya este producto en el depósito
            deposito_id = serializer.validated_data['deposito'].id
            if ProductoDeposito.objects.filter(producto=producto, deposito_id=deposito_id).exists():
                return Response({
                    'error': 'Este producto ya está registrado en el depósito seleccionado'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save(producto=producto)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def stock_producto_detail(request, stock_id):
    """Gestionar stock específico de un producto en un depósito"""
    stock = get_object_or_404(ProductoDeposito, id=stock_id)
    
    if request.method == 'GET':
        serializer = ProductoDepositoSerializer(stock)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ProductoDepositoSerializer(stock, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def productos_por_deposito(request, deposito_id):
    """Obtener productos disponibles en un depósito específico"""
    deposito = get_object_or_404(Deposito, id=deposito_id)
    stocks = ProductoDeposito.objects.filter(
        deposito=deposito,
        producto__activo=True
    ).select_related('producto', 'producto__categoria')
    
    productos_data = []
    for stock in stocks:
        productos_data.append({
            'id': stock.producto.id,
            'nombre': stock.producto.nombre,
            'categoria': stock.producto.categoria.nombre,
            'precio': stock.producto.precio,
            'cantidad': stock.cantidad,
            'cantidad_minima': stock.cantidad_minima,
            'tiene_stock': stock.tiene_stock(),
            'stock_bajo': stock.stock_bajo(),
            'stock_id': stock.id
        })
    
    return Response({
        'deposito': {
            'id': deposito.id,
            'nombre': deposito.nombre,
            'direccion': deposito.direccion
        },
        'productos': productos_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_productos(request):
    """Obtener estadísticas generales de productos"""
    total_productos = Producto.objects.filter(activo=True).count()
    total_categorias = Categoria.objects.filter(activo=True).count()
    productos_sin_stock = Producto.objects.filter(
        activo=True,
        stocks__cantidad=0
    ).distinct().count()
    
    # Stock total por categoría
    stock_por_categoria = []
    categorias = Categoria.objects.filter(activo=True)
    for categoria in categorias:
        stock_total = ProductoDeposito.objects.filter(
            producto__categoria=categoria,
            producto__activo=True
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        stock_por_categoria.append({
            'categoria': categoria.nombre,
            'stock_total': stock_total,
            'productos_count': categoria.productos.filter(activo=True).count()
        })
    
    return Response({
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'productos_sin_stock': productos_sin_stock,
        'stock_por_categoria': stock_por_categoria
    })
