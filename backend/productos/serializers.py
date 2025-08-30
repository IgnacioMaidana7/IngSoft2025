from rest_framework import serializers
from .models import Categoria, Producto, ProductoDeposito
from inventario.models import Deposito

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'activo', 'fecha_creacion']
        read_only_fields = ['fecha_creacion']

class CategoriaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas desplegables"""
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']

class ProductoDepositoSerializer(serializers.ModelSerializer):
    deposito_nombre = serializers.CharField(source='deposito.nombre', read_only=True)
    deposito_direccion = serializers.CharField(source='deposito.direccion', read_only=True)
    tiene_stock = serializers.BooleanField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ProductoDeposito
        fields = ['id', 'deposito', 'deposito_nombre', 'deposito_direccion', 
                 'cantidad', 'cantidad_minima', 'tiene_stock', 'stock_bajo',
                 'fecha_creacion', 'fecha_modificacion']
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']

class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stocks = ProductoDepositoSerializer(many=True, read_only=True)
    stock_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'categoria', 'categoria_nombre', 'precio', 
                 'descripcion', 'activo', 'stocks', 'stock_total',
                 'fecha_creacion', 'fecha_modificacion']
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_stock_total(self, obj):
        return sum(stock.cantidad for stock in obj.stocks.all())

class ProductoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados"""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stock_total = serializers.SerializerMethodField()
    depositos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'categoria_nombre', 'precio', 'activo',
                 'stock_total', 'depositos_count', 'fecha_modificacion']
    
    def get_stock_total(self, obj):
        return sum(stock.cantidad for stock in obj.stocks.all())
    
    def get_depositos_count(self, obj):
        return obj.stocks.count()

class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar productos con stock inicial"""
    deposito_id = serializers.IntegerField(write_only=True, required=False)
    cantidad_inicial = serializers.IntegerField(write_only=True, required=False, default=0)
    cantidad_minima = serializers.IntegerField(write_only=True, required=False, default=0)
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'categoria', 'precio', 'descripcion', 
                 'deposito_id', 'cantidad_inicial', 'cantidad_minima']
    
    def create(self, validated_data):
        deposito_id = validated_data.pop('deposito_id', None)
        cantidad_inicial = validated_data.pop('cantidad_inicial', 0)
        cantidad_minima = validated_data.pop('cantidad_minima', 0)
        
        producto = Producto.objects.create(**validated_data)
        
        # Crear stock inicial si se especifica un depósito
        if deposito_id:
            try:
                deposito = Deposito.objects.get(id=deposito_id)
                ProductoDeposito.objects.create(
                    producto=producto,
                    deposito=deposito,
                    cantidad=cantidad_inicial,
                    cantidad_minima=cantidad_minima
                )
            except Deposito.DoesNotExist:
                pass
        
        return producto

    def update(self, instance, validated_data):
        deposito_id = validated_data.pop('deposito_id', None)
        cantidad_inicial = validated_data.pop('cantidad_inicial', None)
        cantidad_minima = validated_data.pop('cantidad_minima', None)
        
        # Actualizar producto
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar stock si se especifica
        if deposito_id and cantidad_inicial is not None:
            try:
                deposito = Deposito.objects.get(id=deposito_id)
                stock, created = ProductoDeposito.objects.get_or_create(
                    producto=instance,
                    deposito=deposito,
                    defaults={
                        'cantidad': cantidad_inicial,
                        'cantidad_minima': cantidad_minima or 0
                    }
                )
                if not created:
                    stock.cantidad = cantidad_inicial
                    if cantidad_minima is not None:
                        stock.cantidad_minima = cantidad_minima
                    stock.save()
            except Deposito.DoesNotExist:
                pass
        
        return instance
