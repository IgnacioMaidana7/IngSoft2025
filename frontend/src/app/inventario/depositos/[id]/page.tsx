"use client";
import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { useToast } from "@/components/feedback/ToastProvider";
import { useAuth } from "@/context/AuthContext";
import { 
  obtenerDeposito, 
  actualizarDeposito, 
  eliminarDeposito,
  Deposito, 
  DepositoCreate 
} from "@/lib/api";

export default function EditarDepositoPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const { token } = useAuth();
  
  const [deposito, setDeposito] = useState<Deposito | null>(null);
  const [nombre, setNombre] = useState("");
  const [direccion, setDireccion] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const depositoId = parseInt(params.id as string);

  // Cargar datos del depósito
  useEffect(() => {
    if (!token || !depositoId) return;

    const cargarDeposito = async () => {
      try {
        setLoading(true);
        const depositoEncontrado = await obtenerDeposito(depositoId, token);
        
        setDeposito(depositoEncontrado);
        setNombre(depositoEncontrado.nombre);
        setDireccion(depositoEncontrado.direccion);
        setDescripcion(depositoEncontrado.descripcion || "");
      } catch (error) {
        console.error('Error al cargar depósito:', error);
        showToast(`Error al cargar depósito: ${error}`, 'error');
        router.push('/inventario/depositos');
      } finally {
        setLoading(false);
      }
    };

    cargarDeposito();
  }, [token, depositoId, router, showToast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token || !deposito) {
      showToast('No estás autenticado', 'error');
      return;
    }

    // Validaciones
    if (!nombre.trim()) {
      showToast('El nombre del depósito es obligatorio', 'error');
      return;
    }
    if (!direccion.trim()) {
      showToast('La dirección es obligatoria', 'error');
      return;
    }

    try {
      setUpdating(true);
      
      const datosActualizados: DepositoCreate = {
        nombre: nombre.trim(),
        direccion: direccion.trim(),
        descripcion: descripcion.trim() || undefined
      };

      await actualizarDeposito(depositoId, datosActualizados, token);
      showToast('Depósito actualizado exitosamente', 'success');
      router.push('/inventario/depositos');
    } catch (error) {
      showToast(`Error al actualizar depósito: ${error}`, 'error');
    } finally {
      setUpdating(false);
    }
  };

  const handleEliminar = async () => {
    if (!token || !deposito) return;

    const confirmacion = window.confirm(
      `¿Estás seguro de que deseas eliminar el depósito "${deposito.nombre}"?\n\n` +
      "Esta acción es irreversible y no se puede realizar si el depósito tiene stock o empleados asociados."
    );

    if (!confirmacion) return;

    try {
      setUpdating(true);
      await eliminarDeposito(depositoId, token);
      showToast('Depósito eliminado exitosamente', 'success');
      router.push('/inventario/depositos');
    } catch (error) {
      showToast(`Error al eliminar depósito: ${error}`, 'error');
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="text-lg">Cargando depósito...</div>
          </div>
        </Card>
      </Container>
    );
  }

  if (!deposito) {
    return (
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="text-lg text-red-600">Depósito no encontrado</div>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <Container>
      <Card>
        {/* Header */}
        <div className="mb-6 pb-4 border-b border-border">
          <h1 className="text-3xl font-bold text-text mb-1">Editar Depósito</h1>
          <p className="text-lightText">Modifica la información del depósito</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Campos del formulario */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input 
              label="Nombre del Depósito *" 
              value={nombre} 
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej: Depósito Central, Sucursal Norte"
              disabled={updating}
            />
            
            <Input 
              label="Dirección *" 
              value={direccion} 
              onChange={(e) => setDireccion(e.target.value)}
              placeholder="Dirección completa del depósito"
              disabled={updating}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción
            </label>
            <textarea
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              placeholder="Descripción opcional del depósito..."
              disabled={updating}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>

          {/* Información del depósito */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-800 mb-2">Información del Depósito</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <div><strong>Creado:</strong> {new Date(deposito.fecha_creacion).toLocaleDateString()}</div>
              <div><strong>Última modificación:</strong> {new Date(deposito.fecha_modificacion).toLocaleDateString()}</div>
              <div><strong>Estado:</strong> {deposito.activo ? 'Activo' : 'Inactivo'}</div>
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-6">
            <Button 
              type="submit" 
              disabled={updating}
              className={updating ? 'opacity-50 cursor-not-allowed' : ''}
            >
              {updating ? 'Actualizando...' : 'Actualizar Depósito'}
            </Button>
            <Button 
              type="button"
              variant="secondary" 
              onClick={() => router.back()}
              disabled={updating}
            >
              Cancelar
            </Button>
            <Button 
              type="button"
              onClick={handleEliminar}
              disabled={updating}
              className="bg-red-600 hover:bg-red-700 text-white ml-auto"
            >
              {updating ? 'Eliminando...' : 'Eliminar Depósito'}
            </Button>
          </div>
        </form>
      </Card>
    </Container>
  );
}
