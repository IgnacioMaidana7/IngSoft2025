"use client";
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { crearTransferencia, obtenerDepositosDisponibles, obtenerProductosConStock } from '@/lib/transferenciasApi';
import type { 
  TransferenciaForm, 
  DetalleTransferenciaForm, 
  TransferenciaFormErrors, 
  DepositoOption, 
  ProductoOption 
} from '@/types/transferencias';
import Container from '@/components/layout/Container';
import Card from '@/components/layout/Card';
import Button from '@/components/ui/Button';
import CameraCapture from '@/components/CameraCapture';
import { useToast } from '@/components/feedback/ToastProvider';
import type { ProductoDetectado, ReconocimientoResponse } from '@/lib/api';
import { COLORS } from '@/constants/colors';

export default function NuevaTransferenciaPage() {
  const router = useRouter();
  const { token } = useAuth();
  const { showToast } = useToast();
  
  // Obtener información del empleado si es reponedor
  const [empleadoInfo, setEmpleadoInfo] = useState<{
    puesto: string;
    deposito_id: number | null;
    deposito_nombre: string | null;
  } | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const info = localStorage.getItem('empleado_info');
      if (info) {
        const parsed = JSON.parse(info);
        setEmpleadoInfo({
          puesto: parsed.puesto,
          deposito_id: parsed.deposito_id,
          deposito_nombre: parsed.deposito_nombre
        });
      }
    }
  }, []);
  
  const [form, setForm] = useState<TransferenciaForm>({
    deposito_origen: '',
    deposito_destino: '',
    fecha_transferencia: new Date().toISOString().slice(0, 16),
    observaciones: '',
    detalles: []
  });
  
  const [depositos, setDepositos] = useState<DepositoOption[]>([]);
  const [productosDisponibles, setProductosDisponibles] = useState<ProductoOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<TransferenciaFormErrors>({});
  const [step, setStep] = useState(1); // 1: configuración, 2: productos
  
  // Estados para reconocimiento de productos
  const [isCameraModalOpen, setIsCameraModalOpen] = useState(false);
  const [reconociendo, setReconociendo] = useState(false);
  const [productosDetectados, setProductosDetectados] = useState<ProductoDetectado[]>([]);
  const [mostrarProductosDetectados, setMostrarProductosDetectados] = useState(false);
  const [cantidadesDetectados, setCantidadesDetectados] = useState<{ [key: number]: number }>({});

  const cargarDepositos = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await obtenerDepositosDisponibles(token);
      if (response.success && response.data) {
        const opciones = response.data.map(deposito => ({
          value: deposito.id,
          label: deposito.nombre,
          direccion: deposito.direccion
        }));
        setDepositos(opciones);
      }
    } catch (error) {
      console.error('Error cargando depósitos:', error);
    }
  }, [token]);

  const cargarProductosDisponibles = useCallback(async (depositoId: number) => {
    if (!token) return;
    
    try {
      const stocks = await obtenerProductosConStock(depositoId, token);
      const opciones = stocks
        .filter(stock => stock.cantidad > 0) // Solo productos con stock
        .map(stock => ({
          value: stock.producto.id,
          label: stock.producto.nombre,
          categoria: stock.producto.categoria?.nombre || 'Sin categoría',
          stock_disponible: stock.cantidad
        }));
      setProductosDisponibles(opciones);
    } catch (error) {
      console.error('Error cargando productos:', error);
      setProductosDisponibles([]);
    }
  }, [token]);

  useEffect(() => {
    cargarDepositos();
  }, [cargarDepositos]);

  // Auto-seleccionar depósito de origen si es reponedor
  useEffect(() => {
    if (empleadoInfo?.puesto === 'REPONEDOR' && empleadoInfo.deposito_id) {
      setForm(prev => ({
        ...prev,
        deposito_origen: empleadoInfo.deposito_id!
      }));
    }
  }, [empleadoInfo]);

  useEffect(() => {
    if (form.deposito_origen && typeof form.deposito_origen === 'number') {
      cargarProductosDisponibles(form.deposito_origen);
    }
  }, [form.deposito_origen, cargarProductosDisponibles]);

  const handleInputChange = (field: keyof TransferenciaForm, value: string | number) => {
    setForm(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Limpiar error del campo cuando el usuario empiece a escribir
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  const agregarProducto = () => {
    const nuevoDetalle: DetalleTransferenciaForm = {
      producto: '',
      cantidad: '',
      producto_nombre: '',
      stock_disponible: 0
    };
    
    setForm(prev => ({
      ...prev,
      detalles: [...prev.detalles, nuevoDetalle]
    }));
  };

  const actualizarDetalle = (index: number, field: keyof DetalleTransferenciaForm, value: string | number) => {
    const nuevosDetalles = [...form.detalles];
    nuevosDetalles[index] = {
      ...nuevosDetalles[index],
      [field]: value
    };
    
    // Si cambió el producto, actualizar la información adicional
    if (field === 'producto' && typeof value === 'number') {
      const producto = productosDisponibles.find(p => p.value === value);
      if (producto) {
        nuevosDetalles[index].producto_nombre = producto.label;
        nuevosDetalles[index].stock_disponible = producto.stock_disponible;
      }
    }
    
    setForm(prev => ({
      ...prev,
      detalles: nuevosDetalles
    }));
    
    // Limpiar errores del detalle
    if (errors.detalles?.[index]) {
      setErrors(prev => ({
        ...prev,
        detalles: {
          ...prev.detalles,
          [index]: {
            ...prev.detalles?.[index],
            [field]: undefined
          }
        }
      }));
    }
  };

  const eliminarDetalle = (index: number) => {
    setForm(prev => ({
      ...prev,
      detalles: prev.detalles.filter((_, i) => i !== index)
    }));
  };

  const validarFormulario = (): boolean => {
    const newErrors: TransferenciaFormErrors = {};
    
    // Validar campos básicos
    if (!form.deposito_origen) {
      newErrors.deposito_origen = ['Debe seleccionar un depósito origen'];
    }
    
    if (!form.deposito_destino) {
      newErrors.deposito_destino = ['Debe seleccionar un depósito destino'];
    }
    
    if (form.deposito_origen === form.deposito_destino) {
      newErrors.deposito_destino = ['El depósito destino debe ser diferente al origen'];
    }
    
    if (!form.fecha_transferencia) {
      newErrors.fecha_transferencia = ['Debe seleccionar una fecha'];
    }
    
    // Validar detalles
    if (form.detalles.length === 0) {
      newErrors.non_field_errors = ['Debe agregar al menos un producto'];
    } else {
      const erroresDetalles: Record<number, Record<string, string[]>> = {};
      
      form.detalles.forEach((detalle, index) => {
        const erroresDetalle: Record<string, string[]> = {};
        
        if (!detalle.producto) {
          erroresDetalle.producto = ['Debe seleccionar un producto'];
        }
        
        if (!detalle.cantidad || detalle.cantidad <= 0) {
          erroresDetalle.cantidad = ['La cantidad debe ser mayor a 0'];
        } else if (detalle.stock_disponible && detalle.cantidad > detalle.stock_disponible) {
          erroresDetalle.cantidad = [`Stock insuficiente. Disponible: ${detalle.stock_disponible}`];
        }
        
        if (Object.keys(erroresDetalle).length > 0) {
          erroresDetalles[index] = erroresDetalle;
        }
      });
      
      if (Object.keys(erroresDetalles).length > 0) {
        newErrors.detalles = erroresDetalles;
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validarFormulario() || !token) return;
    
    try {
      setLoading(true);
      
      // Preparar datos para envío
      const data = {
        ...form,
        detalles: form.detalles.map(detalle => ({
          producto: detalle.producto as number,
          cantidad: detalle.cantidad as number
        }))
      };
      
      await crearTransferencia(data, token);
      
      // Redireccionar a la lista de transferencias
      router.push('/inventario/transferencias');
      
    } catch (error: unknown) {
      console.error('Error creando transferencia:', error);
      
      // Manejar errores de validación del servidor
      if (error && typeof error === 'object' && 'response' in error) {
        const errorResponse = error as { response?: { data?: { errors?: Record<string, string[]> } } };
        if (errorResponse.response?.data?.errors) {
          setErrors(errorResponse.response.data.errors);
        } else {
          setErrors({
            non_field_errors: ['Error al crear la transferencia. Intente nuevamente.']
          });
        }
      } else {
        setErrors({
          non_field_errors: ['Error al crear la transferencia. Intente nuevamente.']
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const puedeAvanzar = () => {
    return form.deposito_origen && 
           form.deposito_destino && 
           form.deposito_origen !== form.deposito_destino &&
           form.fecha_transferencia;
  };

  // Función para manejar el reconocimiento de productos desde la foto
  const handlePhotoUploaded = async (resultadoReconocimiento: ReconocimientoResponse) => {
    if (!token) {
      showToast("No hay sesión activa", "error");
      return;
    }
    
    try {
      setReconociendo(true);
      setIsCameraModalOpen(false);
      showToast("🔍 Procesando productos reconocidos...", "info");
      
      console.log("📸 Resultado del reconocimiento recibido:", resultadoReconocimiento);
      
      if (resultadoReconocimiento.success && resultadoReconocimiento.productos && resultadoReconocimiento.productos.length > 0) {
        // Filtrar solo productos que existen en la BD y están disponibles en el depósito origen
        const productosValidos = resultadoReconocimiento.productos.filter(
          (p: ProductoDetectado) => p.existe_en_bd && p.ingsoft_product_id
        );
        
        if (productosValidos.length === 0) {
          showToast(
            "No se detectaron productos registrados en el sistema",
            "info"
          );
          setReconociendo(false);
          return;
        }
        
        // Inicializar cantidades en 1 para cada producto detectado
        const cantidadesIniciales: { [key: number]: number } = {};
        productosValidos.forEach((producto: ProductoDetectado) => {
          if (producto.ingsoft_product_id) {
            cantidadesIniciales[producto.ingsoft_product_id] = 1;
          }
        });
        
        setProductosDetectados(productosValidos);
        setCantidadesDetectados(cantidadesIniciales);
        setMostrarProductosDetectados(true);
        
        showToast(
          `✅ Se detectaron ${productosValidos.length} producto(s)`,
          "success"
        );
      } else {
        showToast(
          resultadoReconocimiento.error || "No se detectaron productos en la imagen",
          "info"
        );
      }
    } catch (error) {
      console.error('❌ Error en reconocimiento de productos:', error);
      
      let errorMessage = "Error al reconocer productos";
      
      if (error instanceof Error) {
        if (error.message.includes("HTTP 500")) {
          errorMessage = "Error del servidor al procesar la imagen. Verifica los logs del backend.";
        } else if (error.message.includes("HTTP 503") || error.message.includes("HTTP 504")) {
          errorMessage = "El servidor de reconocimiento no está disponible. Verifica que esté corriendo en puerto 8080.";
        } else if (error.message.includes("HTTP 400")) {
          errorMessage = "Error en los datos enviados. Verifica el formato de la imagen.";
        } else {
          errorMessage = error.message;
        }
      }
      
      showToast(errorMessage, "error");
    } finally {
      setReconociendo(false);
    }
  };

  // Confirmar productos detectados y agregarlos a la transferencia
  const confirmarProductosDetectados = async () => {
    try {
      setLoading(true);
      let productosAgregados = 0;
      
      for (const productoDetectado of productosDetectados) {
        if (productoDetectado.ingsoft_product_id) {
          const cantidad = cantidadesDetectados[productoDetectado.ingsoft_product_id] || 1;
          
          // Buscar el producto en la lista de disponibles
          const productoDisponible = productosDisponibles.find(
            p => p.value === productoDetectado.ingsoft_product_id
          );
          
          if (productoDisponible) {
            // Agregar el producto al detalle de la transferencia
            const nuevoDetalle: DetalleTransferenciaForm = {
              producto: productoDetectado.ingsoft_product_id,
              cantidad: cantidad,
              producto_nombre: productoDetectado.nombre_db || '',
              stock_disponible: productoDisponible.stock_disponible
            };
            
            setForm(prev => ({
              ...prev,
              detalles: [...prev.detalles, nuevoDetalle]
            }));
            
            productosAgregados++;
          }
        }
      }
      
      if (productosAgregados > 0) {
        showToast(
          `${productosAgregados} producto(s) agregado(s) a la transferencia`,
          "success"
        );
      }
      
      // Limpiar estado de detección
      setMostrarProductosDetectados(false);
      setProductosDetectados([]);
      setCantidadesDetectados({});
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error al agregar productos";
      showToast(errorMessage, "error");
    } finally {
      setLoading(false);
    }
  };

  // Cancelar detección de productos
  const cancelarProductosDetectados = () => {
    setMostrarProductosDetectados(false);
    setProductosDetectados([]);
    setCantidadesDetectados({});
    showToast("Detección cancelada", "info");
  };

  // Actualizar cantidad de un producto detectado
  const actualizarCantidadDetectado = (productoId: number, nuevaCantidad: number) => {
    if (nuevaCantidad < 1) return;
    setCantidadesDetectados(prev => ({
      ...prev,
      [productoId]: nuevaCantidad
    }));
  };

  if (step === 1) {
    return (
      <Container>
        <Card>
          <h1 className="text-2xl font-bold mb-6 text-center" style={{ color: COLORS.text }}>
            Nueva Transferencia - Configuración
          </h1>
          
          {errors.non_field_errors && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {errors.non_field_errors.join(', ')}
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label className="block mb-2 font-semibold" style={{ color: COLORS.text }}>
                Depósito Origen *
              </label>
              {empleadoInfo?.puesto === 'REPONEDOR' && empleadoInfo.deposito_id ? (
                <div className="w-full px-4 py-3 border border-border rounded-xl bg-gray-100">
                  {empleadoInfo.deposito_nombre}
                  <span className="ml-2 text-sm text-gray-500">(Tu depósito asignado)</span>
                </div>
              ) : (
                <select 
                  className="w-full px-4 py-3 border border-border rounded-xl"
                  value={form.deposito_origen}
                  onChange={(e) => handleInputChange('deposito_origen', Number(e.target.value) || '')}
                >
                  <option value="">Selecciona un depósito</option>
                  {depositos.map(deposito => (
                    <option key={deposito.value} value={deposito.value}>
                      {deposito.label} - {deposito.direccion}
                    </option>
                  ))}
                </select>
              )}
              {errors.deposito_origen && (
                <p className="text-red-500 text-sm mt-1">{errors.deposito_origen[0]}</p>
              )}
            </div>

            <div>
              <label className="block mb-2 font-semibold" style={{ color: COLORS.text }}>
                Depósito Destino *
              </label>
              <select 
                className="w-full px-4 py-3 border border-border rounded-xl"
                value={form.deposito_destino}
                onChange={(e) => handleInputChange('deposito_destino', Number(e.target.value) || '')}
              >
                <option value="">Selecciona un depósito</option>
                {depositos
                  .filter(deposito => deposito.value !== form.deposito_origen)
                  .map(deposito => (
                  <option key={deposito.value} value={deposito.value}>
                    {deposito.label} - {deposito.direccion}
                  </option>
                ))}
              </select>
              {errors.deposito_destino && (
                <p className="text-red-500 text-sm mt-1">{errors.deposito_destino[0]}</p>
              )}
            </div>

            <div>
              <label className="block mb-2 font-semibold" style={{ color: COLORS.text }}>
                Fecha y Hora de Transferencia *
              </label>
              <input 
                type="datetime-local"
                className="w-full px-4 py-3 border border-border rounded-xl"
                value={form.fecha_transferencia}
                onChange={(e) => handleInputChange('fecha_transferencia', e.target.value)}
              />
              {errors.fecha_transferencia && (
                <p className="text-red-500 text-sm mt-1">{errors.fecha_transferencia[0]}</p>
              )}
            </div>

            <div>
              <label className="block mb-2 font-semibold" style={{ color: COLORS.text }}>
                Observaciones
              </label>
              <textarea 
                className="w-full px-4 py-3 border border-border rounded-xl"
                rows={3}
                value={form.observaciones}
                onChange={(e) => handleInputChange('observaciones', e.target.value)}
                placeholder="Observaciones adicionales sobre la transferencia..."
              />
            </div>
          </div>

          <div className="flex justify-between mt-8">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-3 text-lightText hover:text-text transition-colors"
            >
              ← Cancelar
            </button>
            
            <Button
              onClick={() => puedeAvanzar() && setStep(2)}
              disabled={!puedeAvanzar()}
            >
              Siguiente: Seleccionar Productos →
            </Button>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <Container>
      <Card>
        <h1 className="text-2xl font-bold mb-6 text-center" style={{ color: COLORS.text }}>
          Nueva Transferencia - Productos
        </h1>
        
        {/* Resumen de configuración */}
        <div className="bg-gray-50 p-4 rounded-xl mb-6">
          <h3 className="font-semibold mb-2" style={{ color: COLORS.text }}>Resumen:</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <strong>Origen:</strong> {depositos.find(d => d.value === form.deposito_origen)?.label}
            </div>
            <div>
              <strong>Destino:</strong> {depositos.find(d => d.value === form.deposito_destino)?.label}
            </div>
            <div>
              <strong>Fecha:</strong> {new Date(form.fecha_transferencia).toLocaleString('es-AR')}
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {errors.non_field_errors && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {errors.non_field_errors.join(', ')}
            </div>
          )}

          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold" style={{ color: COLORS.text }}>
              Productos a Transferir
            </h3>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setIsCameraModalOpen(true)}
                disabled={!form.deposito_origen || reconociendo}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
                title="Reconocer productos con foto"
              >
                📸 Foto
              </button>
              <button
                type="button"
                onClick={agregarProducto}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                + Agregar Producto
              </button>
            </div>
          </div>

          {form.detalles.length === 0 ? (
            <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-xl">
              <div className="text-4xl mb-2">📦</div>
              <p className="text-gray-500">No hay productos agregados</p>
              <button
                type="button"
                onClick={agregarProducto}
                className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
              >
                Agregar Primer Producto
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {form.detalles.map((detalle, index) => (
                <div key={index} className="border border-border rounded-xl p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-medium" style={{ color: COLORS.text }}>
                      Producto #{index + 1}
                    </h4>
                    <button
                      type="button"
                      onClick={() => eliminarDetalle(index)}
                      className="text-red-500 hover:text-red-700 transition-colors"
                    >
                      ✕ Eliminar
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block mb-2 font-medium" style={{ color: COLORS.text }}>
                        Producto *
                      </label>
                      <select
                        className="w-full px-4 py-3 border border-border rounded-xl"
                        value={detalle.producto}
                        onChange={(e) => actualizarDetalle(index, 'producto', Number(e.target.value) || '')}
                      >
                        <option value="">Selecciona un producto</option>
                        {productosDisponibles.map(producto => (
                          <option key={producto.value} value={producto.value}>
                            {producto.label} - {producto.categoria} (Stock: {producto.stock_disponible})
                          </option>
                        ))}
                      </select>
                      {errors.detalles?.[index]?.producto && (
                        <p className="text-red-500 text-sm mt-1">{errors.detalles[index].producto[0]}</p>
                      )}
                    </div>
                    
                    <div>
                      <label className="block mb-2 font-medium" style={{ color: COLORS.text }}>
                        Cantidad *
                      </label>
                      <input
                        type="number"
                        min="1"
                        max={detalle.stock_disponible || undefined}
                        className="w-full px-4 py-3 border border-border rounded-xl"
                        value={detalle.cantidad}
                        onChange={(e) => actualizarDetalle(index, 'cantidad', Number(e.target.value) || '')}
                        placeholder="Cantidad a transferir"
                      />
                      {detalle.stock_disponible && (
                        <p className="text-sm text-gray-500 mt-1">
                          Stock disponible: {detalle.stock_disponible}
                        </p>
                      )}
                      {errors.detalles?.[index]?.cantidad && (
                        <p className="text-red-500 text-sm mt-1">{errors.detalles[index].cantidad[0]}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-between mt-8">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="px-6 py-3 text-lightText hover:text-text transition-colors"
            >
              ← Volver a Configuración
            </button>
            
            <Button
              type="submit"
              disabled={loading || form.detalles.length === 0}
            >
              {loading ? 'Creando...' : 'Crear Transferencia'}
            </Button>
          </div>
        </form>

        {/* Modal de Cámara */}
        {isCameraModalOpen && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">Capturar Productos</h3>
                <Button 
                  variant="secondary" 
                  onClick={() => setIsCameraModalOpen(false)}
                >
                  ✕
                </Button>
              </div>
              
              <div className="mb-4">
                <p className="text-sm text-gray-600">
                  Usa la cámara para tomar una foto de los productos que deseas transferir. 
                  La imagen será procesada para reconocer los productos.
                </p>
              </div>

              <CameraCapture onUploaded={handlePhotoUploaded} />
              
              <div className="mt-4 flex justify-end">
                <Button 
                  variant="secondary" 
                  onClick={() => setIsCameraModalOpen(false)}
                >
                  Cancelar
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Reconocimiento en Proceso */}
        {reconociendo && (
          <div className="fixed inset-0 bg-black/70 grid place-items-center z-50">
            <div className="bg-white rounded-2xl p-8 w-[360px] max-w-[90%] text-center">
              <div className="mb-4">
                <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
              </div>
              <h3 className="font-bold text-lg mb-2">Analizando imagen...</h3>
              <p className="text-gray-600">
                Detectando productos en la fotografía
              </p>
            </div>
          </div>
        )}

        {/* Modal de Productos Detectados */}
        {mostrarProductosDetectados && (
          <div className="fixed inset-0 bg-black/50 grid place-items-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <h3 className="font-bold text-xl mb-4 text-center">
                🎯 Productos Detectados
              </h3>
              <p className="text-center text-gray-600 mb-4">
                Se detectaron {productosDetectados.length} producto(s). 
                Ajusta las cantidades y confirma para agregarlos a la transferencia.
              </p>

              <div className="space-y-3 mb-6">
                {productosDetectados.map((producto) => {
                  const productoId = producto.ingsoft_product_id!;
                  const cantidad = cantidadesDetectados[productoId] || 1;
                  const productoDisponible = productosDisponibles.find(p => p.value === productoId);
                  
                  return (
                    <div key={productoId} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="font-bold text-lg">{producto.nombre_db}</div>
                          <div className="text-sm text-gray-600">
                            {producto.categoria_db}
                          </div>
                          {productoDisponible && (
                            <div className={`text-xs mt-1 ${
                              (productoDisponible.stock_disponible ?? 0) < 10 ? 'text-orange-600' : 'text-blue-600'
                            }`}>
                              Stock disponible: {productoDisponible.stock_disponible} unidades
                              {(productoDisponible.stock_disponible ?? 0) < 10 && ' (⚠️ Stock bajo)'}
                            </div>
                          )}
                        </div>
                        
                        <div className="ml-4">
                          <div className="text-xs text-gray-500 mb-1">Confianza</div>
                          <div className="text-sm font-medium">
                            {Math.round((producto.classification_confidence || producto.confidence || 0) * 100)}%
                          </div>
                        </div>
                      </div>

                      {/* Control de cantidad */}
                      <div className="flex items-center justify-between bg-white rounded-lg p-2 border border-gray-300">
                        <span className="text-sm font-medium">Cantidad:</span>
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            className="w-8 h-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center font-bold hover:bg-red-200 transition-colors"
                            onClick={() => actualizarCantidadDetectado(productoId, cantidad - 1)}
                          >
                            -
                          </button>
                          <span className="w-12 text-center font-bold text-lg">
                            {cantidad}
                          </span>
                          <button
                            type="button"
                            className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center font-bold hover:bg-green-200 transition-colors"
                            onClick={() => actualizarCantidadDetectado(productoId, cantidad + 1)}
                            disabled={productoDisponible !== undefined && cantidad >= (productoDisponible.stock_disponible ?? 0)}
                          >
                            +
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Total de productos detectados */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-lg">Total de productos:</span>
                  <span className="font-bold text-2xl text-primary">
                    {productosDetectados.reduce((sum, p) => {
                      const cantidad = cantidadesDetectados[p.ingsoft_product_id!] || 1;
                      return sum + cantidad;
                    }, 0)} unidades
                  </span>
                </div>
              </div>

              {/* Botones de acción */}
              <div className="flex gap-3">
                <Button 
                  variant="secondary" 
                  onClick={cancelarProductosDetectados}
                  className="flex-1"
                  disabled={loading}
                >
                  Cancelar
                </Button>
                <Button 
                  onClick={confirmarProductosDetectados}
                  className="flex-1"
                  disabled={loading}
                >
                  {loading ? "Agregando..." : "Confirmar y Agregar"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </Container>
  );
}