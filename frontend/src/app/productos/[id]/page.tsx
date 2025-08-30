"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter, useParams } from "next/navigation";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { 
  obtenerProducto,
  actualizarProducto,
  obtenerCategoriasDisponibles,
  obtenerDepositos,
  gestionarStockProducto,
  actualizarStockProducto,
  CategoriaSimple,
  Deposito,
  Producto
} from "@/lib/api";

export default function ProductoDetailPage() {
  const { token } = useAuth();
  const router = useRouter();
  const params = useParams();
  const productId = Number(params.id);
  
  const [producto, setProducto] = useState<Producto | null>(null);
  const [categorias, setCategorias] = useState<CategoriaSimple[]>([]);
  const [depositos, setDepositos] = useState<Deposito[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Estados para edición
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState({
    nombre: "",
    categoria: 0,
    precio: "",
    descripcion: ""
  });

  // Estados para gestión de stock
  const [showAddStock, setShowAddStock] = useState(false);
  const [newStock, setNewStock] = useState({
    deposito: 0,
    cantidad: 0,
    cantidad_minima: 0
  });

  const cargarDatos = useCallback(async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      const [productoData, categoriasData, depositosData] = await Promise.all([
        obtenerProducto(productId, token),
        obtenerCategoriasDisponibles(token),
        obtenerDepositos(token)
      ]);
      
      setProducto(productoData);
      setEditedData({
        nombre: productoData.nombre,
        categoria: productoData.categoria,
        precio: productoData.precio,
        descripcion: productoData.descripcion || ""
      });
      
      setCategorias(categoriasData);
      setDepositos(depositosData);
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

  const handleSaveProduct = async () => {
    if (!token || !producto) return;
    
    try {
      setSaving(true);
      const updatedProduct = await actualizarProducto(producto.id, editedData, token);
      setProducto(updatedProduct);
      setIsEditing(false);
      alert('Producto actualizado exitosamente');
    } catch (err: unknown) {
      console.error('Error actualizando producto:', err);
      alert((err as Error).message || 'Error al actualizar producto');
    } finally {
      setSaving(false);
    }
  };

  const handleAddStock = async () => {
    if (!token || !producto) return;
    
    if (!newStock.deposito) {
      alert('Debes seleccionar un depósito');
      return;
    }

    try {
      setSaving(true);
      await gestionarStockProducto(producto.id, newStock, token);
      await cargarDatos(); // Recargar datos
      setShowAddStock(false);
      setNewStock({ deposito: 0, cantidad: 0, cantidad_minima: 0 });
      alert('Stock agregado exitosamente');
    } catch (err: unknown) {
      console.error('Error agregando stock:', err);
      alert((err as Error).message || 'Error al agregar stock');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStock = async (stockId: number, cantidad: number) => {
    if (!token) return;
    
    try {
      await actualizarStockProducto(stockId, { cantidad }, token);
      await cargarDatos(); // Recargar datos
      alert('Stock actualizado exitosamente');
    } catch (err: unknown) {
      console.error('Error actualizando stock:', err);
      alert((err as Error).message || 'Error al actualizar stock');
    }
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
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    value={editedData.categoria}
                    onChange={(e) => setEditedData(prev => ({ ...prev, categoria: Number(e.target.value) }))}
                  >
                    {categorias.map((categoria) => (
                      <option key={categoria.id} value={categoria.id}>
                        {categoria.nombre}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text mb-2">Precio</label>
                  <Input
                    type="number"
                    step="0.01"
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
                variant="secondary"
                size="sm"
                onClick={() => setShowAddStock(true)}
              >
                Agregar Stock
              </Button>
            </div>

            {producto.stocks.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-lightText mb-4">No hay stock registrado en ningún depósito</p>
                <Button onClick={() => setShowAddStock(true)}>
                  Agregar Primer Stock
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {producto.stocks.map((stock) => (
                  <div key={stock.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-medium text-text">{stock.deposito_nombre}</h3>
                        <p className="text-sm text-lightText">{stock.deposito_direccion}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-primary">{stock.cantidad}</p>
                        <p className="text-xs text-lightText">unidades</p>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
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
                      
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          min="0"
                          defaultValue={stock.cantidad}
                          className="w-20"
                          onBlur={(e) => {
                            const newValue = Number(e.target.value);
                            if (newValue !== stock.cantidad) {
                              handleUpdateStock(stock.id, newValue);
                            }
                          }}
                        />
                      </div>
                    </div>
                    
                    <p className="text-xs text-lightText mt-2">
                      Mínimo: {stock.cantidad_minima} | Actualizado: {new Date(stock.fecha_modificacion).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Modal para agregar stock */}
          {showAddStock && (
            <Card>
              <h3 className="text-lg font-semibold text-text mb-4">Agregar Stock</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text mb-2">Depósito</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    value={newStock.deposito}
                    onChange={(e) => setNewStock(prev => ({ ...prev, deposito: Number(e.target.value) }))}
                  >
                    <option value={0}>Seleccionar depósito</option>
                    {depositos
                      .filter(deposito => !producto.stocks.some(stock => stock.deposito === deposito.id))
                      .map((deposito) => (
                        <option key={deposito.id} value={deposito.id}>
                          {deposito.nombre} - {deposito.direccion}
                        </option>
                      ))}
                  </select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text mb-2">Cantidad</label>
                    <Input
                      type="number"
                      min="0"
                      value={newStock.cantidad}
                      onChange={(e) => setNewStock(prev => ({ ...prev, cantidad: Number(e.target.value) }))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text mb-2">Stock Mínimo</label>
                    <Input
                      type="number"
                      min="0"
                      value={newStock.cantidad_minima}
                      onChange={(e) => setNewStock(prev => ({ ...prev, cantidad_minima: Number(e.target.value) }))}
                    />
                  </div>
                </div>
                
                <div className="flex justify-end gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => setShowAddStock(false)}
                  >
                    Cancelar
                  </Button>
                  <Button
                    onClick={handleAddStock}
                    disabled={saving}
                  >
                    {saving ? 'Agregando...' : 'Agregar Stock'}
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </Container>
  );
}
