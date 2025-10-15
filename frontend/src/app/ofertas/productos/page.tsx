"use client";
import React, { useState, useEffect } from "react";
import { COLORS } from "@/constants/colors";
import Button from "@/components/ui/Button";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import { useToast } from "@/components/feedback/ToastProvider";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import {
  obtenerOfertas,
  obtenerProductosConOfertas,
  asignarProductosAOferta,
  quitarProductosDeOferta,
  obtenerCategoriasDisponibles,
  type OfertaList,
  type ProductoConOferta,
  type CategoriaSimple
} from "@/lib/api";

// Componente para cada producto
function ProductoItem({ 
  producto, 
  seleccionado, 
  onToggleSelect 
}: {
  producto: ProductoConOferta;
  seleccionado: boolean;
  onToggleSelect: () => void;
}) {
  const tieneOferta = producto.tiene_ofertas_activas;
  const descuento = tieneOferta ? 
    ((parseFloat(producto.precio) - parseFloat(producto.precio_con_descuento)) / parseFloat(producto.precio) * 100).toFixed(1) : 0;

  return (
    <div className={`border rounded-xl p-4 bg-white transition-colors ${
      seleccionado ? 'border-primary bg-blue-50' : 'border-border hover:border-gray-300'
    }`}>
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={seleccionado}
          onChange={onToggleSelect}
          className="mt-1"
        />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-text">{producto.nombre}</h3>
            {tieneOferta && (
              <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded-full">
                Con Oferta
              </span>
            )}
          </div>
          
          <p className="text-sm text-lightText mb-2">Categoría: {producto.categoria}</p>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-lightText">Precio original:</span>
              <span className={`ml-1 font-medium ${tieneOferta ? 'line-through text-gray-500' : 'text-text'}`}>
                ${producto.precio}
              </span>
            </div>
            {tieneOferta && (
              <div>
                <span className="text-lightText">Precio con oferta:</span>
                <span className="ml-1 font-medium text-green-600">
                  ${producto.precio_con_descuento} (-{descuento}%)
                </span>
              </div>
            )}
          </div>
          
          {tieneOferta && producto.ofertas_aplicadas.length > 0 && (
            <div className="mt-2">
              <span className="text-xs text-lightText">Ofertas aplicadas:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {producto.ofertas_aplicadas.map((oferta) => (
                  <span key={oferta.id} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {oferta.oferta_nombre}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function OfertasProductosPage() {
  const { token } = useAuth();
  const { showToast } = useToast();
  const router = useRouter();
  
  const [ofertas, setOfertas] = useState<OfertaList[]>([]);
  const [productos, setProductos] = useState<ProductoConOferta[]>([]);
  const [categorias, setCategorias] = useState<CategoriaSimple[]>([]);
  
  const [ofertaSeleccionada, setOfertaSeleccionada] = useState<number | null>(null);
  const [productosSeleccionados, setProductosSeleccionados] = useState<number[]>([]);
  
  const [cargandoOfertas, setCargandoOfertas] = useState(true);
  const [cargandoProductos, setCargandoProductos] = useState(false);
  const [procesando, setProcesando] = useState(false);
  
  // Filtros
  const [filtroCategoria, setFiltroCategoria] = useState<number | null>(null);
  const [filtroEstadoOferta, setFiltroEstadoOferta] = useState<'con_oferta' | 'sin_oferta' | ''>('');

  // Cargar ofertas activas
  const cargarOfertas = async () => {
    if (!token) return;
    
    try {
      setCargandoOfertas(true);
      const response = await obtenerOfertas(token, 1, { estado: 'activa' });
      setOfertas(response.results);
    } catch (error) {
      console.error('Error cargando ofertas:', error);
      showToast('Error al cargar ofertas', 'error');
    } finally {
      setCargandoOfertas(false);
    }
  };

  // Cargar categorías
  const cargarCategorias = async () => {
    if (!token) return;
    
    try {
      const categoriasData = await obtenerCategoriasDisponibles(token);
      setCategorias(categoriasData);
    } catch (error) {
      console.error('Error cargando categorías:', error);
    }
  };

  // Cargar productos
  const cargarProductos = async () => {
    if (!token) return;
    
    try {
      setCargandoProductos(true);
      const filtros: any = {};
      
      if (filtroCategoria) filtros.categoria = filtroCategoria;
      if (filtroEstadoOferta) filtros.estado_oferta = filtroEstadoOferta;
      
      const productosData = await obtenerProductosConOfertas(token, filtros);
      setProductos(productosData);
    } catch (error) {
      console.error('Error cargando productos:', error);
      showToast('Error al cargar productos', 'error');
    } finally {
      setCargandoProductos(false);
    }
  };

  // Efectos
  useEffect(() => {
    if (token) {
      cargarOfertas();
      cargarCategorias();
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      cargarProductos();
    }
  }, [token, filtroCategoria, filtroEstadoOferta]);

  // Handlers
  const handleToggleProducto = (productoId: number) => {
    setProductosSeleccionados(prev => 
      prev.includes(productoId) 
        ? prev.filter(id => id !== productoId)
        : [...prev, productoId]
    );
  };

  const handleSeleccionarTodos = () => {
    if (productosSeleccionados.length === productos.length) {
      setProductosSeleccionados([]);
    } else {
      setProductosSeleccionados(productos.map(p => p.id));
    }
  };

  const handleAsignarOferta = async () => {
    if (!ofertaSeleccionada || productosSeleccionados.length === 0 || !token) return;
    
    setProcesando(true);
    
    try {
      const response = await asignarProductosAOferta(ofertaSeleccionada, productosSeleccionados, token);
      showToast(response.message, 'success');
      
      if (response.errores && response.errores.length > 0) {
        response.errores.forEach(error => showToast(error, 'error'));
      }
      
      // Recargar productos para ver los cambios
      await cargarProductos();
      setProductosSeleccionados([]);
    } catch (error: any) {
      console.error('Error asignando oferta:', error);
      showToast(error.message || 'Error al asignar oferta', 'error');
    } finally {
      setProcesando(false);
    }
  };

  const handleQuitarOfertas = async () => {
    if (!ofertaSeleccionada || productosSeleccionados.length === 0 || !token) return;
    
    if (!confirm('¿Estás seguro de que quieres quitar las ofertas de los productos seleccionados?')) {
      return;
    }
    
    setProcesando(true);
    
    try {
      const response = await quitarProductosDeOferta(ofertaSeleccionada, productosSeleccionados, token);
      showToast(response.message, 'success');
      
      // Recargar productos para ver los cambios
      await cargarProductos();
      setProductosSeleccionados([]);
    } catch (error: any) {
      console.error('Error quitando ofertas:', error);
      showToast(error.message || 'Error al quitar ofertas', 'error');
    } finally {
      setProcesando(false);
    }
  };

  return (
    <ProtectedRoute>
      <Container>
        <Card>
          <div style={{ paddingBottom: 12, borderBottom: `1px solid ${COLORS.border}`, marginBottom: 12 }}>
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold text-text">Aplicar Ofertas a Productos</h1>
              <Button 
                variant="secondary" 
                onClick={() => router.push('/ofertas')}
              >
                Volver a Ofertas
              </Button>
            </div>
          </div>

          {/* Selector de oferta */}
          <div className="mb-6">
            <label className="block mb-2 font-medium text-text">Seleccionar Oferta Activa</label>
            {cargandoOfertas ? (
              <p className="text-lightText">Cargando ofertas...</p>
            ) : ofertas.length === 0 ? (
              <p className="text-lightText">No hay ofertas activas disponibles</p>
            ) : (
              <select
                className="w-full px-3 py-2 border border-border rounded-xl"
                value={ofertaSeleccionada || ''}
                onChange={(e) => setOfertaSeleccionada(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">Selecciona una oferta...</option>
                {ofertas.map((oferta) => (
                  <option key={oferta.id} value={oferta.id}>
                    {oferta.nombre} - {oferta.tipo_descuento === 'porcentaje' ? `${oferta.valor_descuento}%` : `$${oferta.valor_descuento}`}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Filtros */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block mb-2 font-medium text-text">Categoría</label>
              <select
                className="w-full px-3 py-2 border border-border rounded-xl"
                value={filtroCategoria || ''}
                onChange={(e) => setFiltroCategoria(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">Todas las categorías</option>
                {categorias.map((categoria) => (
                  <option key={categoria.id} value={categoria.id}>
                    {categoria.nombre}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block mb-2 font-medium text-text">Estado de Oferta</label>
              <select
                className="w-full px-3 py-2 border border-border rounded-xl"
                value={filtroEstadoOferta}
                onChange={(e) => setFiltroEstadoOferta(e.target.value as any)}
              >
                <option value="">Todos los productos</option>
                <option value="con_oferta">Con oferta</option>
                <option value="sin_oferta">Sin oferta</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button
                onClick={cargarProductos}
                variant="secondary"
                disabled={cargandoProductos}
                className="w-full"
              >
                {cargandoProductos ? 'Cargando...' : 'Actualizar'}
              </Button>
            </div>
          </div>

          {/* Controles de selección */}
          {productos.length > 0 && (
            <div className="flex justify-between items-center mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-4">
                <Button
                  onClick={handleSeleccionarTodos}
                  variant="ghost"
                  size="sm"
                >
                  {productosSeleccionados.length === productos.length ? 'Deseleccionar Todos' : 'Seleccionar Todos'}
                </Button>
                <span className="text-sm text-lightText">
                  {productosSeleccionados.length} de {productos.length} seleccionados
                </span>
              </div>
              
              <div className="flex gap-2">
                <Button
                  onClick={handleAsignarOferta}
                  disabled={!ofertaSeleccionada || productosSeleccionados.length === 0 || procesando}
                  size="sm"
                >
                  {procesando ? 'Procesando...' : 'Asignar Oferta'}
                </Button>
                <Button
                  onClick={handleQuitarOfertas}
                  disabled={!ofertaSeleccionada || productosSeleccionados.length === 0 || procesando}
                  variant="secondary"
                  size="sm"
                >
                  Quitar Ofertas
                </Button>
              </div>
            </div>
          )}

          {/* Lista de productos */}
          {cargandoProductos ? (
            <div className="text-center p-8">
              <p className="text-lightText">Cargando productos...</p>
            </div>
          ) : productos.length === 0 ? (
            <div className="text-center p-8">
              <p className="text-lightText">No se encontraron productos con los filtros aplicados</p>
            </div>
          ) : (
            <div className="space-y-3">
              {productos.map((producto) => (
                <ProductoItem
                  key={producto.id}
                  producto={producto}
                  seleccionado={productosSeleccionados.includes(producto.id)}
                  onToggleSelect={() => handleToggleProducto(producto.id)}
                />
              ))}
            </div>
          )}
        </Card>
      </Container>
    </ProtectedRoute>
  );
}