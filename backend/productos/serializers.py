from rest_framework import serializers
from .models import Categoria, Producto, ProductoDeposito
from inventario.models import Deposito
from authentication.models import EmpleadoUser

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
    
    def validate_precio(self, value):
        """Validar que el precio sea positivo"""
        if value is not None and value <= 0:
            raise serializers.ValidationError('El precio debe ser mayor a 0')
        return value
    
    def get_stock_total(self, obj):
        """Calcula el stock total solo de los depósitos del usuario actual"""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return 0
        
        user = request.user
        
        # Filtrar stocks solo de depósitos que pertenecen al usuario
        if hasattr(user, 'supermercado'):
            # Usuario EmpleadoUser - filtrar por supermercado
            user_stocks = obj.stocks.filter(deposito__supermercado=user.supermercado)
        elif hasattr(user, 'depositos'):
            # Usuario Admin - filtrar por sus depósitos
            user_stocks = obj.stocks.filter(deposito__supermercado=user)
        else:
            return 0
        
        return sum(stock.cantidad for stock in user_stocks)

class ProductoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados"""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stock_total = serializers.SerializerMethodField()
    depositos_count = serializers.SerializerMethodField()
    stock_nivel = serializers.SerializerMethodField()
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'categoria_nombre', 'precio', 'activo',
                 'stock_total', 'depositos_count', 'stock_nivel', 'fecha_modificacion']
    
    def _get_user_stocks(self, obj):
        """Obtiene los stocks filtrados por el usuario actual"""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return obj.stocks.none()
        
        user = request.user
        
        # Filtrar stocks solo de depósitos que pertenecen al usuario
        if hasattr(user, 'supermercado'):
            # Usuario EmpleadoUser - filtrar por supermercado
            return obj.stocks.filter(deposito__supermercado=user.supermercado)
        elif hasattr(user, 'depositos'):
            # Usuario Admin - filtrar por sus depósitos
            return obj.stocks.filter(deposito__supermercado=user)
        else:
            return obj.stocks.none()
    
    def get_stock_total(self, obj):
        """Calcula el stock total solo de los depósitos del usuario actual"""
        user_stocks = self._get_user_stocks(obj)
        return sum(stock.cantidad for stock in user_stocks)
    
    def get_depositos_count(self, obj):
        """Cuenta solo los depósitos del usuario actual que tienen este producto"""
        user_stocks = self._get_user_stocks(obj)
        return user_stocks.count()
    
    def get_stock_nivel(self, obj):
        """Determina el nivel de stock general del producto (solo depósitos del usuario)"""
        user_stocks = self._get_user_stocks(obj)
        total_stock = sum(stock.cantidad for stock in user_stocks)
        
        if total_stock == 0:
            return 'sin-stock'
        
        # Verificar si tiene stock bajo en algún depósito del usuario
        for stock in user_stocks:
            if stock.cantidad > 0 and stock.cantidad < stock.cantidad_minima:
                return 'bajo'
        
        return 'normal'

class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar productos con stock inicial"""
    deposito_id = serializers.IntegerField(write_only=True, required=False)
    cantidad_inicial = serializers.IntegerField(write_only=True, required=False, default=0)
    cantidad_minima = serializers.IntegerField(write_only=True, required=False, default=0)
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'categoria', 'precio', 'descripcion', 'activo',
                 'deposito_id', 'cantidad_inicial', 'cantidad_minima']

    def validate_precio(self, value):
        """Validar que el precio sea positivo"""
        if value is not None and value <= 0:
            raise serializers.ValidationError('El precio debe ser mayor a 0')
        return value

    def validate(self, attrs):
        # Solo validar campos obligatorios al crear (instance is None)
        # Para actualizaciones (instance exists), permitir actualizaciones parciales
        if self.instance is None:
            # Validación solo para creación
            for field in ['nombre', 'categoria', 'precio']:
                if field not in attrs:
                    raise serializers.ValidationError({field: 'Este campo es obligatorio.'})
        
        return attrs

    def _get_user_deposito(self):
        request = self.context.get('request')
        if request and isinstance(request.user, EmpleadoUser):
            # Obtener depósito desde el modelo Empleado relacionado por email
            try:
                from empleados.models import Empleado
                emp = Empleado.objects.filter(email=request.user.email, supermercado=request.user.supermercado).first()
                if emp:
                    return emp.deposito
            except Exception:
                pass
        return None
    
    def create(self, validated_data):
        deposito_id = validated_data.pop('deposito_id', None)
        cantidad_inicial = validated_data.pop('cantidad_inicial', 0)
        cantidad_minima = validated_data.pop('cantidad_minima', 0)
        # Si el creador es Reponedor y no manda deposito_id, usar su depósito asignado
        if not deposito_id:
            user_dep = self._get_user_deposito()
            if user_dep:
                deposito_id = user_dep.id

        # Verificar duplicado por nombre en el mismo depósito
        if deposito_id and Producto.objects.filter(nombre__iexact=validated_data['nombre'], stocks__deposito_id=deposito_id).exists():
            raise serializers.ValidationError({'nombre': 'Ya existe un producto con este nombre en su depósito.'})

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
        
        # Actualizar/crear stock si se especifica
        if deposito_id and cantidad_inicial is not None:
            try:
                deposito = Deposito.objects.get(id=deposito_id)
                # Verificar duplicado si cambia el nombre: mismo nombre en ese depósito distinto producto
                nuevo_nombre = getattr(instance, 'nombre', None)
                if nuevo_nombre and Producto.objects.filter(nombre__iexact=nuevo_nombre, stocks__deposito=deposito).exclude(id=instance.id).exists():
                    raise serializers.ValidationError({'nombre': 'Ya existe un producto con este nombre en su depósito.'})
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
