import { useState, useCallback } from 'react';
import {
  crearVenta,
  agregarProductoAVenta,
  actualizarItemVenta,
  eliminarItemVenta,
  finalizarVenta,
  cancelarVenta,
  type Venta,
  type ProductoDisponible
} from '@/lib/api';

export interface UseVentasReturn {
  ventaActual: Venta | null;
  cargando: boolean;
  error: string | null;
  
  // Acciones
  iniciarNuevaVenta: () => Promise<void>;
  agregarProducto: (producto: ProductoDisponible, cantidad?: number) => Promise<void>;
  actualizarCantidadItem: (itemId: number, nuevaCantidad: number) => Promise<void>;
  eliminarItem: (itemId: number) => Promise<void>;
  finalizarVentaActual: (telefono?: string, observaciones?: string, enviarWhatsapp?: boolean) => Promise<void>;
  cancelarVentaActual: () => Promise<void>;
  limpiarVenta: () => void;
}

export function useVentas(token: string | null): UseVentasReturn {
  const [ventaActual, setVentaActual] = useState<Venta | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const iniciarNuevaVenta = useCallback(async () => {
    if (!token) {
      setError('No hay token de autenticación');
      return;
    }

    try {
      setCargando(true);
      setError(null);
      const nuevaVenta = await crearVenta({}, token);
      setVentaActual(nuevaVenta);
    } catch (err: any) {
      const errorMessage = err.message || 'Error al crear venta';
      setError(errorMessage);
      throw err;
    } finally {
      setCargando(false);
    }
  }, [token]);

  const agregarProducto = useCallback(async (producto: ProductoDisponible, cantidad: number = 1) => {
    if (!token) {
      setError('No hay token de autenticación');
      return;
    }

    // Si no hay venta actual, crear una nueva
    if (!ventaActual) {
      await iniciarNuevaVenta();
      return;
    }

    try {
      setCargando(true);
      setError(null);
      const resultado = await agregarProductoAVenta(
        ventaActual.id,
        { producto_id: producto.id, cantidad },
        token
      );
      setVentaActual(resultado.venta);
    } catch (err: any) {
      const errorMessage = err.message || 'Error al agregar producto';
      setError(errorMessage);
      throw err;
    } finally {
      setCargando(false);
    }
  }, [token, ventaActual, iniciarNuevaVenta]);

  const actualizarCantidadItem = useCallback(async (itemId: number, nuevaCantidad: number) => {
    if (!ventaActual || !token || nuevaCantidad < 1) return;

    try {
      setCargando(true);
      setError(null);
      const resultado = await actualizarItemVenta(
        ventaActual.id,
        { item_id: itemId, cantidad: nuevaCantidad },
        token
      );
      setVentaActual(resultado.venta);
    } catch (err: any) {
      const errorMessage = err.message || 'Error al actualizar cantidad';
      setError(errorMessage);
      throw err;
    } finally {
      setCargando(false);
    }
  }, [ventaActual, token]);

  const eliminarItem = useCallback(async (itemId: number) => {
    if (!ventaActual || !token) return;

    try {
      setCargando(true);
      setError(null);
      const resultado = await eliminarItemVenta(ventaActual.id, itemId, token);
      setVentaActual(resultado.venta);
    } catch (err: any) {
      const errorMessage = err.message || 'Error al eliminar producto';
      setError(errorMessage);
      throw err;
    } finally {
      setCargando(false);
    }
  }, [ventaActual, token]);

  const finalizarVentaActual = useCallback(async (
    telefono?: string,
    observaciones?: string,
    enviarWhatsapp: boolean = false
  ) => {
    if (!ventaActual || !token) return;

    try {
      setCargando(true);
      setError(null);
      const resultado = await finalizarVenta(
        ventaActual.id,
        {
          cliente_telefono: telefono,
          observaciones,
          enviar_whatsapp: enviarWhatsapp
        },
        token
      );
      setVentaActual(resultado.venta);
    } catch (err: any) {
      const errorMessage = err.message || 'Error al finalizar venta';
      setError(errorMessage);
      throw err;
    } finally {
      setCargando(false);
    }
  }, [ventaActual, token]);

  const cancelarVentaActual = useCallback(async () => {
    if (!ventaActual || !token) return;

    try {
      setCargando(true);
      setError(null);
      await cancelarVenta(ventaActual.id, token);
      setVentaActual(null);
    } catch (err: any) {
      const errorMessage = err.message || 'Error al cancelar venta';
      setError(errorMessage);
      throw err;
    } finally {
      setCargando(false);
    }
  }, [ventaActual, token]);

  const limpiarVenta = useCallback(() => {
    setVentaActual(null);
    setError(null);
  }, []);

  return {
    ventaActual,
    cargando,
    error,
    iniciarNuevaVenta,
    agregarProducto,
    actualizarCantidadItem,
    eliminarItem,
    finalizarVentaActual,
    cancelarVentaActual,
    limpiarVenta
  };
}