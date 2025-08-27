"use client";
import React, { useState } from "react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { useToast } from "@/components/feedback/ToastProvider";
import { useAuth } from "@/context/AuthContext";
import { crearDeposito, DepositoCreate } from "@/lib/api";

export default function NuevoDepositoPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const { token } = useAuth();
  
  const [nombre, setNombre] = useState("");
  const [direccion, setDireccion] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token) {
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
      setLoading(true);
      
      const nuevoDeposito: DepositoCreate = {
        nombre: nombre.trim(),
        direccion: direccion.trim(),
        descripcion: descripcion.trim() || undefined
      };

      await crearDeposito(nuevoDeposito, token);
      showToast('Depósito creado exitosamente', 'success');
      router.push('/inventario/depositos?created=true');
    } catch (error) {
      showToast(`Error al crear depósito: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <Card>
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-text mb-1">Crear Nuevo Depósito</h1>
          <p className="text-lightText">Complete la información del nuevo depósito</p>
        </div>
        
        <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
          <div className="space-y-4">
            <Input 
              label="Nombre del Depósito *" 
              value={nombre} 
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej: Depósito Central, Sucursal Norte"
              disabled={loading}
            />
            
            <Input 
              label="Dirección *" 
              value={direccion} 
              onChange={(e) => setDireccion(e.target.value)}
              placeholder="Dirección completa del depósito"
              disabled={loading}
            />
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Descripción
              </label>
              <textarea
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                placeholder="Descripción opcional del depósito..."
                disabled={loading}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              />
            </div>
          </div>

          {/* Información adicional */}
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700">
              <strong>Información:</strong> Una vez creado el depósito, podrás asignar empleados 
              y gestionar el inventario desde la sección correspondiente.
            </p>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-6">
            <Button 
              type="submit" 
              disabled={loading}
              className={loading ? 'opacity-50 cursor-not-allowed' : ''}
            >
              {loading ? 'Creando...' : 'Crear Depósito'}
            </Button>
            <Button 
              type="button"
              variant="secondary" 
              onClick={() => router.back()}
              disabled={loading}
            >
              Cancelar
            </Button>
          </div>
        </form>
      </Card>
    </Container>
  );
}


