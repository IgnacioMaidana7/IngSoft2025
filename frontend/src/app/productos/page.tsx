'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import FiltroCategorias from '@/components/productos/FiltroCategorias';
import { 
  obtenerProductos, 
  obtenerCategoriasDisponibles, 
  obtenerDepositos, 
  actualizarProducto,
  type ProductoList,
  type CategoriaSimple,
  type Deposito
} from '@/lib/api';

// Hook personalizado para debounce
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default function ProductosPage() {
  const { isLoggedIn, token } = useAuth();
  const router = useRouter();
  
  const [productos, setProductos] = useState<ProductoList[]>([]);
  const [categorias, setCategorias] = useState<CategoriaSimple[]>([]);
  const [depositos, setDepositos] = useState<Deposito[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filtros y paginación
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategoria, setSelectedCategoria] = useState<number | ''>('');
  const [selectedDeposito, setSelectedDeposito] = useState<number | ''>('');
  const [activoFilter, setActivoFilter] = useState<boolean | ''>(''); // Cambiado de tab a filtro
  type StockOp = 'sin-stock' | 'bajo' | 'normal' | '';
  const [stockFilter, setStockFilter] = useState<StockOp>('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Debounce del término de búsqueda para evitar muchas llamadas a la API
  const debouncedSearchTerm = useDebounce(searchTerm, 500); // 500ms de retraso

  const loadData = useCallback(async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      setError(null);

      // Cargar datos básicos
      const [categoriasData, depositosData] = await Promise.all([
        obtenerCategoriasDisponibles(token),
        obtenerDepositos(token)
      ]);

      setCategorias(categoriasData);
      setDepositos(depositosData);

      // Cargar productos con filtros
      const filters: {
        search?: string;
        categoria?: number;
        deposito?: number;
        activo?: boolean;
        stock?: string;
      } = {};
      if (debouncedSearchTerm) filters.search = debouncedSearchTerm;
      if (selectedCategoria) filters.categoria = selectedCategoria;
      if (selectedDeposito) filters.deposito = selectedDeposito;
      // Filtro activo/inactivo
      if (activoFilter !== '') {
        filters.activo = activoFilter;
      }
      // Filtro de stock por nivel
      if (stockFilter) {
        filters.stock = stockFilter;
      }

      const productosData = await obtenerProductos(token, currentPage, filters);
      
      setProductos(productosData.results);
      setTotalCount(productosData.count);
      setTotalPages(Math.ceil(productosData.count / 10)); // Asumiendo 10 items por página

    } catch (err) {
      console.error('Error loading data:', err);
      setError('Error al cargar los datos. Por favor, intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  }, [token, debouncedSearchTerm, selectedCategoria, selectedDeposito, activoFilter, stockFilter, currentPage]);

  useEffect(() => {
    if (!isLoggedIn || !token) {
      router.push('/login');
      return;
    }
    loadData();
  }, [loadData, token, isLoggedIn, router]);

  const handleToggleActive = async (id: number, currentState: boolean) => {
    const action = currentState ? 'deshabilitar' : 'habilitar';
    if (!confirm(`¿Estás seguro de que quieres ${action} este producto?`)) {
      return;
    }

    try {
      await actualizarProducto(id, { activo: !currentState }, token!);
      await loadData(); // Recargar la lista
    } catch (err) {
      console.error(`Error ${action}ing product:`, err);
      alert(`Error al ${action} el producto`);
    }
  };

  const resetFilters = () => {
    setSearchTerm('');
    setSelectedCategoria('');
    setSelectedDeposito('');
    setActivoFilter('');
    setStockFilter('');
    setCurrentPage(1);
  };

  // Resetear página cuando cambian los filtros
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearchTerm, selectedCategoria, selectedDeposito, activoFilter, stockFilter]);

  if (!isLoggedIn || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Productos</h1>
          <button
            onClick={() => router.push('/productos/nuevo')}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
          >
            Nuevo Producto
          </button>
          </div>
        </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Filtros</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Buscar por nombre
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Nombre del producto..."
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categoría
            </label>
            <FiltroCategorias
              categorias={categorias}
              value={selectedCategoria}
              onChange={setSelectedCategoria}
              placeholder="Todas las categorías"
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Depósito
            </label>
            <select
              value={selectedDeposito}
              onChange={(e) => setSelectedDeposito(e.target.value ? Number(e.target.value) : '')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los depósitos</option>
              {depositos.map((deposito) => (
                <option key={deposito.id} value={deposito.id}>
                  {deposito.nombre}
                </option>
              ))}
            </select>
          </div>

          {/* Filtro de Estado */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Estado
            </label>
            <select
              value={activoFilter === '' ? '' : activoFilter ? 'activo' : 'inactivo'}
              onChange={(e) => setActivoFilter(e.target.value === '' ? '' : e.target.value === 'activo')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los estados</option>
              <option value="activo">Activos</option>
              <option value="inactivo">Inactivos</option>
            </select>
          </div>

          {/* Filtro de Stock */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nivel de Stock
            </label>
            <select
              value={stockFilter}
              onChange={(e) => setStockFilter(e.target.value as StockOp)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los niveles</option>
              <option value="sin-stock">Sin Stock (0 unidades)</option>
              <option value="bajo">Stock Bajo (&lt; Stock Mínimo)</option>
              <option value="normal">Stock Normal (&gt;= Stock Mínimo)</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={resetFilters}
              className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
            >
              Limpiar Filtros
            </button>
          </div>
        </div>
      </div>

      {/* Lista de productos */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">
            Productos ({totalCount} total{totalCount !== 1 ? 'es' : ''})
          </h2>
        </div>

        {productos.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No se encontraron productos.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nombre
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Categoría
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Precio
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stock Total
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {productos.map((producto) => (
                  <tr key={producto.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {producto.nombre}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {producto.categoria_nombre}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${parseFloat(producto.precio).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {producto.stock_total}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          producto.activo
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {producto.activo ? 'Activo' : 'Inactivo'}
                        </span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          producto.stock_nivel === 'sin-stock'
                            ? 'bg-red-100 text-red-800'
                            : producto.stock_nivel === 'bajo'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {producto.stock_nivel === 'sin-stock' 
                            ? 'Sin Stock' 
                            : producto.stock_nivel === 'bajo' 
                            ? 'Stock Bajo' 
                            : 'Stock Normal'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => router.push(`/productos/${producto.id}`)}
                        className="text-indigo-600 hover:text-indigo-900"
                      >
                        Ver/Editar
                      </button>
                      <button
                        onClick={() => handleToggleActive(producto.id, producto.activo)}
                        className={producto.activo ? "text-red-600 hover:text-red-900" : "text-green-600 hover:text-green-900"}
                      >
                        {producto.activo ? 'Deshabilitar' : 'Habilitar'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Paginación */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Página {currentPage} de {totalPages}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Siguiente
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
