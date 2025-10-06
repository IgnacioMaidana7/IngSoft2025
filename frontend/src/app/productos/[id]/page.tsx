"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter, useParams } from "next/navigation";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import SelectorCategorias from "@/components/productos/SelectorCategorias";
import { 
  obtenerProducto,
  actualizarProducto,
  obtenerCategoriasDisponibles,
  obtenerStockCompletoProducto,
  actualizarStockCompletoProducto,
  CategoriaSimple,
  Producto,
  type StockCompleto
} from "@/lib/api";

export default function ProductoDetailPage() {
  const { token } = useAuth();
  const router = useRouter();
  const params = useParams();
  const productId = Number(params.id);
  
  const [producto, setProducto] = useState<Producto | null>(null);
  const [categorias, setCategorias] = useState<CategoriaSimple[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Estados para reponedor
  const [isReponedor, setIsReponedor] = useState(false);
  
  // Estados para edición
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState({
    nombre: "",
    categoria: 0,
    precio: "",
    descripcion: ""
  });

  // Estados para gestión de stock
  const [stockCompleto, setStockCompleto] = useState<StockCompleto[]>([]);
  const [stockLoading, setStockLoading] = useState(false);
  const [stockEditado, setStockEditado] = useState<{[key: number]: {cantidad: number, cantidad_minima: number}}>({});

  const cargarStockCompleto = useCallback(async () => {
    if (!token || !producto) return;
    
    try {
      setStockLoading(true);
      const stockData = await obtenerStockCompletoProducto(producto.id, token);
      setStockCompleto(stockData.stocks);
      
      // Inicializar valores editables
      const inicial: {[key: number]: {cantidad: number, cantidad_minima: number}} = {};
      stockData.stocks.forEach(stock => {
        inicial[stock.deposito_id] = {
          cantidad: stock.cantidad,
          cantidad_minima: stock.cantidad_minima
        };
      });
      setStockEditado(inicial);
    } catch (err: unknown) {
      console.error('Error cargando stock completo:', err);
      setError('Error cargando información de stock');
    } finally {
      setStockLoading(false);
    }
  }, [token, producto]);

  const cargarDatos = useCallback(async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      
      // Detectar si es reponedor
      const userType = localStorage.getItem('user_type');
      const esReponedor = userType === 'empleado';
      setIsReponedor(esReponedor);
      
      // Cargar datos base
      const [productoData, categoriasData] = await Promise.all([
        obtenerProducto(productId, token),
        obtenerCategoriasDisponibles(token)
      ]);
      

      
      setProducto(productoData);
      setEditedData({
        nombre: productoData.nombre,
        categoria: productoData.categoria,
        precio: productoData.precio,
        descripcion: productoData.descripcion || ""
      });
      
      setCategorias(categoriasData);
    } catch (err: unknown) {
      console.error('Error cargando datos:', err);
      setError('Error cargando datos del producto');
    } finally {
      setLoading(false);
    }
  }, [token, productId]);

  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    cargarDatos();
  }, [token, router, cargarDatos]);

  // useEffect separado para cargar stock completo después de tener el producto
  useEffect(() => {
    if (producto && token) {
      cargarStockCompleto();
    }
  }, [producto, token, cargarStockCompleto]);

  const handleSaveProduct = async () => {
    if (!token || !producto) return;
    
    // Validaciones
    if (editedData.precio && Number(editedData.precio) <= 0) {
      alert('El precio debe ser mayor a 0');
      return;
    }
    
    if (editedData.nombre && !editedData.nombre.trim()) {
      alert('El nombre del producto es obligatorio');
      return;
    }
    
    try {
      setSaving(true);
      const updatedProduct = await actualizarProducto(producto.id, editedData, token);
      setProducto(updatedProduct);
      setIsEditing(false);
      alert('Producto actualizado exitosamente');
    } catch (err: unknown) {
      console.error('Error actualizando producto:', err);
      const errorMessage = (err as any)?.response?.data?.precio?.[0] || 
                          (err as any)?.response?.data?.detail ||
                          (err as Error).message || 
                          'Error al actualizar producto';
      alert(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleCategoriaCreada = (nuevaCategoria: CategoriaSimple) => {
    setCategorias(prev => [...prev, nuevaCategoria]);
  };

  const handleGuardarTodoStock = async () => {
    if (!token || !producto) return;
    
    try {
      setSaving(true);
      
      // Preparar datos para enviar
      const stocksParaActualizar = Object.entries(stockEditado).map(([depositoId, stock]) => ({
        deposito_id: Number(depositoId),
        cantidad: stock.cantidad,
        cantidad_minima: stock.cantidad_minima
      }));
      
      await actualizarStockCompletoProducto(producto.id, stocksParaActualizar, token);
      await cargarDatos(); // Recargar datos del producto
      await cargarStockCompleto(); // Recargar stock completo
      alert('Stock actualizado exitosamente');
    } catch (err: unknown) {
      console.error('Error actualizando stock:', err);
      alert((err as Error).message || 'Error al actualizar stock');
    } finally {
      setSaving(false);
    }
  };

  const handleCambioStock = (depositoId: number, campo: 'cantidad' | 'cantidad_minima', valor: number) => {
    setStockEditado(prev => ({
      ...prev,
      [depositoId]: {
        ...prev[depositoId],
        [campo]: valor
      }
    }));
  };



  if (loading) {
    return (
      <Container size="xl">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-lightText">Cargando producto...</p>
          </div>
        </div>
      </Container>
    );
  }

  if (error || !producto) {
    return (
      <Container size="xl">
        <Card className="text-center py-12">
          <p className="text-red-600 mb-4">{error || 'Producto no encontrado'}</p>
          <Button onClick={() => router.push('/productos')}>Volver a Productos</Button>
        </Card>
      </Container>
    );
  }

  return (
    <Container size="xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => router.push('/productos')}
            className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center hover:bg-gray-200 transition-colors"
          >
            ←
          </button>
          <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/80 rounded-2xl flex items-center justify-center text-white text-2xl shadow-xl shadow-primary/30">
            🏷️
          </div>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-text mb-1">{producto.nombre}</h1>
            <p className="text-lightText">Gestionar información y stock del producto</p>
          </div>
          <div className="flex gap-2">
            {!isEditing ? (
              <Button onClick={() => setIsEditing(true)}>
                Editar Producto
              </Button>
            ) : (
              <>
                <Button variant="secondary" onClick={() => setIsEditing(false)}>
                  Cancelar
                </Button>
                <Button onClick={handleSaveProduct} disabled={saving}>
                  {saving ? 'Guardando...' : 'Guardar'}
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Información del Producto */}
        <div className="space-y-6">
          <Card>
            <h2 className="text-xl font-semibold text-text mb-4">Información del Producto</h2>
            
            {isEditing ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text mb-2">Nombre</label>
                  <Input
                    value={editedData.nombre}
                    onChange={(e) => setEditedData(prev => ({ ...prev, nombre: e.target.value }))}
                    placeholder="Nombre del producto"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text mb-2">Categoría</label>
                  <SelectorCategorias
                    categorias={categorias}
                    value={editedData.categoria}
                    onChange={(value) => setEditedData(prev => ({ ...prev, categoria: value }))}
                    onCategoriaCreada={handleCategoriaCreada}
                    placeholder="Seleccionar categoría"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text mb-2">Precio</label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={editedData.precio}
                    onChange={(e) => setEditedData(prev => ({ ...prev, precio: e.target.value }))}
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text mb-2">Descripción</label>
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    rows={3}
                    value={editedData.descripcion}
                    onChange={(e) => setEditedData(prev => ({ ...prev, descripcion: e.target.value }))}
                    placeholder="Descripción del producto..."
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-lightText">Categoría</p>
                    <p className="font-medium">{producto.categoria_nombre}</p>
                  </div>
                  <div>
                    <p className="text-sm text-lightText">Precio</p>
                    <p className="font-medium text-primary text-lg">${producto.precio}</p>
                  </div>
                </div>
                
                {producto.descripcion && (
                  <div>
                    <p className="text-sm text-lightText mb-1">Descripción</p>
                    <p className="text-text">{producto.descripcion}</p>
                  </div>
                )}
                
                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div>
                    <p className="text-sm text-lightText">Estado</p>
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      producto.activo ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {producto.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-lightText">Stock Total</p>
                    <p className="font-medium text-lg">{producto.stock_total}</p>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Gestión de Stock */}
        <div className="space-y-6">
          <Card>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-text">Stock por Depósito</h2>
              <Button
                onClick={handleGuardarTodoStock}
                disabled={saving || stockLoading}
                variant="primary"
              >
                {saving ? 'Guardando...' : 'Guardar'}
              </Button>
            </div>

            {stockLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                <p className="text-lightText">Cargando información de stock...</p>
              </div>
            ) : stockCompleto.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-lightText mb-4">No hay depósitos configurados</p>
              </div>
            ) : (
              <div className="space-y-4">
                {stockCompleto.map((stock) => (
                  <div key={stock.deposito_id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-medium text-text">{stock.deposito_nombre}</h3>
                        <p className="text-sm text-lightText">{stock.deposito_direccion}</p>
                      </div>
                      <div className="flex gap-2">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          stock.tiene_stock ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {stock.tiene_stock ? 'Con Stock' : 'Sin Stock'}
                        </span>
                        {stock.stock_bajo && (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                            Stock Bajo
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-text mb-1">Cantidad</label>
                        <Input
                          type="number"
                          min="0"
                          value={stockEditado[stock.deposito_id]?.cantidad ?? stock.cantidad}
                          onChange={(e) => handleCambioStock(stock.deposito_id, 'cantidad', Number(e.target.value))}
                          className="w-full"
                        />
                      </div>
                      
                      {!isReponedor && (
                        <div>
                          <label className="block text-sm font-medium text-text mb-1">Stock Mínimo</label>
                          <Input
                            type="number"
                            min="0"
                            value={stockEditado[stock.deposito_id]?.cantidad_minima ?? stock.cantidad_minima}
                            onChange={(e) => handleCambioStock(stock.deposito_id, 'cantidad_minima', Number(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      )}
                    </div>
                    
                    {stock.fecha_modificacion && (
                      <p className="text-xs text-lightText mt-2">
                        {isReponedor && `Mínimo: ${stock.cantidad_minima} | `}
                        Actualizado: {new Date(stock.fecha_modificacion).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>


        </div>
      </div>
    </Container>
  );
}
