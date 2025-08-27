"use client";
import React, { useState, useEffect } from "react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { useToast } from "@/components/feedback/ToastProvider";
import { useAuth } from "@/context/AuthContext";
import { 
  crearEmpleado, 
  obtenerDepositosDisponibles, 
  obtenerRolesDisponibles,
  Deposito,
  Role,
  EmpleadoCreate 
} from "@/lib/api";

export default function NuevoEmpleadoPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const { token } = useAuth();
  
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [email, setEmail] = useState("");
  const [dni, setDni] = useState("");
  const [puesto, setPuesto] = useState<'CAJERO' | 'REPONEDOR' | ''>('');
  const [deposito, setDeposito] = useState<number | ''>('');
  
  const [depositos, setDepositos] = useState<Deposito[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  // Cargar datos iniciales
  useEffect(() => {
    if (!token) return;
    
    const cargarDatos = async () => {
      try {
        const [depositosData, rolesData] = await Promise.all([
          obtenerDepositosDisponibles(token),
          obtenerRolesDisponibles(token)
        ]);
        
        setDepositos(depositosData.data);
        setRoles(rolesData.roles);
      } catch (error) {
        showToast(`Error al cargar datos: ${error}`, 'error');
      } finally {
        setLoadingData(false);
      }
    };

    cargarDatos();
  }, [token, showToast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token) {
      showToast('No estás autenticado', 'error');
      return;
    }

    // Validaciones
    if (!nombre.trim()) {
      showToast('El nombre es obligatorio', 'error');
      return;
    }
    if (!apellido.trim()) {
      showToast('El apellido es obligatorio', 'error');
      return;
    }
    if (!email.trim()) {
      showToast('El email es obligatorio', 'error');
      return;
    }
    if (!dni.trim()) {
      showToast('El DNI es obligatorio', 'error');
      return;
    }
    if (!puesto) {
      showToast('El puesto es obligatorio', 'error');
      return;
    }
    if (!deposito) {
      showToast('El depósito es obligatorio', 'error');
      return;
    }

    // Validar formato de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      showToast('El email no tiene un formato válido', 'error');
      return;
    }

    // Validar DNI (7-8 dígitos)
    const dniRegex = /^\d{7,8}$/;
    if (!dniRegex.test(dni)) {
      showToast('El DNI debe tener entre 7 y 8 dígitos', 'error');
      return;
    }

    try {
      setLoading(true);
      
      const nuevoEmpleado: EmpleadoCreate = {
        nombre: nombre.trim(),
        apellido: apellido.trim(),
        email: email.trim().toLowerCase(),
        dni: dni.trim(),
        puesto,
        deposito: deposito as number,
        password: dni.trim() // La contraseña será el DNI
      };

      await crearEmpleado(nuevoEmpleado, token);
      showToast('Empleado registrado exitosamente', 'success');
      router.push('/empleados');
    } catch (error) {
      showToast(`Error al registrar empleado: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="text-lg">Cargando formulario...</div>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <Container>
      <Card>
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-text mb-1">Registrar Empleado</h1>
          <p className="text-lightText">Complete la información del nuevo empleado</p>
        </div>
        
        <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
          {/* Información Personal */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-text border-b border-border pb-2">
              Información Personal
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input 
                label="Nombre *" 
                value={nombre} 
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Ingrese el nombre"
                disabled={loading}
              />
              <Input 
                label="Apellido *" 
                value={apellido} 
                onChange={(e) => setApellido(e.target.value)}
                placeholder="Ingrese el apellido"
                disabled={loading}
              />
            </div>
            
            <Input 
              label="Email *" 
              type="email"
              value={email} 
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ejemplo@email.com"
              disabled={loading}
            />
            
            <Input 
              label="DNI *" 
              value={dni} 
              onChange={(e) => setDni(e.target.value.replace(/\D/g, ''))}
              placeholder="12345678"
              maxLength={8}
              disabled={loading}
            />
          </div>

          {/* Información Laboral */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-text border-b border-border pb-2">
              Información Laboral
            </h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Puesto *</label>
              <select 
                value={puesto} 
                onChange={(e) => setPuesto(e.target.value as 'CAJERO' | 'REPONEDOR' | '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={loading}
              >
                <option value="">Selecciona un puesto</option>
                {roles.map((role) => (
                  <option key={role.value} value={role.value}>{role.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Depósito *</label>
              <select 
                value={deposito} 
                onChange={(e) => setDeposito(e.target.value ? parseInt(e.target.value) : '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={loading}
              >
                <option value="">Selecciona un depósito</option>
                {depositos.map((dep) => (
                  <option key={dep.id} value={dep.id}>{dep.nombre}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Información de Acceso */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-text border-b border-border pb-2">
              Información de Acceso
            </h2>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-700">
                <strong>Importante:</strong> La contraseña del empleado será su DNI por defecto. 
                El empleado podrá cambiarla una vez que acceda al sistema.
              </p>
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-6">
            <Button 
              type="submit" 
              disabled={loading}
              className={loading ? 'opacity-50 cursor-not-allowed' : ''}
            >
              {loading ? 'Guardando...' : 'Guardar Empleado'}
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


