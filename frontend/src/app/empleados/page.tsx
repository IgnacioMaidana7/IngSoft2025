"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/feedback/ToastProvider";
import { 
  obtenerEmpleados, 
  obtenerDepositosDisponibles, 
  obtenerRolesDisponibles, 
  eliminarEmpleado,
  Empleado,
  Deposito,
  Role 
} from "@/lib/api";

export default function EmpleadosPage() {
  const { token } = useAuth();
  const { showToast } = useToast();
  
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [depositos, setDepositos] = useState<Deposito[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroRol, setFiltroRol] = useState<string>('');
  const [filtroDeposito, setFiltroDeposito] = useState<string>('');
  const [busqueda, setBusqueda] = useState<string>('');

  // Cargar datos iniciales
  useEffect(() => {
    if (!token) return;
    
    const cargarDatos = async () => {
      try {
        setLoading(true);
        const [empleadosData, depositosData, rolesData] = await Promise.all([
          obtenerEmpleados(token),
          obtenerDepositosDisponibles(token),
          obtenerRolesDisponibles(token)
        ]);
        
        console.log('Empleados recibidos:', empleadosData);
        console.log('Depósitos recibidos:', depositosData);
        console.log('Roles recibidos:', rolesData);
        
        setEmpleados(empleadosData);
        setDepositos(depositosData?.data || []);
        setRoles(rolesData?.roles || []);
      } catch (error) {
        console.error('Error al cargar datos:', error);
        showToast(`Error al cargar datos: ${error}`, 'error');
        // En caso de error, establecer valores por defecto
        setEmpleados([]);
        setDepositos([]);
        setRoles([]);
      } finally {
        setLoading(false);
      }
    };

    cargarDatos();
  }, [token, showToast]);

  // Cargar empleados con filtros
  useEffect(() => {
    if (!token) return;
    
    const cargarEmpleadosFiltrados = async () => {
      try {
        const filtros: {
          puesto?: string;
          deposito?: number;
          search?: string;
        } = {};
        if (filtroRol) filtros.puesto = filtroRol;
        if (filtroDeposito) filtros.deposito = parseInt(filtroDeposito);
        if (busqueda) filtros.search = busqueda;
        
        const empleadosData = await obtenerEmpleados(token, filtros);
        // Asegurar que empleadosData es un array
        setEmpleados(Array.isArray(empleadosData) ? empleadosData : []);
      } catch (error) {
        console.error('Error al filtrar empleados:', error);
        showToast(`Error al filtrar empleados: ${error}`, 'error');
        // En caso de error, establecer array vacío
        setEmpleados([]);
      }
    };

    // Debounce para la búsqueda
    const timeoutId = setTimeout(() => {
      if (token) {
        cargarEmpleadosFiltrados();
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [filtroRol, filtroDeposito, busqueda, token, showToast]);

  const handleEliminarEmpleado = async (id: number, nombre: string) => {
    if (!token) return;
    
    if (window.confirm(`¿Estás seguro de que deseas eliminar al empleado ${nombre}?`)) {
      try {
        await eliminarEmpleado(id, token);
        setEmpleados(empleados.filter(e => e.id !== id));
        showToast('Empleado eliminado correctamente', 'success');
      } catch (error) {
        showToast(`Error al eliminar empleado: ${error}`, 'error');
      }
    }
  };

  const limpiarFiltros = () => {
    setFiltroRol('');
    setFiltroDeposito('');
    setBusqueda('');
  };

  if (loading) {
    return (
      <Container>
        <Card>
          <div className="text-center py-8">
            <div className="text-lg">Cargando empleados...</div>
          </div>
        </Card>
      </Container>
    );
  }

  return (
    <Container>
      <Card>
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-border">
          <div>
            <h1 className="text-3xl font-bold text-text mb-1">Gestión de Empleados</h1>
            <p className="text-lightText">Administra tu equipo de trabajo</p>
          </div>
          <Link href="/empleados/nuevo" className="bg-primary text-white px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors">
            + Añadir Empleado
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{empleados?.length || 0}</div>
            <div className="text-sm text-blue-700">Total Empleados</div>
          </div>
          <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {empleados?.filter(e => e.puesto === 'CAJERO').length || 0}
            </div>
            <div className="text-sm text-green-700">Cajeros</div>
          </div>
          <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {empleados?.filter(e => e.puesto === 'REPONEDOR').length || 0}
            </div>
            <div className="text-sm text-purple-700">Reponedores</div>
          </div>
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <Input
            label="Buscar empleado"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Nombre, apellido o email"
          />
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
            <select
              value={filtroRol}
              onChange={(e) => setFiltroRol(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Todos los roles</option>
              {roles.map((role) => (
                <option key={role.value} value={role.value}>{role.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Depósito</label>
            <select
              value={filtroDeposito}
              onChange={(e) => setFiltroDeposito(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Todos los depósitos</option>
              {depositos.map((deposito) => (
                <option key={deposito.id} value={deposito.id}>{deposito.nombre}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <Button variant="secondary" onClick={limpiarFiltros} className="w-full">
              Limpiar Filtros
            </Button>
          </div>
        </div>

        {/* Lista de empleados */}
        {!empleados || empleados.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-500 mb-4">No se encontraron empleados</div>
            <Link href="/empleados/nuevo" className="text-primary hover:underline">
              Añadir el primer empleado
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {empleados.map((empleado) => (
              <div key={empleado.id} className="border border-border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg text-text">{empleado.nombre_completo}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        empleado.puesto === 'CAJERO' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {empleado.puesto === 'CAJERO' ? 'Cajero' : 'Reponedor'}
                      </span>
                    </div>
                    <div className="text-sm text-lightText space-y-1">
                      <div><strong>Email:</strong> {empleado.email}</div>
                      <div><strong>DNI:</strong> {empleado.dni}</div>
                      <div><strong>Depósito:</strong> {empleado.deposito_nombre}</div>
                      <div><strong>Fecha ingreso:</strong> {new Date(empleado.fecha_ingreso).toLocaleDateString()}</div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Link 
                      href={`/empleados/${empleado.id}`}
                      className="text-primary hover:text-primary/80 px-3 py-1 border border-primary rounded hover:bg-primary/10 transition-colors"
                    >
                      Editar
                    </Link>
                    <button 
                      onClick={() => handleEliminarEmpleado(empleado.id, empleado.nombre_completo)}
                      className="text-red-600 hover:text-red-700 px-3 py-1 border border-red-600 rounded hover:bg-red-50 transition-colors"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </Container>
  );
}


