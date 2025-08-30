"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { 
  crearProducto, 
  obtenerCategoriasDisponibles,
  obtenerDepositos,
  CategoriaSimple,
  Deposito,
  ProductoCreate
} from "@/lib/api";

export default function NuevoProductoPage() {
  const { token } = useAuth();
  const router = useRouter();
  
  const [categorias, setCategorias] = useState<CategoriaSimple[]>([]);
  const [depositos, setDepositos] = useState<Deposito[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Datos del formulario
  const [formData, setFormData] = useState<ProductoCreate>({
    nombre: "",
    categoria: 0,
    precio: "",
    descripcion: "",
    deposito_id: undefined,
    cantidad_inicial: 0,
    cantidad_minima: 0
  });

  const cargarDatos = useCallback(async () => {
    if (!token) return;
    
    try {
      setLoading(true);
      const [categoriasData, depositosData] = await Promise.all([
        obtenerCategoriasDisponibles(token),
        obtenerDepositos(token)
      ]);
      
      setCategorias(categoriasData);
      setDepositos(depositosData);
    } catch (err: unknown) {
      console.error('Error cargando datos:', err);
      setError('Error cargando datos necesarios');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    cargarDatos();
  }, [token, router, cargarDatos]);

  const handleInputChange = (field: keyof ProductoCreate, value: string | number | undefined) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token) return;
    
    // Validaciones
    if (!formData.nombre.trim()) {
      alert('El nombre del producto es obligatorio');
      return;
    }
    
    if (!formData.categoria) {
      alert('Debes seleccionar una categoría');
      return;
    }
    
    if (!formData.precio || Number(formData.precio) <= 0) {
      alert('El precio debe ser mayor a 0');
      return;
    }

    try {
      setSaving(true);
      await crearProducto(formData, token);
      
      alert('Producto creado exitosamente');
      router.push('/productos');
    } catch (err: unknown) {
      console.error('Error creando producto:', err);
      alert((err as Error).message || 'Error al crear el producto');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    router.push('/productos');
  };

  if (loading) {
    return (
      <Container size="xl">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-lightText">Cargando formulario...</p>
          </div>
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container size="xl">
        <Card className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <div className="flex gap-4 justify-center">
            <Button onClick={cargarDatos}>Reintentar</Button>
            <Button variant="secondary" onClick={handleCancel}>Volver</Button>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <Container size="lg">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={handleCancel}
            className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center hover:bg-gray-200 transition-colors"
          >
          </button>
          <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/80 rounded-2xl flex items-center justify-center text-white text-2xl shadow-xl shadow-primary/30">
            🏷️
          </div>
          <div>
            <h1 className="text-3xl font-bold text-text mb-1">Nuevo Producto</h1>
            <p className="text-lightText">Registra un nuevo producto en tu catálogo</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="space-y-6">
          {/* Información Básica */}
          <Card>
            <h2 className="text-xl font-semibold text-text mb-4">Información Básica</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-text mb-2">
                  Nombre del Producto *
                </label>
                <Input
                  type="text"
                  value={formData.nombre}
                  onChange={(e) => handleInputChange('nombre', e.target.value)}
                  placeholder="Ej: Leche Entera La Serenísima 1L"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text mb-2">
                  Categoría *
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  value={formData.categoria || ""}
                  onChange={(e) => handleInputChange('categoria', Number(e.target.value))}
                  required
                >
                  <option value="">Seleccionar categoría</option>
                  {categorias.map((categoria) => (
                    <option key={categoria.id} value={categoria.id}>
                      {categoria.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text mb-2">
                  Precio *
                </label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.precio}
                  onChange={(e) => handleInputChange('precio', e.target.value)}
                  placeholder="0.00"
                  required
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-text mb-2">
                  Descripción (Opcional)
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  rows={3}
                  value={formData.descripcion || ""}
                  onChange={(e) => handleInputChange('descripcion', e.target.value)}
                  placeholder="Descripción del producto..."
                />
              </div>
            </div>
          </Card>

          {/* Stock Inicial */}
          <Card>
            <h2 className="text-xl font-semibold text-text mb-4">Stock Inicial (Opcional)</h2>
            <p className="text-sm text-lightText mb-4">
              Puedes asignar stock inicial a un depósito específico. También podrás gestionar el stock más tarde.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-text mb-2">
                  Depósito
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  value={formData.deposito_id || ""}
                  onChange={(e) => handleInputChange('deposito_id', e.target.value ? Number(e.target.value) : undefined)}
                >
                  <option value="">Seleccionar depósito</option>
                  {depositos.map((deposito) => (
                    <option key={deposito.id} value={deposito.id}>
                      {deposito.nombre} - {deposito.direccion}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text mb-2">
                  Cantidad Inicial
                </label>
                <Input
                  type="number"
                  min="0"
                  value={formData.cantidad_inicial || 0}
                  onChange={(e) => handleInputChange('cantidad_inicial', Number(e.target.value))}
                  placeholder="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text mb-2">
                  Stock Mínimo
                </label>
                <Input
                  type="number"
                  min="0"
                  value={formData.cantidad_minima || 0}
                  onChange={(e) => handleInputChange('cantidad_minima', Number(e.target.value))}
                  placeholder="0"
                />
              </div>
            </div>

            {formData.deposito_id && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  💡 Se creará stock inicial de <strong>{formData.cantidad_inicial || 0}</strong> unidades 
                  en el depósito seleccionado con un mínimo de <strong>{formData.cantidad_minima || 0}</strong> unidades.
                </p>
              </div>
            )}
          </Card>

          {/* Botones de Acción */}
          <Card>
            <div className="flex justify-end gap-4">
              <Button
                type="button"
                variant="secondary"
                onClick={handleCancel}
                disabled={saving}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={saving}
              >
                {saving ? 'Guardando...' : 'Crear Producto'}
              </Button>
            </div>
          </Card>
        </div>
      </form>
    </Container>
  );
}