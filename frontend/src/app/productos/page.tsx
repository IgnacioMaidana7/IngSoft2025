'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { 
  obtenerProductos, 
  obtenerCategoriasDisponibles, 
  obtenerDepositos, 
  eliminarProducto,
  type ProductoList,
  type CategoriaSimple,
  type Deposito
} from '@/lib/api';

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
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

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
      } = {};
      if (searchTerm) filters.search = searchTerm;
      if (selectedCategoria) filters.categoria = selectedCategoria;
      if (selectedDeposito) filters.deposito = selectedDeposito;

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
  }, [token, searchTerm, selectedCategoria, selectedDeposito, currentPage]);

  useEffect(() => {
    if (!isLoggedIn || !token) {
      router.push('/login');
      return;
    }
    loadData();
  }, [loadData, token, isLoggedIn, router]);

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de que quieres deshabilitar este producto?')) {
      return;
    }

    try {
      await eliminarProducto(id, token!);
      await loadData(); // Recargar la lista
    } catch (err) {
      console.error('Error deleting product:', err);
      alert('Error al deshabilitar el producto');
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadData();
  };

  const resetFilters = () => {
    setSearchTerm('');
    setSelectedCategoria('');
    setSelectedDeposito('');
    setCurrentPage(1);
  };

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

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Filtros</h2>
        
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
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
            <select
              value={selectedCategoria}
              onChange={(e) => setSelectedCategoria(e.target.value ? Number(e.target.value) : '')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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

          <div className="flex gap-2">
            <button
              type="submit"
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
              Buscar
            </button>
            <button
              type="button"
              onClick={resetFilters}
              className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
            >
              Limpiar
            </button>
          </div>
        </form>
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
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        producto.activo
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {producto.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => router.push(`/productos/${producto.id}`)}
                        className="text-indigo-600 hover:text-indigo-900"
                      >
                        Ver/Editar
                      </button>
                      {producto.activo && (
                        <button
                          onClick={() => handleDelete(producto.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Deshabilitar
                        </button>
                      )}
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
