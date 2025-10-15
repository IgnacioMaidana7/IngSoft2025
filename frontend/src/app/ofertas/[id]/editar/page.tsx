"use client";
import React, { useState, useEffect } from "react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useRouter, useParams } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import { useToast } from "@/components/feedback/ToastProvider";
import { useAuth } from "@/context/AuthContext";
import { obtenerOferta, actualizarOferta, type OfertaCreate } from "@/lib/api";

export default function EditarOfertaPage() {
  const router = useRouter();
  const params = useParams();
  const { token } = useAuth();
  const { showToast } = useToast();
  
  const ofertaId = parseInt(params.id as string);
  
  // Estado del formulario
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    tipo_descuento: 'porcentaje' as 'porcentaje' | 'monto_fijo',
    valor_descuento: '',
    fecha_inicio: '',
    fecha_fin: ''
  });
  
  const [cargandoOferta, setCargandoOferta] = useState(true);
  const [cargando, setCargando] = useState(false);
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [puedeEditar, setPuedeEditar] = useState(true);

  // Cargar datos de la oferta
  useEffect(() => {
    const cargarOferta = async () => {
      if (!token || !ofertaId) return;
      
      try {
        setCargandoOferta(true);
        const oferta = await obtenerOferta(ofertaId, token);
        
        // Verificar si puede editar
        setPuedeEditar(oferta.puede_editar);
        
        setFormData({
          nombre: oferta.nombre,
          descripcion: oferta.descripcion,
          tipo_descuento: oferta.tipo_descuento,
          valor_descuento: oferta.valor_descuento,
          fecha_inicio: new Date(oferta.fecha_inicio).toISOString().slice(0, 16),
          fecha_fin: new Date(oferta.fecha_fin).toISOString().slice(0, 16)
        });
      } catch (error: any) {
        console.error('Error cargando oferta:', error);
        showToast(error.message || 'Error al cargar la oferta', 'error');
        router.push('/ofertas');
      } finally {
        setCargandoOferta(false);
      }
    };
    
    cargarOferta();
  }, [token, ofertaId, showToast, router]);

  // Validar formulario
  const validarFormulario = (): boolean => {
    const nuevosErrores: Record<string, string> = {};
    
    if (!formData.nombre.trim()) {
      nuevosErrores.nombre = 'El nombre es obligatorio';
    }
    
    // Descripción es opcional - no validar
    
    if (!formData.valor_descuento || parseFloat(formData.valor_descuento) <= 0) {
      nuevosErrores.valor_descuento = 'El valor del descuento debe ser mayor a 0';
    }
    
    if (formData.tipo_descuento === 'porcentaje' && parseFloat(formData.valor_descuento) > 100) {
      nuevosErrores.valor_descuento = 'El descuento porcentual no puede ser mayor a 100%';
    }
    
    if (!formData.fecha_inicio) {
      nuevosErrores.fecha_inicio = 'La fecha de inicio es obligatoria';
    }
    
    if (!formData.fecha_fin) {
      nuevosErrores.fecha_fin = 'La fecha de fin es obligatoria';
    }
    
    if (formData.fecha_inicio && formData.fecha_fin) {
      const inicio = new Date(formData.fecha_inicio);
      const fin = new Date(formData.fecha_fin);
      
      if (fin <= inicio) {
        nuevosErrores.fecha_fin = 'La fecha de fin debe ser posterior a la fecha de inicio';
      }
    }
    
    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  // Handler para cambios en el formulario
  const handleChange = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Limpiar error del campo cuando el usuario empiece a escribir
    if (errores[field]) {
      setErrores(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Submitir formulario
  const handleSubmit = async () => {
    if (!validarFormulario() || !token || !puedeEditar) return;
    
    setCargando(true);
    
    try {
      const ofertaData: Partial<OfertaCreate> = {
        ...formData,
        valor_descuento: parseFloat(formData.valor_descuento),
        fecha_inicio: new Date(formData.fecha_inicio).toISOString(),
        fecha_fin: new Date(formData.fecha_fin).toISOString()
      };
      
      const response = await actualizarOferta(ofertaId, ofertaData, token);
      showToast(response.message || 'Oferta actualizada correctamente', 'success');
      router.push('/ofertas');
    } catch (error: any) {
      console.error('Error actualizando oferta:', error);
      
      if (error.message.includes(':')) {
        // Es un error de validación del backend
        const errorLines = error.message.split('\n');
        const nuevosErrores: Record<string, string> = {};
        
        errorLines.forEach((line: string) => {
          const [field, message] = line.split(': ');
          if (field && message) {
            nuevosErrores[field] = message;
          }
        });
        
        setErrores(nuevosErrores);
        showToast('Por favor corrige los errores en el formulario', 'error');
      } else {
        showToast(error.message || 'Error al actualizar la oferta', 'error');
      }
    } finally {
      setCargando(false);
    }
  };

  if (cargandoOferta) {
    return (
      <Container>
        <Card>
          <div className="text-center p-8">
            <p className="text-lightText">Cargando oferta...</p>
          </div>
        </Card>
      </Container>
    );
  }

  if (!puedeEditar) {
    return (
      <Container>
        <Card>
          <div className="text-center p-8">
            <h2 className="text-xl font-semibold text-text mb-2">Oferta No Editable</h2>
            <p className="text-lightText">Esta oferta no puede ser editada porque ya ha expirado.</p>
            <Button onClick={() => router.push('/ofertas')} className="mt-4">
              Volver a Ofertas
            </Button>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <ProtectedRoute>
      <Container>
        <Card className="bg-background text-text p-5">
          <div className="mb-6">
            <h1 className="text-2xl font-bold mb-2">Editar Oferta</h1>
            <p className="text-lightText">Modifica los datos de la oferta promocional</p>
          </div>

          <div className="space-y-4">
            {/* Información básica */}
            <div>
              <Input 
                label="Nombre de la Oferta *" 
                value={formData.nombre} 
                onChange={(e) => handleChange('nombre', e.target.value)}
                placeholder="ej: 15% OFF en Lácteos"
              />
              {errores.nombre && <p className="text-red-500 text-sm mt-1">{errores.nombre}</p>}
            </div>

            <div>
              <label className="block mb-2 font-medium text-text">Descripción</label>
              <textarea
                className="w-full px-3 py-3 border border-border rounded-xl resize-none"
                rows={3}
                value={formData.descripcion}
                onChange={(e) => handleChange('descripcion', e.target.value)}
                placeholder="Describe los detalles de la oferta (opcional)..."
              />
              {errores.descripcion && <p className="text-red-500 text-sm mt-1">{errores.descripcion}</p>}
            </div>

            {/* Tipo de descuento */}
            <div>
              <label className="block mb-3 font-medium text-text">Tipo de Descuento *</label>
              <div className="flex border border-border rounded-xl overflow-hidden">
                <button
                  type="button"
                  className={`flex-1 py-3 font-medium transition-colors ${
                    formData.tipo_descuento === 'porcentaje'
                      ? 'bg-primary text-white'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                  }`}
                  onClick={() => handleChange('tipo_descuento', 'porcentaje')}
                >
                  Descuento Porcentual
                </button>
                <button
                  type="button"
                  className={`flex-1 py-3 font-medium transition-colors ${
                    formData.tipo_descuento === 'monto_fijo'
                      ? 'bg-primary text-white'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                  }`}
                  onClick={() => handleChange('tipo_descuento', 'monto_fijo')}
                >
                  Monto Fijo
                </button>
              </div>
            </div>

            {/* Valor del descuento */}
            <div>
              <Input
                label={`Valor del Descuento * ${formData.tipo_descuento === 'porcentaje' ? '(%)' : '($)'}`}
                type="number"
                step="0.01"
                min="0"
                max={formData.tipo_descuento === 'porcentaje' ? '100' : undefined}
                value={formData.valor_descuento}
                onChange={(e) => handleChange('valor_descuento', e.target.value)}
                placeholder={formData.tipo_descuento === 'porcentaje' ? '15' : '50.00'}
              />
              {errores.valor_descuento && <p className="text-red-500 text-sm mt-1">{errores.valor_descuento}</p>}
            </div>

            {/* Fechas de vigencia */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block mb-2 font-medium text-text">Fecha de Inicio *</label>
                <input
                  type="datetime-local"
                  className="w-full px-3 py-3 border border-border rounded-xl"
                  value={formData.fecha_inicio}
                  onChange={(e) => handleChange('fecha_inicio', e.target.value)}
                />
                {errores.fecha_inicio && <p className="text-red-500 text-sm mt-1">{errores.fecha_inicio}</p>}
              </div>

              <div>
                <label className="block mb-2 font-medium text-text">Fecha de Fin *</label>
                <input
                  type="datetime-local"
                  className="w-full px-3 py-3 border border-border rounded-xl"
                  value={formData.fecha_fin}
                  onChange={(e) => handleChange('fecha_fin', e.target.value)}
                  min={formData.fecha_inicio}
                />
                {errores.fecha_fin && <p className="text-red-500 text-sm mt-1">{errores.fecha_fin}</p>}
              </div>
            </div>
          </div>

          {/* Botones de acción */}
          <div className="flex gap-3 mt-6 pt-6 border-t border-border">
            <Button 
              onClick={handleSubmit} 
              disabled={cargando}
              className="flex-1"
            >
              {cargando ? 'Actualizando...' : 'Actualizar Oferta'}
            </Button>
            <Button 
              variant="secondary" 
              onClick={() => router.push('/ofertas')}
              disabled={cargando}
            >
              Cancelar
            </Button>
          </div>
        </Card>
      </Container>
    </ProtectedRoute>
  );
}