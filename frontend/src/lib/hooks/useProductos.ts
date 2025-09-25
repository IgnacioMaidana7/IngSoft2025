import { useState, useEffect, useCallback } from 'react';
import { obtenerProductosDisponibles, buscarProductos, type ProductoDisponible } from '@/lib/api';

export interface UseProductosReturn {
  productos: ProductoDisponible[];
  productosFiltrados: ProductoDisponible[];
  cargando: boolean;
  error: string | null;
  busqueda: string;
  
  // Acciones
  setBusqueda: (query: string) => void;
  recargarProductos: () => Promise<void>;
  buscarProductosEnTiempoReal: (query: string) => Promise<void>;
}

export function useProductos(token: string | null): UseProductosReturn {
  const [productos, setProductos] = useState<ProductoDisponible[]>([]);
  const [productosFiltrados, setProductosFiltrados] = useState<ProductoDisponible[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState('');

  // Cargar productos al inicializar
  useEffect(() => {
    if (token) {
      recargarProductos();
    }
  }, [token]);

  // Filtrar productos cuando cambie la búsqueda
  useEffect(() => {
    if (busqueda.trim().length >= 2) {
      buscarProductosEnTiempoReal(busqueda);
    } else {
      setProductosFiltrados(productos.slice(0, 20));
    }
  }, [busqueda, productos]);

  const recargarProductos = useCallback(async () => {
    if (!token) return;

    try {
      setCargando(true);
      setError(null);
      const productosObtenidos = await obtenerProductosDisponibles(token);
      setProductos(productosObtenidos);
      setProductosFiltrados(productosObtenidos.slice(0, 20));
    } catch (err: any) {
      const errorMessage = err.message || 'Error al cargar productos';
      setError(errorMessage);
      console.error('Error cargando productos:', err);
    } finally {
      setCargando(false);
    }
  }, [token]);

  const buscarProductosEnTiempoReal = useCallback(async (query: string) => {
    if (!token || query.trim().length < 2) return;

    try {
      setError(null);
      const productosEncontrados = await buscarProductos(query.trim(), token);
      setProductosFiltrados(productosEncontrados);
    } catch (err: any) {
      console.error('Error en búsqueda:', err);
      // No mostrar error para búsquedas, solo filtrar por productos existentes
      const filtrados = productos.filter(p => 
        p.nombre.toLowerCase().includes(query.toLowerCase()) ||
        p.categoria.toLowerCase().includes(query.toLowerCase())
      );
      setProductosFiltrados(filtrados);
    }
  }, [token, productos]);

  return {
    productos,
    productosFiltrados,
    cargando,
    error,
    busqueda,
    setBusqueda,
    recargarProductos,
    buscarProductosEnTiempoReal
  };
}